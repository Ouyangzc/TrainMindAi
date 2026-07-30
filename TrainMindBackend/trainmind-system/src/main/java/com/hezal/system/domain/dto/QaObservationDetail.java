package com.hezal.system.domain.dto;

import java.util.ArrayList;
import java.util.Date;
import java.util.List;
import com.hezal.system.domain.StudentQaCitation;

/** 课程 AI 问答观测详情。 */
public class QaObservationDetail
{
    private Long messageId;
    private Long sessionId;
    private Long userId;
    private String question;
    private String answer;
    private String answerStatus;
    private String rejectReason;
    private Long retrievalLogRef;
    private String retrievalChannel;
    private String warningsJson;
    private Integer retrievalLatencyMs;
    private Integer llmLatencyMs;
    private Integer firstTokenMs;
    private Integer totalLatencyMs;
    private Date createTime;
    private List<StudentQaCitation> citations = new ArrayList<>();
    private List<QaRetrievalTopSource> topSources = new ArrayList<>();

    public Long getMessageId() { return messageId; }
    public void setMessageId(Long messageId) { this.messageId = messageId; }
    public Long getSessionId() { return sessionId; }
    public void setSessionId(Long sessionId) { this.sessionId = sessionId; }
    public Long getUserId() { return userId; }
    public void setUserId(Long userId) { this.userId = userId; }
    public String getQuestion() { return question; }
    public void setQuestion(String question) { this.question = question; }
    public String getAnswer() { return answer; }
    public void setAnswer(String answer) { this.answer = answer; }
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
    public Integer getRetrievalLatencyMs() { return retrievalLatencyMs; }
    public void setRetrievalLatencyMs(Integer retrievalLatencyMs) { this.retrievalLatencyMs = retrievalLatencyMs; }
    public Integer getLlmLatencyMs() { return llmLatencyMs; }
    public void setLlmLatencyMs(Integer llmLatencyMs) { this.llmLatencyMs = llmLatencyMs; }
    public Integer getFirstTokenMs() { return firstTokenMs; }
    public void setFirstTokenMs(Integer firstTokenMs) { this.firstTokenMs = firstTokenMs; }
    public Integer getTotalLatencyMs() { return totalLatencyMs; }
    public void setTotalLatencyMs(Integer totalLatencyMs) { this.totalLatencyMs = totalLatencyMs; }
    public Date getCreateTime() { return createTime; }
    public void setCreateTime(Date createTime) { this.createTime = createTime; }
    public List<StudentQaCitation> getCitations() { return citations; }
    public void setCitations(List<StudentQaCitation> citations) { this.citations = citations; }
    public List<QaRetrievalTopSource> getTopSources() { return topSources; }
    public void setTopSources(List<QaRetrievalTopSource> topSources) { this.topSources = topSources; }
}
