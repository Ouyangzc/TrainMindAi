package com.hezal.system.domain.dto;

import java.math.BigDecimal;

/** 课程 AI 问答观测聚合指标。 */
public class QaObservationSummary
{
    private Long questionCount;
    private Long insufficientEvidenceCount;
    private Long noValidCitationCount;
    private Long weakCitationCount;
    private Long fallbackCount;
    private BigDecimal insufficientEvidenceRate;
    private BigDecimal noValidCitationRate;
    private BigDecimal weakCitationRate;
    private BigDecimal fallbackRate;
    private Integer p95TotalLatencyMs;

    public Long getQuestionCount() { return questionCount; }
    public void setQuestionCount(Long questionCount) { this.questionCount = questionCount; }
    public Long getInsufficientEvidenceCount() { return insufficientEvidenceCount; }
    public void setInsufficientEvidenceCount(Long value) { this.insufficientEvidenceCount = value; }
    public Long getNoValidCitationCount() { return noValidCitationCount; }
    public void setNoValidCitationCount(Long value) { this.noValidCitationCount = value; }
    public Long getWeakCitationCount() { return weakCitationCount; }
    public void setWeakCitationCount(Long weakCitationCount) { this.weakCitationCount = weakCitationCount; }
    public Long getFallbackCount() { return fallbackCount; }
    public void setFallbackCount(Long fallbackCount) { this.fallbackCount = fallbackCount; }
    public BigDecimal getInsufficientEvidenceRate() { return insufficientEvidenceRate; }
    public void setInsufficientEvidenceRate(BigDecimal value) { this.insufficientEvidenceRate = value; }
    public BigDecimal getNoValidCitationRate() { return noValidCitationRate; }
    public void setNoValidCitationRate(BigDecimal value) { this.noValidCitationRate = value; }
    public BigDecimal getWeakCitationRate() { return weakCitationRate; }
    public void setWeakCitationRate(BigDecimal weakCitationRate) { this.weakCitationRate = weakCitationRate; }
    public BigDecimal getFallbackRate() { return fallbackRate; }
    public void setFallbackRate(BigDecimal fallbackRate) { this.fallbackRate = fallbackRate; }
    public Integer getP95TotalLatencyMs() { return p95TotalLatencyMs; }
    public void setP95TotalLatencyMs(Integer p95TotalLatencyMs) { this.p95TotalLatencyMs = p95TotalLatencyMs; }
}
