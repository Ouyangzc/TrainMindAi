package com.hezal.system.domain;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;
import org.apache.commons.lang3.builder.ToStringBuilder;
import org.apache.commons.lang3.builder.ToStringStyle;
import com.hezal.common.core.domain.BaseEntity;

/**
 * 课程资料 course_document
 *
 * @author trainmind
 */
public class CourseDocument extends BaseEntity
{
    private static final long serialVersionUID = 1L;

    private Long id;
    private Long tenantId;
    private Long courseId;
    private Long moduleId;
    private String title;
    private String documentType;
    private Long latestVersionId;
    private String status;
    private String delFlag;

    private String moduleName;
    private Integer versionNo;
    private String originalFilename;
    private String fileExt;
    private Long fileSize;
    /** 最新资料版本状态 */
    private String versionStatus;

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }
    public Long getTenantId() { return tenantId; }
    public void setTenantId(Long tenantId) { this.tenantId = tenantId; }
    @NotNull(message = "课程ID不能为空")
    public Long getCourseId() { return courseId; }
    public void setCourseId(Long courseId) { this.courseId = courseId; }
    public Long getModuleId() { return moduleId; }
    public void setModuleId(Long moduleId) { this.moduleId = moduleId; }
    @NotBlank(message = "资料标题不能为空")
    @Size(max = 255, message = "资料标题长度不能超过255个字符")
    public String getTitle() { return title; }
    public void setTitle(String title) { this.title = title; }
    public String getDocumentType() { return documentType; }
    public void setDocumentType(String documentType) { this.documentType = documentType; }
    public Long getLatestVersionId() { return latestVersionId; }
    public void setLatestVersionId(Long latestVersionId) { this.latestVersionId = latestVersionId; }
    public String getStatus() { return status; }
    public void setStatus(String status) { this.status = status; }
    public String getDelFlag() { return delFlag; }
    public void setDelFlag(String delFlag) { this.delFlag = delFlag; }
    public String getModuleName() { return moduleName; }
    public void setModuleName(String moduleName) { this.moduleName = moduleName; }
    public Integer getVersionNo() { return versionNo; }
    public void setVersionNo(Integer versionNo) { this.versionNo = versionNo; }
    public String getOriginalFilename() { return originalFilename; }
    public void setOriginalFilename(String originalFilename) { this.originalFilename = originalFilename; }
    public String getFileExt() { return fileExt; }
    public void setFileExt(String fileExt) { this.fileExt = fileExt; }
    public Long getFileSize() { return fileSize; }
    public void setFileSize(Long fileSize) { this.fileSize = fileSize; }
    public String getVersionStatus() { return versionStatus; }
    public void setVersionStatus(String versionStatus) { this.versionStatus = versionStatus; }

    @Override
    public String toString()
    {
        return new ToStringBuilder(this, ToStringStyle.MULTI_LINE_STYLE)
                .append("id", getId())
                .append("tenantId", getTenantId())
                .append("courseId", getCourseId())
                .append("moduleId", getModuleId())
                .append("title", getTitle())
                .append("documentType", getDocumentType())
                .append("latestVersionId", getLatestVersionId())
                .append("status", getStatus())
                .append("delFlag", getDelFlag())
                .append("remark", getRemark())
                .toString();
    }
}
