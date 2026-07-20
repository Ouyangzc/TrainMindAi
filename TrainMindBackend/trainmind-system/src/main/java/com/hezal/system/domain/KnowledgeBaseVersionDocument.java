package com.hezal.system.domain;

import com.hezal.common.core.domain.BaseEntity;

/** 知识库版本资料快照 knowledge_base_version_document。 */
public class KnowledgeBaseVersionDocument extends BaseEntity
{
    private static final long serialVersionUID = 1L;
    private Long id;
    private Long tenantId;
    private Long knowledgeBaseVersionId;
    private Long documentId;
    private Long documentVersionId;
    private String delFlag;
    private String documentTitle;
    private Integer versionNo;
    private String originalFilename;
    private String fileExt;
    private String versionStatus;
    private Long moduleId;

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }
    public Long getTenantId() { return tenantId; }
    public void setTenantId(Long tenantId) { this.tenantId = tenantId; }
    public Long getKnowledgeBaseVersionId() { return knowledgeBaseVersionId; }
    public void setKnowledgeBaseVersionId(Long value) { this.knowledgeBaseVersionId = value; }
    public Long getDocumentId() { return documentId; }
    public void setDocumentId(Long documentId) { this.documentId = documentId; }
    public Long getDocumentVersionId() { return documentVersionId; }
    public void setDocumentVersionId(Long value) { this.documentVersionId = value; }
    public String getDelFlag() { return delFlag; }
    public void setDelFlag(String delFlag) { this.delFlag = delFlag; }
    public String getDocumentTitle() { return documentTitle; }
    public void setDocumentTitle(String documentTitle) { this.documentTitle = documentTitle; }
    public Integer getVersionNo() { return versionNo; }
    public void setVersionNo(Integer versionNo) { this.versionNo = versionNo; }
    public String getOriginalFilename() { return originalFilename; }
    public void setOriginalFilename(String originalFilename) { this.originalFilename = originalFilename; }
    public String getFileExt() { return fileExt; }
    public void setFileExt(String fileExt) { this.fileExt = fileExt; }
    public String getVersionStatus() { return versionStatus; }
    public void setVersionStatus(String versionStatus) { this.versionStatus = versionStatus; }
    public Long getModuleId() { return moduleId; }
    public void setModuleId(Long moduleId) { this.moduleId = moduleId; }
}
