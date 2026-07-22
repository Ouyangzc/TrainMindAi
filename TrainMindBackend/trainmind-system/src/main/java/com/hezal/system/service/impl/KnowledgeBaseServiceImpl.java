package com.hezal.system.service.impl;

import java.util.Collections;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import org.springframework.dao.DuplicateKeyException;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import com.hezal.common.constant.TrainMindConstants;
import com.hezal.common.exception.ServiceException;
import com.hezal.system.domain.Course;
import com.hezal.system.domain.CourseDocumentVersion;
import com.hezal.system.domain.KnowledgeBase;
import com.hezal.system.domain.KnowledgeBaseBuildTask;
import com.hezal.system.domain.KnowledgeBaseVersion;
import com.hezal.system.domain.KnowledgeBaseVersionDocument;
import com.hezal.system.mapper.CourseMapper;
import com.hezal.system.mapper.KnowledgeBaseMapper;
import com.hezal.system.ai.AiKnowledgeBaseClient;
import com.hezal.system.service.IKnowledgeBaseService;
import com.hezal.system.service.CourseAccessService;

/** 知识库草稿与资料快照服务实现。 */
@Service
public class KnowledgeBaseServiceImpl implements IKnowledgeBaseService
{
    private static final String DEFAULT_CHUNK_STRATEGY_VERSION = "v1";
    private static final String DEFAULT_RETRIEVAL_STRATEGY_VERSION = "v1";

    private final KnowledgeBaseMapper knowledgeBaseMapper;
    private final CourseMapper courseMapper;
    private final AiKnowledgeBaseClient aiKnowledgeBaseClient;
    private final CourseAccessService courseAccessService;

    public KnowledgeBaseServiceImpl(KnowledgeBaseMapper knowledgeBaseMapper, CourseMapper courseMapper,
            AiKnowledgeBaseClient aiKnowledgeBaseClient, CourseAccessService courseAccessService)
    {
        this.knowledgeBaseMapper = knowledgeBaseMapper;
        this.courseMapper = courseMapper;
        this.aiKnowledgeBaseClient = aiKnowledgeBaseClient;
        this.courseAccessService = courseAccessService;
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public KnowledgeBase selectKnowledgeBase(Long courseId, String username)
    {
        return ensureKnowledgeBase(courseId, username);
    }

    @Override
    public List<KnowledgeBaseVersion> selectVersions(Long courseId, String username)
    {
        KnowledgeBase knowledgeBase = ensureKnowledgeBase(courseId, username);
        return knowledgeBaseMapper.selectVersions(knowledgeBase.getId());
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public KnowledgeBaseVersion createDraft(Long courseId, String username)
    {
        KnowledgeBase knowledgeBase = ensureKnowledgeBase(courseId, username);
        knowledgeBaseMapper.lockById(knowledgeBase.getId());
        KnowledgeBaseVersion active = knowledgeBaseMapper.selectActiveVersion(knowledgeBase.getId());
        if (active != null)
        {
            return active;
        }

        KnowledgeBaseVersion version = new KnowledgeBaseVersion();
        version.setTenantId(knowledgeBase.getTenantId());
        version.setKnowledgeBaseId(knowledgeBase.getId());
        version.setVersionNo(knowledgeBaseMapper.selectMaxVersionNo(knowledgeBase.getId()) + 1);
        version.setStatus(TrainMindConstants.KNOWLEDGE_BASE_VERSION_STATUS_DRAFT);
        version.setChunkCount(0);
        version.setChunkStrategyVersion(DEFAULT_CHUNK_STRATEGY_VERSION);
        version.setRetrievalStrategyVersion(DEFAULT_RETRIEVAL_STRATEGY_VERSION);
        version.setCreateBy(username);
        knowledgeBaseMapper.insertVersion(version);
        if (knowledgeBase.getCurrentVersionId() != null)
        {
            knowledgeBaseMapper.copySnapshot(knowledgeBase.getCurrentVersionId(), version.getId(), username);
        }
        return version;
    }

    @Override
    public List<KnowledgeBaseVersionDocument> selectSnapshot(
            Long courseId, Long versionId, String username)
    {
        requireVersion(courseId, versionId, username);
        return knowledgeBaseMapper.selectSnapshot(versionId);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public List<KnowledgeBaseVersionDocument> saveSnapshot(Long courseId, Long versionId,
            List<Long> documentVersionIds, String username)
    {
        KnowledgeBaseVersion version = requireVersion(courseId, versionId, username);
        if (!TrainMindConstants.KNOWLEDGE_BASE_VERSION_STATUS_DRAFT.equals(version.getStatus()))
        {
            throw new ServiceException("只有草稿版本可以修改资料快照");
        }

        List<Long> ids = documentVersionIds == null
                ? Collections.emptyList() : documentVersionIds.stream().distinct().toList();
        List<CourseDocumentVersion> versions = ids.isEmpty()
                ? Collections.emptyList() : knowledgeBaseMapper.selectParsedVersions(courseId, ids);
        if (versions.size() != ids.size())
        {
            throw new ServiceException("资料版本不存在、未解析或不属于当前课程");
        }
        Set<Long> documentIds = new HashSet<>();
        for (CourseDocumentVersion item : versions)
        {
            if (!documentIds.add(item.getDocumentId()))
            {
                throw new ServiceException("同一资料只能选择一个版本");
            }
        }

        knowledgeBaseMapper.deleteSnapshot(versionId, username);
        for (CourseDocumentVersion item : versions)
        {
            KnowledgeBaseVersionDocument snapshot = new KnowledgeBaseVersionDocument();
            snapshot.setTenantId(item.getTenantId());
            snapshot.setKnowledgeBaseVersionId(versionId);
            snapshot.setDocumentId(item.getDocumentId());
            snapshot.setDocumentVersionId(item.getId());
            snapshot.setCreateBy(username);
            knowledgeBaseMapper.insertSnapshot(snapshot);
        }
        return knowledgeBaseMapper.selectSnapshot(versionId);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public KnowledgeBaseBuildTask build(Long courseId, Long versionId, String username)
    {
        KnowledgeBaseVersion version = requireVersion(courseId, versionId, username);
        if (!TrainMindConstants.KNOWLEDGE_BASE_VERSION_STATUS_DRAFT.equals(version.getStatus())
                && !TrainMindConstants.KNOWLEDGE_BASE_VERSION_STATUS_FAILED.equals(version.getStatus()))
        {
            throw new ServiceException("只有草稿或构建失败版本可以发起构建");
        }
        if (knowledgeBaseMapper.countSnapshot(versionId) == 0)
        {
            throw new ServiceException("知识库草稿未选择资料");
        }
        KnowledgeBaseBuildTask task = aiKnowledgeBaseClient.createBuildTask(versionId);
        knowledgeBaseMapper.updateBuildState(versionId,
                TrainMindConstants.KNOWLEDGE_BASE_VERSION_STATUS_BUILDING,
                task.getId(), null, username);
        return task;
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public KnowledgeBaseBuildTask selectBuildStatus(Long courseId, Long versionId, String username)
    {
        KnowledgeBaseVersion version = requireVersion(courseId, versionId, username);
        if (version.getBuildTaskId() == null)
        {
            throw new ServiceException("知识库版本尚未创建构建任务");
        }
        KnowledgeBaseBuildTask task = aiKnowledgeBaseClient.getBuildTask(version.getBuildTaskId());
        if ("success".equals(task.getStatus()))
        {
            knowledgeBaseMapper.markBuildReady(versionId, username);
        }
        else if ("failed".equals(task.getStatus()) || "cancelled".equals(task.getStatus()))
        {
            knowledgeBaseMapper.updateBuildState(versionId,
                    TrainMindConstants.KNOWLEDGE_BASE_VERSION_STATUS_FAILED,
                    task.getId(), task.getErrorMessage(), username);
        }
        else
        {
            knowledgeBaseMapper.updateBuildState(versionId,
                    TrainMindConstants.KNOWLEDGE_BASE_VERSION_STATUS_BUILDING,
                    task.getId(), null, username);
        }
        return task;
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public KnowledgeBaseVersion publish(Long courseId, Long versionId, String username)
    {
        KnowledgeBase knowledgeBase = ensureKnowledgeBase(courseId, username);
        KnowledgeBase lockedKnowledgeBase = knowledgeBaseMapper.lockById(knowledgeBase.getId());
        KnowledgeBaseVersion version = knowledgeBaseMapper.lockVersion(knowledgeBase.getId(), versionId);
        if (version == null)
        {
            throw new ServiceException("知识库版本不存在");
        }
        if (!TrainMindConstants.KNOWLEDGE_BASE_VERSION_STATUS_READY.equals(version.getStatus()))
        {
            throw new ServiceException("只有待发布版本可以发布");
        }
        if (lockedKnowledgeBase.getCurrentVersionId() != null
                && !lockedKnowledgeBase.getCurrentVersionId().equals(versionId))
        {
            knowledgeBaseMapper.archiveVersion(lockedKnowledgeBase.getCurrentVersionId(), username);
        }
        if (knowledgeBaseMapper.publishVersion(versionId, username) == 0)
        {
            throw new ServiceException("知识库版本状态已变化，请刷新后重试");
        }
        knowledgeBaseMapper.updateCurrentVersion(knowledgeBase.getId(), versionId, username);
        return knowledgeBaseMapper.selectVersion(knowledgeBase.getId(), versionId);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public KnowledgeBaseVersion rollback(Long courseId, Long sourceVersionId, String username)
    {
        KnowledgeBase knowledgeBase = ensureKnowledgeBase(courseId, username);
        knowledgeBaseMapper.lockById(knowledgeBase.getId());
        KnowledgeBaseVersion source = knowledgeBaseMapper.lockVersion(
                knowledgeBase.getId(), sourceVersionId);
        if (source == null)
        {
            throw new ServiceException("回滚来源版本不存在");
        }
        if (!TrainMindConstants.KNOWLEDGE_BASE_VERSION_STATUS_PUBLISHED.equals(source.getStatus())
                && !TrainMindConstants.KNOWLEDGE_BASE_VERSION_STATUS_ARCHIVED.equals(source.getStatus()))
        {
            throw new ServiceException("只能基于已发布或已归档版本创建回滚草稿");
        }
        if (knowledgeBaseMapper.selectActiveVersion(knowledgeBase.getId()) != null)
        {
            throw new ServiceException("当前存在活动版本，不能创建回滚草稿");
        }

        KnowledgeBaseVersion target = new KnowledgeBaseVersion();
        target.setTenantId(knowledgeBase.getTenantId());
        target.setKnowledgeBaseId(knowledgeBase.getId());
        target.setVersionNo(knowledgeBaseMapper.selectMaxVersionNo(knowledgeBase.getId()) + 1);
        target.setStatus(TrainMindConstants.KNOWLEDGE_BASE_VERSION_STATUS_DRAFT);
        target.setChunkCount(0);
        target.setChunkStrategyVersion(source.getChunkStrategyVersion());
        target.setRetrievalStrategyVersion(source.getRetrievalStrategyVersion());
        target.setCreateBy(username);
        target.setRemark("基于 V" + source.getVersionNo() + " 创建的回滚草稿");
        knowledgeBaseMapper.insertVersion(target);
        knowledgeBaseMapper.copySnapshot(sourceVersionId, target.getId(), username);
        return target;
    }

    @Override
    public List<KnowledgeBaseVersionDocument> selectPublishedDocuments(Long courseId, Long userId)
    {
        courseAccessService.requireStudentAccess(courseId, userId);
        return knowledgeBaseMapper.selectPublishedDocuments(courseId);
    }

    private KnowledgeBaseVersion requireVersion(Long courseId, Long versionId, String username)
    {
        KnowledgeBase knowledgeBase = ensureKnowledgeBase(courseId, username);
        KnowledgeBaseVersion version = knowledgeBaseMapper.selectVersion(knowledgeBase.getId(), versionId);
        if (version == null)
        {
            throw new ServiceException("知识库版本不存在");
        }
        return version;
    }

    private KnowledgeBase ensureKnowledgeBase(Long courseId, String username)
    {
        Course course = courseMapper.selectCourseById(courseId);
        if (course == null)
        {
            throw new ServiceException("课程不存在");
        }
        KnowledgeBase existing = knowledgeBaseMapper.selectByCourseId(course.getTenantId(), courseId);
        if (existing != null)
        {
            return existing;
        }
        KnowledgeBase knowledgeBase = new KnowledgeBase();
        knowledgeBase.setTenantId(course.getTenantId());
        knowledgeBase.setCourseId(courseId);
        knowledgeBase.setName(course.getCourseName() + "知识库");
        knowledgeBase.setDescription(course.getDescription());
        knowledgeBase.setStatus(TrainMindConstants.KNOWLEDGE_BASE_STATUS_ACTIVE);
        knowledgeBase.setCreateBy(username);
        try
        {
            knowledgeBaseMapper.insertKnowledgeBase(knowledgeBase);
            return knowledgeBase;
        }
        catch (DuplicateKeyException exception)
        {
            return knowledgeBaseMapper.selectByCourseId(course.getTenantId(), courseId);
        }
    }
}
