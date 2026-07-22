package com.hezal.system.domain.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Pattern;

/** 学员活动上报；身份、课程和展示文案均由服务端确定。 */
public class StudentActivityRequest
{
    @NotBlank(message = "活动类型不能为空")
    @Pattern(regexp = "course_view|module_view|document_view", message = "不支持的活动类型")
    private String activityType;
    private Long targetId;

    public String getActivityType() { return activityType; }
    public void setActivityType(String activityType) { this.activityType = activityType; }
    public Long getTargetId() { return targetId; }
    public void setTargetId(Long targetId) { this.targetId = targetId; }
}
