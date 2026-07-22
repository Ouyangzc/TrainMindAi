package com.hezal.system.domain.dto;

import java.math.BigDecimal;
import com.fasterxml.jackson.annotation.JsonProperty;

/** AI 服务返回的结构化引用。 */
public class AiQaSource
{
    @JsonProperty("chunk_id")
    private Long chunkId;
    @JsonProperty("document_id")
    private Long documentId;
    @JsonProperty("document_version_id")
    private Long documentVersionId;
    @JsonProperty("source_file")
    private String sourceFile;
    @JsonProperty("page_start")
    private Integer pageStart;
    @JsonProperty("page_end")
    private Integer pageEnd;
    @JsonProperty("section_title")
    private String sectionTitle;
    private BigDecimal score;

    public Long getChunkId() { return chunkId; }
    public void setChunkId(Long chunkId) { this.chunkId = chunkId; }
    public Long getDocumentId() { return documentId; }
    public void setDocumentId(Long documentId) { this.documentId = documentId; }
    public Long getDocumentVersionId() { return documentVersionId; }
    public void setDocumentVersionId(Long value) { this.documentVersionId = value; }
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
}
