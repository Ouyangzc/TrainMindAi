package com.hezal.system.domain.vo.student;

/** 学员访问课程内容时由服务端解析的可信上下文。 */
public class StudentCourseContext
{
    private Long tenantId;
    private Long userId;
    private Long courseId;
    private Long courseUserId;
    private Long knowledgeBaseId;
    private Long publishedVersionId;
    private Integer publishedVersionNo;

    public Long getTenantId() { return tenantId; }
    public void setTenantId(Long tenantId) { this.tenantId = tenantId; }
    public Long getUserId() { return userId; }
    public void setUserId(Long userId) { this.userId = userId; }
    public Long getCourseId() { return courseId; }
    public void setCourseId(Long courseId) { this.courseId = courseId; }
    public Long getCourseUserId() { return courseUserId; }
    public void setCourseUserId(Long courseUserId) { this.courseUserId = courseUserId; }
    public Long getKnowledgeBaseId() { return knowledgeBaseId; }
    public void setKnowledgeBaseId(Long knowledgeBaseId) { this.knowledgeBaseId = knowledgeBaseId; }
    public Long getPublishedVersionId() { return publishedVersionId; }
    public void setPublishedVersionId(Long publishedVersionId) { this.publishedVersionId = publishedVersionId; }
    public Integer getPublishedVersionNo() { return publishedVersionNo; }
    public void setPublishedVersionNo(Integer publishedVersionNo) { this.publishedVersionNo = publishedVersionNo; }
}
