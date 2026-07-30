package com.hezal.system.domain.dto;

/** 课程 AI 问答观测查询条件。 */
public class QaObservationQuery
{
    private String answerStatus;
    private String retrievalChannel;
    private String warningType;
    private String beginTime;
    private String endTime;

    public String getAnswerStatus() { return answerStatus; }
    public void setAnswerStatus(String answerStatus) { this.answerStatus = answerStatus; }
    public String getRetrievalChannel() { return retrievalChannel; }
    public void setRetrievalChannel(String retrievalChannel) { this.retrievalChannel = retrievalChannel; }
    public String getWarningType() { return warningType; }
    public void setWarningType(String warningType) { this.warningType = warningType; }
    public String getBeginTime() { return beginTime; }
    public void setBeginTime(String beginTime) { this.beginTime = beginTime; }
    public String getEndTime() { return endTime; }
    public void setEndTime(String endTime) { this.endTime = endTime; }
}
