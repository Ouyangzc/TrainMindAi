package com.hezal.system.domain;

import org.apache.commons.lang3.builder.ToStringBuilder;
import org.apache.commons.lang3.builder.ToStringStyle;
import com.hezal.common.core.domain.BaseEntity;

/**
 * 课程资料版本 course_document_version
 *
 * @author trainmind
 */
public class CourseDocumentVersion extends BaseEntity
{
    private static final long serialVersionUID = 1L;

    private Long id;
    private Long tenantId;
    private Long courseId;
    private Long moduleId;
    private Long documentId;
    private Integer versionNo;
    private String originalFilename;
    private String fileExt;
    private String contentType;
    private Long fileSize;
    private String checksumMd5;
    private String bucket;
    private String objectName;
    private String status;
    private Long parseTaskId;
    private String parseErrorMessage;
    private String delFlag;

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }
    public Long getTenantId() { return tenantId; }
    public void setTenantId(Long tenantId) { this.tenantId = tenantId; }
    public Long getCourseId() { return courseId; }
    public void setCourseId(Long courseId) { this.courseId = courseId; }
    public Long getModuleId() { return moduleId; }
    public void setModuleId(Long moduleId) { this.moduleId = moduleId; }
    public Long getDocumentId() { return documentId; }
    public void setDocumentId(Long documentId) { this.documentId = documentId; }
    public Integer getVersionNo() { return versionNo; }
    public void setVersionNo(Integer versionNo) { this.versionNo = versionNo; }
    public String getOriginalFilename() { return originalFilename; }
    public void setOriginalFilename(String originalFilename) { this.originalFilename = originalFilename; }
    public String getFileExt() { return fileExt; }
    public void setFileExt(String fileExt) { this.fileExt = fileExt; }
    public String getContentType() { return contentType; }
    public void setContentType(String contentType) { this.contentType = contentType; }
    public Long getFileSize() { return fileSize; }
    public void setFileSize(Long fileSize) { this.fileSize = fileSize; }
    public String getChecksumMd5() { return checksumMd5; }
    public void setChecksumMd5(String checksumMd5) { this.checksumMd5 = checksumMd5; }
    public String getBucket() { return bucket; }
    public void setBucket(String bucket) { this.bucket = bucket; }
    public String getObjectName() { return objectName; }
    public void setObjectName(String objectName) { this.objectName = objectName; }
    public String getStatus() { return status; }
    public void setStatus(String status) { this.status = status; }
    public Long getParseTaskId() { return parseTaskId; }
    public void setParseTaskId(Long parseTaskId) { this.parseTaskId = parseTaskId; }
    public String getParseErrorMessage() { return parseErrorMessage; }
    public void setParseErrorMessage(String parseErrorMessage) { this.parseErrorMessage = parseErrorMessage; }
    public String getDelFlag() { return delFlag; }
    public void setDelFlag(String delFlag) { this.delFlag = delFlag; }

    @Override
    public String toString()
    {
        return new ToStringBuilder(this, ToStringStyle.MULTI_LINE_STYLE)
                .append("id", getId())
                .append("documentId", getDocumentId())
                .append("versionNo", getVersionNo())
                .append("bucket", getBucket())
                .append("objectName", getObjectName())
                .append("status", getStatus())
                .append("delFlag", getDelFlag())
                .toString();
    }
}
