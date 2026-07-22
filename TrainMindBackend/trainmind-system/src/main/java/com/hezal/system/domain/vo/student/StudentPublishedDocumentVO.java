package com.hezal.system.domain.vo.student;

/** 当前发布知识库快照中的学员资料。 */
public class StudentPublishedDocumentVO
{
    private Long documentId;
    private Long documentVersionId;
    private String title;
    private String documentType;
    private Integer versionNo;
    private String originalFilename;
    private String fileExt;
    private Long fileSize;
    private Long moduleId;
    private String moduleCode;
    private String moduleName;
    private String moduleDescription;
    private Integer moduleSortOrder;

    public Long getDocumentId() { return documentId; }
    public void setDocumentId(Long documentId) { this.documentId = documentId; }
    public Long getDocumentVersionId() { return documentVersionId; }
    public void setDocumentVersionId(Long documentVersionId) { this.documentVersionId = documentVersionId; }
    public String getTitle() { return title; }
    public void setTitle(String title) { this.title = title; }
    public String getDocumentType() { return documentType; }
    public void setDocumentType(String documentType) { this.documentType = documentType; }
    public Integer getVersionNo() { return versionNo; }
    public void setVersionNo(Integer versionNo) { this.versionNo = versionNo; }
    public String getOriginalFilename() { return originalFilename; }
    public void setOriginalFilename(String originalFilename) { this.originalFilename = originalFilename; }
    public String getFileExt() { return fileExt; }
    public void setFileExt(String fileExt) { this.fileExt = fileExt; }
    public Long getFileSize() { return fileSize; }
    public void setFileSize(Long fileSize) { this.fileSize = fileSize; }
    public Long getModuleId() { return moduleId; }
    public void setModuleId(Long moduleId) { this.moduleId = moduleId; }
    public String getModuleCode() { return moduleCode; }
    public void setModuleCode(String moduleCode) { this.moduleCode = moduleCode; }
    public String getModuleName() { return moduleName; }
    public void setModuleName(String moduleName) { this.moduleName = moduleName; }
    public String getModuleDescription() { return moduleDescription; }
    public void setModuleDescription(String moduleDescription) { this.moduleDescription = moduleDescription; }
    public Integer getModuleSortOrder() { return moduleSortOrder; }
    public void setModuleSortOrder(Integer moduleSortOrder) { this.moduleSortOrder = moduleSortOrder; }
}
