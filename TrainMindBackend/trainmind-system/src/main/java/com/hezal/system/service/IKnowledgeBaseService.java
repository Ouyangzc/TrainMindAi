package com.hezal.system.service;

import java.util.List;
import com.hezal.system.domain.KnowledgeBase;
import com.hezal.system.domain.KnowledgeBaseBuildTask;
import com.hezal.system.domain.KnowledgeBaseVersion;
import com.hezal.system.domain.KnowledgeBaseVersionDocument;

/** 知识库草稿与资料快照服务。 */
public interface IKnowledgeBaseService
{
    KnowledgeBase selectKnowledgeBase(Long courseId, String username);
    List<KnowledgeBaseVersion> selectVersions(Long courseId, String username);
    KnowledgeBaseVersion createDraft(Long courseId, String username);
    List<KnowledgeBaseVersionDocument> selectSnapshot(Long courseId, Long versionId, String username);
    List<KnowledgeBaseVersionDocument> saveSnapshot(Long courseId, Long versionId,
            List<Long> documentVersionIds, String username);
    KnowledgeBaseBuildTask build(Long courseId, Long versionId, String username);
    KnowledgeBaseBuildTask selectBuildStatus(Long courseId, Long versionId, String username);
    KnowledgeBaseVersion publish(Long courseId, Long versionId, String username);
    KnowledgeBaseVersion rollback(Long courseId, Long sourceVersionId, String username);
    List<KnowledgeBaseVersionDocument> selectPublishedDocuments(Long courseId, Long userId);
}
