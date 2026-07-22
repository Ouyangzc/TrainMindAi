package com.hezal.system.service.impl;

import java.util.List;
import java.util.Objects;
import org.apache.commons.lang3.StringUtils;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import com.hezal.common.exception.ServiceException;
import com.hezal.system.ai.AiQaClient;
import com.hezal.system.domain.StudentQaCitation;
import com.hezal.system.domain.StudentQaMessage;
import com.hezal.system.domain.StudentQaSession;
import com.hezal.system.domain.dto.AiQaAnswer;
import com.hezal.system.domain.dto.AiQaRequest;
import com.hezal.system.domain.dto.AiQaSource;
import com.hezal.system.domain.vo.student.StudentCourseContext;
import com.hezal.system.domain.vo.student.StudentPublishedDocumentVO;
import com.hezal.system.mapper.StudentPublishedContentMapper;
import com.hezal.system.mapper.StudentQaMapper;
import com.hezal.system.service.CourseAccessService;
import com.hezal.system.service.IStudentQaService;
import com.hezal.system.service.IStudentLearningActivityService;

/** 学员课程问答服务实现。 */
@Service
public class StudentQaServiceImpl implements IStudentQaService
{
    private static final Logger log = LoggerFactory.getLogger(StudentQaServiceImpl.class);
    private static final String NEW_SESSION_TITLE = "新对话";
    private static final String INSUFFICIENT_ANSWER =
            "未在当前课程资料中找到足够依据，建议换一种问法或查阅课程资料库。";
    private static final String UNAVAILABLE_ANSWER =
            "问答服务暂时不可用，请稍后重试。你仍可继续查阅当前课程资料。";

    private final CourseAccessService courseAccessService;
    private final StudentQaMapper qaMapper;
    private final StudentPublishedContentMapper contentMapper;
    private final AiQaClient aiQaClient;
    private final IStudentLearningActivityService activityService;

    public StudentQaServiceImpl(CourseAccessService courseAccessService, StudentQaMapper qaMapper,
            StudentPublishedContentMapper contentMapper, AiQaClient aiQaClient,
            IStudentLearningActivityService activityService)
    {
        this.courseAccessService = courseAccessService;
        this.qaMapper = qaMapper;
        this.contentMapper = contentMapper;
        this.aiQaClient = aiQaClient;
        this.activityService = activityService;
    }

    @Override
    public List<StudentQaSession> selectSessions(Long courseId, Long userId)
    {
        StudentCourseContext context = requirePublishedContext(courseId, userId);
        return qaMapper.selectSessions(context.getTenantId(), courseId, userId);
    }

    @Override
    public StudentQaSession createSession(Long courseId, Long userId)
    {
        StudentCourseContext context = requirePublishedContext(courseId, userId);
        StudentQaSession session = new StudentQaSession();
        session.setTenantId(context.getTenantId());
        session.setUserId(userId);
        session.setCourseId(courseId);
        session.setTitle(NEW_SESSION_TITLE);
        session.setStatus("active");
        session.setCreateBy(userId.toString());
        qaMapper.insertSession(session);
        return session;
    }

    @Override
    public List<StudentQaMessage> selectMessages(Long courseId, Long sessionId, Long userId)
    {
        StudentCourseContext context = requirePublishedContext(courseId, userId);
        requireSession(context, courseId, sessionId, userId);
        List<StudentQaMessage> messages = qaMapper.selectMessages(context.getTenantId(), sessionId);
        for (StudentQaMessage message : messages)
        {
            if ("assistant".equals(message.getRole()))
            {
                message.setCitations(qaMapper.selectCitations(context.getTenantId(), message.getId()));
            }
        }
        return messages;
    }

    @Override
    public StudentQaMessage ask(Long courseId, Long sessionId, Long userId, String rawQuestion)
    {
        StudentCourseContext context = requirePublishedContext(courseId, userId);
        StudentQaSession session = requireSession(context, courseId, sessionId, userId);
        String question = StringUtils.trimToNull(rawQuestion);
        if (question == null)
        {
            throw new ServiceException("问题不能为空");
        }

        StudentQaMessage userMessage = newMessage(context, sessionId, userId, courseId,
                "user", question, "completed");
        qaMapper.insertMessage(userMessage);
        StudentQaMessage assistant = newMessage(context, sessionId, userId, courseId,
                "assistant", "", "pending");
        qaMapper.insertMessage(assistant);

        if (NEW_SESSION_TITLE.equals(session.getTitle()))
        {
            qaMapper.updateSessionTitle(sessionId, question.length() <= 30
                    ? question : question.substring(0, 30));
        }

        try
        {
            AiQaAnswer answer = aiQaClient.answer(createAiRequest(
                    context, courseId, sessionId, assistant.getId(), userId, question));
            if (!Objects.equals(context.getPublishedVersionId(), answer.getKnowledgeBaseVersionId()))
            {
                throw new ServiceException("AI回答所用知识库版本与当前课程发布版本不一致");
            }
            completeAssistant(context, courseId, assistant, answer);
        }
        catch (ServiceException ex)
        {
            assistant.setContent(UNAVAILABLE_ANSWER);
            assistant.setStatus("service_unavailable");
            assistant.setRejectReason(ex.getMessage());
            qaMapper.completeAssistantMessage(assistant);
        }
        qaMapper.touchSession(sessionId);
        try
        {
            activityService.recordChat(courseId, userId, sessionId, question);
        }
        catch (RuntimeException ex)
        {
            log.warn("记录学员问答活动失败，courseId={}, sessionId={}", courseId, sessionId, ex);
        }
        assistant.setCitations(qaMapper.selectCitations(context.getTenantId(), assistant.getId()));
        return assistant;
    }

    @Override
    public StudentQaCitation selectCitation(Long courseId, Long sessionId, Long messageId,
            Long citationId, Long userId)
    {
        StudentCourseContext context = requirePublishedContext(courseId, userId);
        requireSession(context, courseId, sessionId, userId);
        boolean ownedMessage = qaMapper.selectMessages(context.getTenantId(), sessionId).stream()
                .anyMatch(message -> Objects.equals(message.getId(), messageId));
        if (!ownedMessage)
        {
            throw new ServiceException("消息不存在或不属于当前会话");
        }
        StudentQaCitation citation = qaMapper.selectCitation(
                context.getTenantId(), messageId, citationId);
        if (citation == null)
        {
            throw new ServiceException("引用不存在");
        }
        return citation;
    }

    private StudentCourseContext requirePublishedContext(Long courseId, Long userId)
    {
        StudentCourseContext context = courseAccessService.requireStudentAccess(courseId, userId);
        if (context.getPublishedVersionId() == null)
        {
            throw new ServiceException("当前课程内容尚未发布");
        }
        return context;
    }

    private StudentQaSession requireSession(StudentCourseContext context, Long courseId,
            Long sessionId, Long userId)
    {
        StudentQaSession session = qaMapper.selectSession(
                context.getTenantId(), courseId, userId, sessionId);
        if (session == null)
        {
            throw new ServiceException("问答会话不存在或不属于当前学员");
        }
        return session;
    }

    private StudentQaMessage newMessage(StudentCourseContext context, Long sessionId,
            Long userId, Long courseId, String role, String content, String status)
    {
        StudentQaMessage message = new StudentQaMessage();
        message.setTenantId(context.getTenantId());
        message.setSessionId(sessionId);
        message.setUserId(userId);
        message.setCourseId(courseId);
        message.setKnowledgeBaseVersionId(context.getPublishedVersionId());
        message.setRole(role);
        message.setContent(content);
        message.setStatus(status);
        message.setCreateBy(userId.toString());
        return message;
    }

    private AiQaRequest createAiRequest(StudentCourseContext context, Long courseId,
            Long sessionId, Long messageId, Long userId, String question)
    {
        AiQaRequest request = new AiQaRequest();
        request.setUserId(userId);
        request.setCourseId(courseId);
        request.setKnowledgeBaseVersionId(context.getPublishedVersionId());
        request.setSessionId(sessionId);
        request.setMessageId(messageId);
        request.setQuestion(question);
        return request;
    }

    private void completeAssistant(StudentCourseContext context, Long courseId,
            StudentQaMessage assistant, AiQaAnswer answer)
    {
        boolean grounded = "grounded".equals(answer.getAnswerStatus());
        assistant.setContent(grounded ? answer.getAnswer() : INSUFFICIENT_ANSWER);
        assistant.setStatus(grounded ? "grounded" : "insufficient_evidence");
        assistant.setRejectReason(answer.getRejectReason());
        assistant.setRetrievalLogRef(answer.getRetrievalLogRef());
        qaMapper.completeAssistantMessage(assistant);
        if (!grounded || answer.getSources() == null)
        {
            return;
        }
        int rank = 1;
        for (AiQaSource source : answer.getSources())
        {
            StudentPublishedDocumentVO document = contentMapper.selectPublishedDocument(
                    context.getTenantId(), courseId, context.getPublishedVersionId(),
                    source.getDocumentId());
            if (document == null
                    || !Objects.equals(document.getDocumentVersionId(), source.getDocumentVersionId()))
            {
                continue;
            }
            qaMapper.insertCitation(toCitation(context.getTenantId(), assistant.getId(),
                    source, document, rank++));
        }
    }

    private StudentQaCitation toCitation(Long tenantId, Long messageId, AiQaSource source,
            StudentPublishedDocumentVO document, int rank)
    {
        StudentQaCitation citation = new StudentQaCitation();
        citation.setTenantId(tenantId);
        citation.setMessageId(messageId);
        citation.setChunkId(source.getChunkId());
        citation.setDocumentId(source.getDocumentId());
        citation.setDocumentVersionId(source.getDocumentVersionId());
        citation.setDocumentTitle(document.getTitle());
        citation.setVersionNo(document.getVersionNo());
        citation.setSourceFile(source.getSourceFile());
        citation.setPageStart(source.getPageStart());
        citation.setPageEnd(source.getPageEnd());
        citation.setSectionTitle(source.getSectionTitle());
        citation.setScore(source.getScore());
        citation.setRankNo(rank);
        return citation;
    }
}
