package com.hezal.system.domain.dto;

/** Java 业务后端调用 AI 问答的可信上下文。 */
public class AiQaRequest
{
    private Long userId;
    private Long courseId;
    private Long knowledgeBaseVersionId;
    private Long sessionId;
    private Long messageId;
    private String question;

    public Long getUserId() { return userId; }
    public void setUserId(Long userId) { this.userId = userId; }
    public Long getCourseId() { return courseId; }
    public void setCourseId(Long courseId) { this.courseId = courseId; }
    public Long getKnowledgeBaseVersionId() { return knowledgeBaseVersionId; }
    public void setKnowledgeBaseVersionId(Long value) { this.knowledgeBaseVersionId = value; }
    public Long getSessionId() { return sessionId; }
    public void setSessionId(Long sessionId) { this.sessionId = sessionId; }
    public Long getMessageId() { return messageId; }
    public void setMessageId(Long messageId) { this.messageId = messageId; }
    public String getQuestion() { return question; }
    public void setQuestion(String question) { this.question = question; }
}
