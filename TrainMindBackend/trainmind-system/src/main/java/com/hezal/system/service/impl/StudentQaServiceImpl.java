package com.hezal.system.service.impl;

import java.io.IOException;
import java.io.OutputStream;
import java.math.BigDecimal;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.JsonNodeFactory;
import org.apache.commons.lang3.StringUtils;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import com.hezal.common.constant.TrainMindConstants;
import com.hezal.common.exception.ServiceException;
import com.hezal.system.ai.AiQaClient;
import com.hezal.system.domain.StudentQaCitation;
import com.hezal.system.domain.StudentQaMessage;
import com.hezal.system.domain.StudentQaSession;
import com.hezal.system.domain.dto.AiQaAnswer;
import com.hezal.system.domain.dto.AiQaHistoryTurn;
import com.hezal.system.domain.dto.AiQaRequest;
import com.hezal.system.domain.dto.AiQaSource;
import com.hezal.system.domain.dto.AiQaStreamEvent;
import com.hezal.system.domain.dto.QaObservationDetail;
import com.hezal.system.domain.dto.QaObservationItem;
import com.hezal.system.domain.dto.QaObservationQuery;
import com.hezal.system.domain.dto.QaObservationSummary;
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
    private static final int HISTORY_TURN_LIMIT = 3;
    private static final int HISTORY_USER_MAX_LENGTH = 300;
    private static final int HISTORY_ASSISTANT_MAX_LENGTH = 800;

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
    @Transactional
    public void deleteSession(Long courseId, Long sessionId, Long userId)
    {
        StudentCourseContext context = requirePublishedContext(courseId, userId);
        requireSession(context, courseId, sessionId, userId);
        qaMapper.deleteCitations(context.getTenantId(), sessionId);
        qaMapper.deleteMessages(context.getTenantId(), sessionId);
        if (qaMapper.deleteSession(context.getTenantId(), courseId, userId, sessionId) != 1)
        {
            throw new ServiceException("问答会话删除失败");
        }
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
        List<AiQaHistoryTurn> history = buildRecentHistory(
                qaMapper.selectMessages(context.getTenantId(), sessionId));
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
                    context, courseId, sessionId, assistant.getId(), userId, question, history));
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
    public void askStream(Long courseId, Long sessionId, Long userId, String rawQuestion,
            OutputStream outputStream) throws IOException
    {
        StudentCourseContext context = requirePublishedContext(courseId, userId);
        StudentQaSession session = requireSession(context, courseId, sessionId, userId);
        List<AiQaHistoryTurn> history = buildRecentHistory(
                qaMapper.selectMessages(context.getTenantId(), sessionId));
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

        StringBuilder answerBuffer = new StringBuilder();
        AiQaAnswer[] finalAnswer = new AiQaAnswer[1];
        try
        {
            AiQaRequest request = createAiRequest(
                    context, courseId, sessionId, assistant.getId(), userId, question, history);
            aiQaClient.answerStream(request, event -> {
                handleStreamEvent(event, answerBuffer, finalAnswer);
                writeSse(outputStream, event);
            });
            if (finalAnswer[0] != null)
            {
                if (!Objects.equals(context.getPublishedVersionId(),
                        finalAnswer[0].getKnowledgeBaseVersionId()))
                {
                    throw new ServiceException("AI回答所用知识库版本与当前课程发布版本不一致");
                }
                completeAssistant(context, courseId, assistant, finalAnswer[0]);
            }
            else
            {
                assistant.setContent(StringUtils.defaultIfBlank(
                        answerBuffer.toString(), UNAVAILABLE_ANSWER));
                assistant.setStatus("service_unavailable");
                assistant.setRejectReason("stream_incomplete");
                qaMapper.completeAssistantMessage(assistant);
            }
        }
        catch (ServiceException ex)
        {
            assistant.setContent(UNAVAILABLE_ANSWER);
            assistant.setStatus("service_unavailable");
            assistant.setRejectReason(ex.getMessage());
            qaMapper.completeAssistantMessage(assistant);
            writeSse(outputStream, new AiQaStreamEvent("error",
                    JsonNodeFactory.instance.objectNode().put("error", ex.getMessage())));
            writeSse(outputStream, new AiQaStreamEvent("done", null));
        }
        qaMapper.touchSession(sessionId);
        try
        {
            activityService.recordChat(courseId, userId, sessionId, question);
        }
        catch (RuntimeException ex)
        {
            log.warn("记录学员流式问答活动失败，courseId={}, sessionId={}", courseId, sessionId, ex);
        }
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

    @Override
    public QaObservationSummary selectObservationSummary(Long courseId, Long userId,
            QaObservationQuery query)
    {
        courseAccessService.requireManageAccess(courseId, userId);
        QaObservationSummary summary = qaMapper.selectQaObservationSummary(
                TrainMindConstants.DEFAULT_TENANT_ID, courseId, query);
        return summary == null ? new QaObservationSummary() : summary;
    }

    @Override
    public List<QaObservationItem> selectObservationList(Long courseId, Long userId,
            QaObservationQuery query)
    {
        courseAccessService.requireManageAccess(courseId, userId);
        return qaMapper.selectQaObservationList(
                TrainMindConstants.DEFAULT_TENANT_ID, courseId, query);
    }

    @Override
    public QaObservationDetail selectObservationDetail(Long courseId, Long userId, Long messageId)
    {
        courseAccessService.requireManageAccess(courseId, userId);
        QaObservationDetail detail = qaMapper.selectQaObservationDetail(
                TrainMindConstants.DEFAULT_TENANT_ID, courseId, messageId);
        if (detail == null)
        {
            throw new ServiceException("问答观测记录不存在");
        }
        detail.setCitations(qaMapper.selectCitations(
                TrainMindConstants.DEFAULT_TENANT_ID, messageId));
        detail.setTopSources(qaMapper.selectQaRetrievalTopSources(
                TrainMindConstants.DEFAULT_TENANT_ID, messageId));
        return detail;
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
            Long sessionId, Long messageId, Long userId, String question,
            List<AiQaHistoryTurn> history)
    {
        AiQaRequest request = new AiQaRequest();
        request.setUserId(userId);
        request.setCourseId(courseId);
        request.setKnowledgeBaseVersionId(context.getPublishedVersionId());
        request.setSessionId(sessionId);
        request.setMessageId(messageId);
        request.setQuestion(question);
        request.setHistory(history);
        return request;
    }

    private List<AiQaHistoryTurn> buildRecentHistory(List<StudentQaMessage> messages)
    {
        List<AiQaHistoryTurn> turns = new ArrayList<>();
        String pendingQuestion = null;
        for (StudentQaMessage message : messages)
        {
            if ("user".equals(message.getRole()) && "completed".equals(message.getStatus()))
            {
                pendingQuestion = message.getContent();
                continue;
            }
            if (!"assistant".equals(message.getRole()) || pendingQuestion == null)
            {
                continue;
            }
            if ("grounded".equals(message.getStatus()) || "completed".equals(message.getStatus()))
            {
                turns.add(new AiQaHistoryTurn(
                        StringUtils.abbreviate(pendingQuestion, HISTORY_USER_MAX_LENGTH),
                        StringUtils.abbreviate(message.getContent(), HISTORY_ASSISTANT_MAX_LENGTH)));
                pendingQuestion = null;
            }
        }
        int fromIndex = Math.max(turns.size() - HISTORY_TURN_LIMIT, 0);
        return new ArrayList<>(turns.subList(fromIndex, turns.size()));
    }

    private void handleStreamEvent(AiQaStreamEvent event, StringBuilder answerBuffer,
            AiQaAnswer[] finalAnswer)
    {
        JsonNode data = event.getData();
        if ("token".equals(event.getEvent()) && data != null && data.has("token"))
        {
            answerBuffer.append(data.path("token").asText());
            return;
        }
        if ("sources".equals(event.getEvent()) && data != null)
        {
            finalAnswer[0] = toAiQaAnswer(data, answerBuffer.toString());
        }
    }

    private AiQaAnswer toAiQaAnswer(JsonNode data, String fallbackAnswer)
    {
        AiQaAnswer answer = new AiQaAnswer();
        answer.setAnswer(data.path("answer").asText(fallbackAnswer));
        answer.setAnswerStatus(data.path("answer_status").asText("grounded"));
        if (data.path("knowledge_base_version_id").isIntegralNumber())
        {
            answer.setKnowledgeBaseVersionId(data.path("knowledge_base_version_id").asLong());
        }
        answer.setRejectReason(text(data, "reject_reason"));
        if (data.path("retrieval_log_ref").isIntegralNumber())
        {
            answer.setRetrievalLogRef(data.path("retrieval_log_ref").asLong());
        }
        List<AiQaSource> sources = new ArrayList<>();
        if (data.path("sources").isArray())
        {
            for (JsonNode item : data.path("sources"))
            {
                sources.add(toAiQaSource(item));
            }
        }
        answer.setSources(sources);
        return answer;
    }

    private AiQaSource toAiQaSource(JsonNode item)
    {
        AiQaSource source = new AiQaSource();
        source.setChunkId(longValue(item, "chunk_id"));
        source.setSourceIndex(intValue(item, "source_index"));
        source.setDocumentId(longValue(item, "document_id"));
        source.setDocumentVersionId(longValue(item, "document_version_id"));
        source.setSourceFile(text(item, "source_file"));
        source.setPageStart(intValue(item, "page_start"));
        source.setPageEnd(intValue(item, "page_end"));
        source.setSectionTitle(text(item, "section_title"));
        if (item.path("score").isNumber())
        {
            source.setScore(BigDecimal.valueOf(item.path("score").asDouble()));
        }
        return source;
    }

    private void writeSse(OutputStream outputStream, AiQaStreamEvent event) throws IOException
    {
        String data = event.getData() == null ? "{}" : event.getData().toString();
        String frame = "event: " + event.getEvent() + "\n"
                + "data: " + data + "\n\n";
        outputStream.write(frame.getBytes(StandardCharsets.UTF_8));
        outputStream.flush();
    }

    private String text(JsonNode data, String field)
    {
        JsonNode value = data.path(field);
        return value.isMissingNode() || value.isNull() ? null : value.asText();
    }

    private Long longValue(JsonNode data, String field)
    {
        JsonNode value = data.path(field);
        return value.isIntegralNumber() ? value.asLong() : null;
    }

    private Integer intValue(JsonNode data, String field)
    {
        JsonNode value = data.path(field);
        return value.isIntegralNumber() ? value.asInt() : null;
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
