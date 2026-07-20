package com.hezal.system.domain;

import java.util.Date;
import com.fasterxml.jackson.annotation.JsonFormat;
import com.hezal.common.core.domain.BaseEntity;

/** 知识库版本 knowledge_base_version。 */
public class KnowledgeBaseVersion extends BaseEntity
{
    private static final long serialVersionUID = 1L;
    private Long id;
    private Long tenantId;
    private Long knowledgeBaseId;
    private Integer versionNo;
    private String status;
    private Integer chunkCount;
    private String chunkStrategyVersion;
    private String retrievalStrategyVersion;
    private Long embeddingIndexVersionId;
    private Long keywordIndexVersionId;
    private Long buildTaskId;
    private String buildErrorMessage;
    @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")
    private Date publishedAt;
    private String publishedBy;
    private String delFlag;

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }
    public Long getTenantId() { return tenantId; }
    public void setTenantId(Long tenantId) { this.tenantId = tenantId; }
    public Long getKnowledgeBaseId() { return knowledgeBaseId; }
    public void setKnowledgeBaseId(Long knowledgeBaseId) { this.knowledgeBaseId = knowledgeBaseId; }
    public Integer getVersionNo() { return versionNo; }
    public void setVersionNo(Integer versionNo) { this.versionNo = versionNo; }
    public String getStatus() { return status; }
    public void setStatus(String status) { this.status = status; }
    public Integer getChunkCount() { return chunkCount; }
    public void setChunkCount(Integer chunkCount) { this.chunkCount = chunkCount; }
    public String getChunkStrategyVersion() { return chunkStrategyVersion; }
    public void setChunkStrategyVersion(String value) { this.chunkStrategyVersion = value; }
    public String getRetrievalStrategyVersion() { return retrievalStrategyVersion; }
    public void setRetrievalStrategyVersion(String value) { this.retrievalStrategyVersion = value; }
    public Long getEmbeddingIndexVersionId() { return embeddingIndexVersionId; }
    public void setEmbeddingIndexVersionId(Long value) { this.embeddingIndexVersionId = value; }
    public Long getKeywordIndexVersionId() { return keywordIndexVersionId; }
    public void setKeywordIndexVersionId(Long value) { this.keywordIndexVersionId = value; }
    public Long getBuildTaskId() { return buildTaskId; }
    public void setBuildTaskId(Long buildTaskId) { this.buildTaskId = buildTaskId; }
    public String getBuildErrorMessage() { return buildErrorMessage; }
    public void setBuildErrorMessage(String value) { this.buildErrorMessage = value; }
    public Date getPublishedAt() { return publishedAt; }
    public void setPublishedAt(Date publishedAt) { this.publishedAt = publishedAt; }
    public String getPublishedBy() { return publishedBy; }
    public void setPublishedBy(String publishedBy) { this.publishedBy = publishedBy; }
    public String getDelFlag() { return delFlag; }
    public void setDelFlag(String delFlag) { this.delFlag = delFlag; }
}
