package com.hezal.system.domain;

import java.util.Date;
import com.fasterxml.jackson.annotation.JsonFormat;
import com.hezal.common.core.domain.BaseEntity;

/** 学员在课程内真实发生的轻量活动。 */
public class StudentLearningActivity extends BaseEntity
{
    private static final long serialVersionUID = 1L;
    private Long id;
    private Long tenantId;
    private Long userId;
    private Long courseId;
    private String activityType;
    private Long targetId;
    private String targetTitle;
    private String targetDetail;
    @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")
    private Date occurredAt;
    private String metadataJson;

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }
    public Long getTenantId() { return tenantId; }
    public void setTenantId(Long tenantId) { this.tenantId = tenantId; }
    public Long getUserId() { return userId; }
    public void setUserId(Long userId) { this.userId = userId; }
    public Long getCourseId() { return courseId; }
    public void setCourseId(Long courseId) { this.courseId = courseId; }
    public String getActivityType() { return activityType; }
    public void setActivityType(String activityType) { this.activityType = activityType; }
    public Long getTargetId() { return targetId; }
    public void setTargetId(Long targetId) { this.targetId = targetId; }
    public String getTargetTitle() { return targetTitle; }
    public void setTargetTitle(String targetTitle) { this.targetTitle = targetTitle; }
    public String getTargetDetail() { return targetDetail; }
    public void setTargetDetail(String targetDetail) { this.targetDetail = targetDetail; }
    public Date getOccurredAt() { return occurredAt; }
    public void setOccurredAt(Date occurredAt) { this.occurredAt = occurredAt; }
    public String getMetadataJson() { return metadataJson; }
    public void setMetadataJson(String metadataJson) { this.metadataJson = metadataJson; }
}
