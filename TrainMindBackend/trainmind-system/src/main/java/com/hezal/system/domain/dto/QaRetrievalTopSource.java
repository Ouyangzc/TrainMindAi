package com.hezal.system.domain.dto;

import java.math.BigDecimal;

/** AI 检索 Top 来源。 */
public class QaRetrievalTopSource
{
    private Long chunkId;
    private Long documentId;
    private Long documentVersionId;
    private String documentTitle;
    private String sourceFile;
    private Integer pageStart;
    private Integer pageEnd;
    private String sectionTitle;
    private BigDecimal score;
    private Integer rankNo;
    private Boolean usedInPrompt;
    private Boolean cited;

    public Long getChunkId() { return chunkId; }
    public void setChunkId(Long chunkId) { this.chunkId = chunkId; }
    public Long getDocumentId() { return documentId; }
    public void setDocumentId(Long documentId) { this.documentId = documentId; }
    public Long getDocumentVersionId() { return documentVersionId; }
    public void setDocumentVersionId(Long documentVersionId) { this.documentVersionId = documentVersionId; }
    public String getDocumentTitle() { return documentTitle; }
    public void setDocumentTitle(String documentTitle) { this.documentTitle = documentTitle; }
    public String getSourceFile() { return sourceFile; }
    public void setSourceFile(String sourceFile) { this.sourceFile = sourceFile; }
    public Integer getPageStart() { return pageStart; }
    public void setPageStart(Integer pageStart) { this.pageStart = pageStart; }
    public Integer getPageEnd() { return pageEnd; }
    public void setPageEnd(Integer pageEnd) { this.pageEnd = pageEnd; }
    public String getSectionTitle() { return sectionTitle; }
    public void setSectionTitle(String sectionTitle) { this.sectionTitle = sectionTitle; }
    public BigDecimal getScore() { return score; }
    public void setScore(BigDecimal score) { this.score = score; }
    public Integer getRankNo() { return rankNo; }
    public void setRankNo(Integer rankNo) { this.rankNo = rankNo; }
    public Boolean getUsedInPrompt() { return usedInPrompt; }
    public void setUsedInPrompt(Boolean usedInPrompt) { this.usedInPrompt = usedInPrompt; }
    public Boolean getCited() { return cited; }
    public void setCited(Boolean cited) { this.cited = cited; }
}
