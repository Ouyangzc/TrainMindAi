package com.hezal.system.domain.dto;

import java.util.ArrayList;
import java.util.List;

/** 保存知识库草稿资料快照请求。 */
public class KnowledgeBaseSnapshotRequest
{
    private List<Long> documentVersionIds = new ArrayList<>();

    public List<Long> getDocumentVersionIds()
    {
        return documentVersionIds;
    }

    public void setDocumentVersionIds(List<Long> documentVersionIds)
    {
        this.documentVersionIds = documentVersionIds;
    }
}
