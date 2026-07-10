package com.hezal.system.ai;

import com.hezal.system.domain.CourseDocumentVersion;
import com.hezal.system.domain.DocumentParseTask;

/**
 * AI文档解析内部客户端。
 *
 * @author trainmind
 */
public interface AiDocumentParseClient
{
    DocumentParseTask createTask(CourseDocumentVersion version);

    DocumentParseTask getTask(Long taskId);
}
