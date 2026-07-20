package com.hezal.system.mapper;

import java.util.List;
import org.apache.ibatis.annotations.Param;
import com.hezal.system.domain.CourseDocumentVersion;
import com.hezal.system.domain.KnowledgeBase;
import com.hezal.system.domain.KnowledgeBaseVersion;
import com.hezal.system.domain.KnowledgeBaseVersionDocument;

/** 知识库治理数据访问。 */
public interface KnowledgeBaseMapper
{
    KnowledgeBase selectByCourseId(@Param("tenantId") Long tenantId, @Param("courseId") Long courseId);
    KnowledgeBase lockById(Long id);
    int insertKnowledgeBase(KnowledgeBase knowledgeBase);
    List<KnowledgeBaseVersion> selectVersions(Long knowledgeBaseId);
    KnowledgeBaseVersion selectVersion(@Param("knowledgeBaseId") Long knowledgeBaseId,
            @Param("versionId") Long versionId);
    KnowledgeBaseVersion lockVersion(@Param("knowledgeBaseId") Long knowledgeBaseId,
            @Param("versionId") Long versionId);
    KnowledgeBaseVersion selectActiveVersion(Long knowledgeBaseId);
    Integer selectMaxVersionNo(Long knowledgeBaseId);
    int insertVersion(KnowledgeBaseVersion version);
    int copySnapshot(@Param("sourceVersionId") Long sourceVersionId,
            @Param("targetVersionId") Long targetVersionId, @Param("username") String username);
    List<KnowledgeBaseVersionDocument> selectSnapshot(Long versionId);
    List<CourseDocumentVersion> selectParsedVersions(@Param("courseId") Long courseId,
            @Param("versionIds") List<Long> versionIds);
    int deleteSnapshot(@Param("versionId") Long versionId, @Param("username") String username);
    int insertSnapshot(KnowledgeBaseVersionDocument document);
    int countSnapshot(Long versionId);
    int updateBuildState(@Param("versionId") Long versionId, @Param("status") String status,
            @Param("taskId") Long taskId, @Param("errorMessage") String errorMessage,
            @Param("username") String username);
    int markBuildReady(@Param("versionId") Long versionId, @Param("username") String username);
    int archiveVersion(@Param("versionId") Long versionId, @Param("username") String username);
    int publishVersion(@Param("versionId") Long versionId, @Param("username") String username);
    int updateCurrentVersion(@Param("knowledgeBaseId") Long knowledgeBaseId,
            @Param("versionId") Long versionId, @Param("username") String username);
    List<KnowledgeBaseVersionDocument> selectPublishedDocuments(Long courseId);
    int countDocumentReferences(Long documentId);
}
