package com.hezal.system.domain.dto;

/** 转移课程主负责人请求。 */
public class CourseOwnerTransferRequest
{
    private Long targetUserId;

    public Long getTargetUserId() { return targetUserId; }
    public void setTargetUserId(Long targetUserId) { this.targetUserId = targetUserId; }
}
