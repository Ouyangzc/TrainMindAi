package com.hezal.system.domain;

import java.util.Date;

import com.hezal.common.core.domain.BaseEntity;

/**
 * 文档解析任务。
 *
 * @author trainmind
 */
public class DocumentParseTask extends BaseEntity
{
    private static final long serialVersionUID = 1L;

    private Long id;
    private Long documentId;
    private Long documentVersionId;
    private String status;
    private String currentStep;
    private Integer progress;
    private String errorCode;
    private String errorMessage;
    private Integer retryCount;
    private Date startedAt;
    private Date finishedAt;

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }
    public Long getDocumentId() { return documentId; }
    public void setDocumentId(Long documentId) { this.documentId = documentId; }
    public Long getDocumentVersionId() { return documentVersionId; }
    public void setDocumentVersionId(Long documentVersionId) { this.documentVersionId = documentVersionId; }
    public String getStatus() { return status; }
    public void setStatus(String status) { this.status = status; }
    public String getCurrentStep() { return currentStep; }
    public void setCurrentStep(String currentStep) { this.currentStep = currentStep; }
    public Integer getProgress() { return progress; }
    public void setProgress(Integer progress) { this.progress = progress; }
    public String getErrorCode() { return errorCode; }
    public void setErrorCode(String errorCode) { this.errorCode = errorCode; }
    public String getErrorMessage() { return errorMessage; }
    public void setErrorMessage(String errorMessage) { this.errorMessage = errorMessage; }
    public Integer getRetryCount() { return retryCount; }
    public void setRetryCount(Integer retryCount) { this.retryCount = retryCount; }
    public Date getStartedAt() { return startedAt; }
    public void setStartedAt(Date startedAt) { this.startedAt = startedAt; }
    public Date getFinishedAt() { return finishedAt; }
    public void setFinishedAt(Date finishedAt) { this.finishedAt = finishedAt; }
}
