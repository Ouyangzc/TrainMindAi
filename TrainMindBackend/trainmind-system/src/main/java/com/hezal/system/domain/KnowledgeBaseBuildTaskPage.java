package com.hezal.system.domain;

import java.io.Serializable;
import java.util.Collections;
import java.util.List;

/** AI知识库构建任务分页结果。 */
public class KnowledgeBaseBuildTaskPage implements Serializable
{
    private static final long serialVersionUID = 1L;

    private List<KnowledgeBaseBuildTask> rows = Collections.emptyList();
    private Long total = 0L;
    private Integer page = 1;
    private Integer pageSize = 20;

    public List<KnowledgeBaseBuildTask> getRows() { return rows; }
    public void setRows(List<KnowledgeBaseBuildTask> rows) { this.rows = rows; }
    public Long getTotal() { return total; }
    public void setTotal(Long total) { this.total = total; }
    public Integer getPage() { return page; }
    public void setPage(Integer page) { this.page = page; }
    public Integer getPageSize() { return pageSize; }
    public void setPageSize(Integer pageSize) { this.pageSize = pageSize; }
}
