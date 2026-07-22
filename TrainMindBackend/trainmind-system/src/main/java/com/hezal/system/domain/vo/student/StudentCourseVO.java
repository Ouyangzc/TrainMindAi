package com.hezal.system.domain.vo.student;

import java.util.Date;
import com.fasterxml.jackson.annotation.JsonFormat;

/** 学员端课程只读视图。 */
public class StudentCourseVO
{
    private Long courseId;
    private String courseCode;
    private String courseName;
    private String courseCategory;
    private String description;
    private String ownerName;
    private String availability;
    @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")
    private Date accessStartAt;
    @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")
    private Date accessEndAt;
    private Long knowledgeBaseId;
    private Long publishedVersionId;
    private Integer publishedVersionNo;
    private Boolean allowDownload;
    @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")
    private Date lastVisitedAt;

    public Long getCourseId() { return courseId; }
    public void setCourseId(Long courseId) { this.courseId = courseId; }
    public String getCourseCode() { return courseCode; }
    public void setCourseCode(String courseCode) { this.courseCode = courseCode; }
    public String getCourseName() { return courseName; }
    public void setCourseName(String courseName) { this.courseName = courseName; }
    public String getCourseCategory() { return courseCategory; }
    public void setCourseCategory(String courseCategory) { this.courseCategory = courseCategory; }
    public String getDescription() { return description; }
    public void setDescription(String description) { this.description = description; }
    public String getOwnerName() { return ownerName; }
    public void setOwnerName(String ownerName) { this.ownerName = ownerName; }
    public String getAvailability() { return availability; }
    public void setAvailability(String availability) { this.availability = availability; }
    public Date getAccessStartAt() { return accessStartAt; }
    public void setAccessStartAt(Date accessStartAt) { this.accessStartAt = accessStartAt; }
    public Date getAccessEndAt() { return accessEndAt; }
    public void setAccessEndAt(Date accessEndAt) { this.accessEndAt = accessEndAt; }
    public Long getKnowledgeBaseId() { return knowledgeBaseId; }
    public void setKnowledgeBaseId(Long knowledgeBaseId) { this.knowledgeBaseId = knowledgeBaseId; }
    public Long getPublishedVersionId() { return publishedVersionId; }
    public void setPublishedVersionId(Long publishedVersionId) { this.publishedVersionId = publishedVersionId; }
    public Integer getPublishedVersionNo() { return publishedVersionNo; }
    public void setPublishedVersionNo(Integer publishedVersionNo) { this.publishedVersionNo = publishedVersionNo; }
    public Boolean getAllowDownload() { return allowDownload; }
    public void setAllowDownload(Boolean allowDownload) { this.allowDownload = allowDownload; }
    public Date getLastVisitedAt() { return lastVisitedAt; }
    public void setLastVisitedAt(Date lastVisitedAt) { this.lastVisitedAt = lastVisitedAt; }
}
