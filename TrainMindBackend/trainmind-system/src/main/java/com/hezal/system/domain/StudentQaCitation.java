package com.hezal.system.domain;

import java.math.BigDecimal;
import com.hezal.common.core.domain.BaseEntity;

/** AI 回答引用快照。 */
public class StudentQaCitation extends BaseEntity
{
    private static final long serialVersionUID = 1L;
    private Long id;
    private Long tenantId;
    private Long messageId;
    private Long chunkId;
    private Long documentId;
    private Long documentVersionId;
    private String documentTitle;
    private Integer versionNo;
    private String sourceFile;
    private Integer pageStart;
    private Integer pageEnd;
    private String sectionTitle;
    private String quote;
    private BigDecimal score;
    private Integer rankNo;

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }
    public Long getTenantId() { return tenantId; }
    public void setTenantId(Long tenantId) { this.tenantId = tenantId; }
    public Long getMessageId() { return messageId; }
    public void setMessageId(Long messageId) { this.messageId = messageId; }
    public Long getChunkId() { return chunkId; }
    public void setChunkId(Long chunkId) { this.chunkId = chunkId; }
    public Long getDocumentId() { return documentId; }
    public void setDocumentId(Long documentId) { this.documentId = documentId; }
    public Long getDocumentVersionId() { return documentVersionId; }
    public void setDocumentVersionId(Long value) { this.documentVersionId = value; }
    public String getDocumentTitle() { return documentTitle; }
    public void setDocumentTitle(String documentTitle) { this.documentTitle = documentTitle; }
    public Integer getVersionNo() { return versionNo; }
    public void setVersionNo(Integer versionNo) { this.versionNo = versionNo; }
    public String getSourceFile() { return sourceFile; }
    public void setSourceFile(String sourceFile) { this.sourceFile = sourceFile; }
    public Integer getPageStart() { return pageStart; }
    public void setPageStart(Integer pageStart) { this.pageStart = pageStart; }
    public Integer getPageEnd() { return pageEnd; }
    public void setPageEnd(Integer pageEnd) { this.pageEnd = pageEnd; }
    public String getSectionTitle() { return sectionTitle; }
    public void setSectionTitle(String sectionTitle) { this.sectionTitle = sectionTitle; }
    public String getQuote() { return quote; }
    public void setQuote(String quote) { this.quote = quote; }
    public BigDecimal getScore() { return score; }
    public void setScore(BigDecimal score) { this.score = score; }
    public Integer getRankNo() { return rankNo; }
    public void setRankNo(Integer rankNo) { this.rankNo = rankNo; }
}
