package com.hezal.system.ai;

import java.io.IOException;
import com.hezal.system.domain.dto.AiQaStreamEvent;

/** AI问答流式事件处理器。 */
@FunctionalInterface
public interface AiQaStreamHandler
{
    void accept(AiQaStreamEvent event) throws IOException;
}
