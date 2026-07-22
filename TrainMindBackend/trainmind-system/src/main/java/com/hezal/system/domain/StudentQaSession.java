package com.hezal.system.domain;

import com.hezal.common.core.domain.BaseEntity;

/** 学员课程 AI 问答会话。 */
public class StudentQaSession extends BaseEntity
{
    private static final long serialVersionUID = 1L;
    private Long id;
    private Long tenantId;
    private Long userId;
    private Long courseId;
    private String title;
    private String status;
    private String delFlag;

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }
    public Long getTenantId() { return tenantId; }
    public void setTenantId(Long tenantId) { this.tenantId = tenantId; }
    public Long getUserId() { return userId; }
    public void setUserId(Long userId) { this.userId = userId; }
    public Long getCourseId() { return courseId; }
    public void setCourseId(Long courseId) { this.courseId = courseId; }
    public String getTitle() { return title; }
    public void setTitle(String title) { this.title = title; }
    public String getStatus() { return status; }
    public void setStatus(String status) { this.status = status; }
    public String getDelFlag() { return delFlag; }
    public void setDelFlag(String delFlag) { this.delFlag = delFlag; }
}
