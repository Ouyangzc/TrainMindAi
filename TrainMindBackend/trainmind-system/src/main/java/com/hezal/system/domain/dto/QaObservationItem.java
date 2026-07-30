package com.hezal.system.domain.dto;

import java.math.BigDecimal;
import java.util.Date;

/** 课程 AI 问答观测列表项。 */
public class QaObservationItem
{
    private Long messageId;
    private Long sessionId;
    private Long userId;
    private String question;
    private String answerPreview;
    private String answerStatus;
    private String rejectReason;
    private Long retrievalLogRef;
    private String retrievalChannel;
    private String warningsJson;
    private Integer citationCount;
    private BigDecimal topScore;
    private Integer totalLatencyMs;
    private Date createTime;

    public Long getMessageId() { return messageId; }
    public void setMessageId(Long messageId) { this.messageId = messageId; }
    public Long getSessionId() { return sessionId; }
    public void setSessionId(Long sessionId) { this.sessionId = sessionId; }
    public Long getUserId() { return userId; }
    public void setUserId(Long userId) { this.userId = userId; }
    public String getQuestion() { return question; }
    public void setQuestion(String question) { this.question = question; }
    public String getAnswerPreview() { return answerPreview; }
    public void setAnswerPreview(String answerPreview) { this.answerPreview = answerPreview; }
    public String getAnswerStatus() { return answerStatus; }
    public void setAnswerStatus(String answerStatus) { this.answerStatus = answerStatus; }
    public String getRejectReason() { return rejectReason; }
    public void setRejectReason(String rejectReason) { this.rejectReason = rejectReason; }
    public Long getRetrievalLogRef() { return retrievalLogRef; }
    public void setRetrievalLogRef(Long retrievalLogRef) { this.retrievalLogRef = retrievalLogRef; }
    public String getRetrievalChannel() { return retrievalChannel; }
    public void setRetrievalChannel(String retrievalChannel) { this.retrievalChannel = retrievalChannel; }
    public String getWarningsJson() { return warningsJson; }
    public void setWarningsJson(String warningsJson) { this.warningsJson = warningsJson; }
    public Integer getCitationCount() { return citationCount; }
    public void setCitationCount(Integer citationCount) { this.citationCount = citationCount; }
    public BigDecimal getTopScore() { return topScore; }
    public void setTopScore(BigDecimal topScore) { this.topScore = topScore; }
    public Integer getTotalLatencyMs() { return totalLatencyMs; }
    public void setTotalLatencyMs(Integer totalLatencyMs) { this.totalLatencyMs = totalLatencyMs; }
    public Date getCreateTime() { return createTime; }
    public void setCreateTime(Date createTime) { this.createTime = createTime; }
}
