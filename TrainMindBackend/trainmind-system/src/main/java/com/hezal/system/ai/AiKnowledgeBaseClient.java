package com.hezal.system.ai;

import com.hezal.system.domain.KnowledgeBaseBuildTask;
import com.hezal.system.domain.KnowledgeBaseBuildTaskPage;

/** AI知识库构建内部客户端。 */
public interface AiKnowledgeBaseClient
{
    KnowledgeBaseBuildTask createBuildTask(Long knowledgeBaseVersionId);
    KnowledgeBaseBuildTask getBuildTask(Long taskId);
    KnowledgeBaseBuildTaskPage listBuildTasks(Long knowledgeBaseVersionId, int page, int size);
}
