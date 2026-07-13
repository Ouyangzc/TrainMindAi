package com.hezal.system.domain;

import java.util.Date;

import com.fasterxml.jackson.annotation.JsonFormat;
import com.hezal.common.core.domain.BaseEntity;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;
import org.apache.commons.lang3.builder.ToStringBuilder;
import org.apache.commons.lang3.builder.ToStringStyle;

/**
 * 课程 course
 *
 * @author trainmind
 */
public class Course extends BaseEntity
{
    private static final long serialVersionUID = 1L;

    private Long id;
    private Long tenantId;
    private String courseCode;
    private String courseName;
    private String courseCategory;
    private String description;
    private Long ownerUserId;
    private String ownerName;
    @JsonFormat(pattern = "yyyy-MM-dd")
    private Date startDate;
    private String status;
    private Integer sortOrder;
    private String delFlag;

    /** 模块数量，用于课程管理列表展示。 */
    private Integer moduleCount;
    /** 资料数量，用于课程管理列表展示。 */
    private Integer documentCount;
    /** 已解析资料数量，用于课程管理列表展示。 */
    private Integer parsedCount;
    /** 学员数量，课程成员后端落地前默认为0。 */
    private Integer studentCount;
    /** 当前发布知识库版本，知识库治理落地前为空。 */
    private String currentVersion;
    /** 当前发布知识库版本状态，知识库治理落地前为空。 */
    private String currentVersionStatus;

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }
    public Long getTenantId() { return tenantId; }
    public void setTenantId(Long tenantId) { this.tenantId = tenantId; }
    @Size(max = 64, message = "课程编码长度不能超过64个字符")
    public String getCourseCode() { return courseCode; }
    public void setCourseCode(String courseCode) { this.courseCode = courseCode; }
    @NotBlank(message = "课程名称不能为空")
    @Size(max = 200, message = "课程名称长度不能超过200个字符")
    public String getCourseName() { return courseName; }
    public void setCourseName(String courseName) { this.courseName = courseName; }
    @Size(max = 100, message = "课程分类长度不能超过100个字符")
    public String getCourseCategory() { return courseCategory; }
    public void setCourseCategory(String courseCategory) { this.courseCategory = courseCategory; }
    @Size(max = 1000, message = "课程简介长度不能超过1000个字符")
    public String getDescription() { return description; }
    public void setDescription(String description) { this.description = description; }
    public Long getOwnerUserId() { return ownerUserId; }
    public void setOwnerUserId(Long ownerUserId) { this.ownerUserId = ownerUserId; }
    public String getOwnerName() { return ownerName; }
    public void setOwnerName(String ownerName) { this.ownerName = ownerName; }
    public Date getStartDate() { return startDate; }
    public void setStartDate(Date startDate) { this.startDate = startDate; }
    public String getStatus() { return status; }
    public void setStatus(String status) { this.status = status; }
    public Integer getSortOrder() { return sortOrder; }
    public void setSortOrder(Integer sortOrder) { this.sortOrder = sortOrder; }
    public String getDelFlag() { return delFlag; }
    public void setDelFlag(String delFlag) { this.delFlag = delFlag; }
    public Integer getModuleCount() { return moduleCount; }
    public void setModuleCount(Integer moduleCount) { this.moduleCount = moduleCount; }
    public Integer getDocumentCount() { return documentCount; }
    public void setDocumentCount(Integer documentCount) { this.documentCount = documentCount; }
    public Integer getParsedCount() { return parsedCount; }
    public void setParsedCount(Integer parsedCount) { this.parsedCount = parsedCount; }
    public Integer getStudentCount() { return studentCount; }
    public void setStudentCount(Integer studentCount) { this.studentCount = studentCount; }
    public String getCurrentVersion() { return currentVersion; }
    public void setCurrentVersion(String currentVersion) { this.currentVersion = currentVersion; }
    public String getCurrentVersionStatus() { return currentVersionStatus; }
    public void setCurrentVersionStatus(String currentVersionStatus) { this.currentVersionStatus = currentVersionStatus; }

    @Override
    public String toString()
    {
        return new ToStringBuilder(this, ToStringStyle.MULTI_LINE_STYLE)
                .append("id", getId())
                .append("tenantId", getTenantId())
                .append("courseCode", getCourseCode())
                .append("courseName", getCourseName())
                .append("courseCategory", getCourseCategory())
                .append("description", getDescription())
                .append("ownerUserId", getOwnerUserId())
                .append("startDate", getStartDate())
                .append("status", getStatus())
                .append("sortOrder", getSortOrder())
                .append("delFlag", getDelFlag())
                .append("remark", getRemark())
                .toString();
    }
}
