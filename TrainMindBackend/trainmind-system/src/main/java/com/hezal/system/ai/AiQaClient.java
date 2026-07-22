package com.hezal.system.ai;

import com.hezal.system.domain.dto.AiQaAnswer;
import com.hezal.system.domain.dto.AiQaRequest;

/** AI 课程问答内部客户端。 */
public interface AiQaClient
{
    AiQaAnswer answer(AiQaRequest request);
}
