package com.hezal.system.ai;

import com.hezal.system.domain.KnowledgeBaseBuildTask;

/** AI知识库构建内部客户端。 */
public interface AiKnowledgeBaseClient
{
    KnowledgeBaseBuildTask createBuildTask(Long knowledgeBaseVersionId);
    KnowledgeBaseBuildTask getBuildTask(Long taskId);
}
