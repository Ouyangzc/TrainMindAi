package com.hezal.system.domain;

import java.util.ArrayList;
import java.util.List;
import com.hezal.common.core.domain.BaseEntity;

/** 学员课程 AI 问答消息。 */
public class StudentQaMessage extends BaseEntity
{
    private static final long serialVersionUID = 1L;
    private Long id;
    private Long tenantId;
    private Long sessionId;
    private Long userId;
    private Long courseId;
    private Long knowledgeBaseVersionId;
    private String role;
    private String content;
    private String status;
    private String rejectReason;
    private Long retrievalLogRef;
    private List<StudentQaCitation> citations = new ArrayList<>();

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }
    public Long getTenantId() { return tenantId; }
    public void setTenantId(Long tenantId) { this.tenantId = tenantId; }
    public Long getSessionId() { return sessionId; }
    public void setSessionId(Long sessionId) { this.sessionId = sessionId; }
    public Long getUserId() { return userId; }
    public void setUserId(Long userId) { this.userId = userId; }
    public Long getCourseId() { return courseId; }
    public void setCourseId(Long courseId) { this.courseId = courseId; }
    public Long getKnowledgeBaseVersionId() { return knowledgeBaseVersionId; }
    public void setKnowledgeBaseVersionId(Long value) { this.knowledgeBaseVersionId = value; }
    public String getRole() { return role; }
    public void setRole(String role) { this.role = role; }
    public String getContent() { return content; }
    public void setContent(String content) { this.content = content; }
    public String getStatus() { return status; }
    public void setStatus(String status) { this.status = status; }
    public String getRejectReason() { return rejectReason; }
    public void setRejectReason(String rejectReason) { this.rejectReason = rejectReason; }
    public Long getRetrievalLogRef() { return retrievalLogRef; }
    public void setRetrievalLogRef(Long retrievalLogRef) { this.retrievalLogRef = retrievalLogRef; }
    public List<StudentQaCitation> getCitations() { return citations; }
    public void setCitations(List<StudentQaCitation> citations) { this.citations = citations; }
}
