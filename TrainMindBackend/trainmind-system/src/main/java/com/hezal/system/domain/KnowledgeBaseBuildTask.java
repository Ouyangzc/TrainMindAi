package com.hezal.system.domain;

import com.hezal.common.core.domain.BaseEntity;

/** AI知识库构建任务。 */
public class KnowledgeBaseBuildTask extends BaseEntity
{
    private static final long serialVersionUID = 1L;
    private Long id;
    private String taskType;
    private String status;
    private String currentStep;
    private Integer progress;
    private String errorCode;
    private String errorMessage;
    private Integer retryCount;

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }
    public String getTaskType() { return taskType; }
    public void setTaskType(String taskType) { this.taskType = taskType; }
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
}
