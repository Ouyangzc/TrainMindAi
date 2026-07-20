package com.hezal.system.domain;

import java.util.Date;
import com.fasterxml.jackson.annotation.JsonFormat;
import com.hezal.common.core.domain.BaseEntity;

/** 课程用户直接授权 course_user。 */
public class CourseUser extends BaseEntity
{
    private static final long serialVersionUID = 1L;
    private Long id;
    private Long tenantId;
    private Long courseId;
    private Long userId;
    private String accessRole;
    private String accessStatus;
    @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")
    private Date startAt;
    @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")
    private Date endAt;
    private String delFlag;
    private String userName;
    private String nickName;

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }
    public Long getTenantId() { return tenantId; }
    public void setTenantId(Long tenantId) { this.tenantId = tenantId; }
    public Long getCourseId() { return courseId; }
    public void setCourseId(Long courseId) { this.courseId = courseId; }
    public Long getUserId() { return userId; }
    public void setUserId(Long userId) { this.userId = userId; }
    public String getAccessRole() { return accessRole; }
    public void setAccessRole(String accessRole) { this.accessRole = accessRole; }
    public String getAccessStatus() { return accessStatus; }
    public void setAccessStatus(String accessStatus) { this.accessStatus = accessStatus; }
    public Date getStartAt() { return startAt; }
    public void setStartAt(Date startAt) { this.startAt = startAt; }
    public Date getEndAt() { return endAt; }
    public void setEndAt(Date endAt) { this.endAt = endAt; }
    public String getDelFlag() { return delFlag; }
    public void setDelFlag(String delFlag) { this.delFlag = delFlag; }
    public String getUserName() { return userName; }
    public void setUserName(String userName) { this.userName = userName; }
    public String getNickName() { return nickName; }
    public void setNickName(String nickName) { this.nickName = nickName; }
}
