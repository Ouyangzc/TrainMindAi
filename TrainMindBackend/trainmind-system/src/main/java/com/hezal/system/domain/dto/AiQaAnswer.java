package com.hezal.system.domain.dto;

import java.util.ArrayList;
import java.util.List;
import com.fasterxml.jackson.annotation.JsonProperty;

/** AI 服务问答响应。 */
public class AiQaAnswer
{
    private String answer;
    @JsonProperty("answer_status")
    private String answerStatus;
    @JsonProperty("knowledge_base_version_id")
    private Long knowledgeBaseVersionId;
    @JsonProperty("reject_reason")
    private String rejectReason;
    @JsonProperty("retrieval_log_ref")
    private Long retrievalLogRef;
    private List<AiQaSource> sources = new ArrayList<>();

    public String getAnswer() { return answer; }
    public void setAnswer(String answer) { this.answer = answer; }
    public String getAnswerStatus() { return answerStatus; }
    public void setAnswerStatus(String answerStatus) { this.answerStatus = answerStatus; }
    public Long getKnowledgeBaseVersionId() { return knowledgeBaseVersionId; }
    public void setKnowledgeBaseVersionId(Long value) { this.knowledgeBaseVersionId = value; }
    public String getRejectReason() { return rejectReason; }
    public void setRejectReason(String rejectReason) { this.rejectReason = rejectReason; }
    public Long getRetrievalLogRef() { return retrievalLogRef; }
    public void setRetrievalLogRef(Long retrievalLogRef) { this.retrievalLogRef = retrievalLogRef; }
    public List<AiQaSource> getSources() { return sources; }
    public void setSources(List<AiQaSource> sources) { this.sources = sources; }
}
