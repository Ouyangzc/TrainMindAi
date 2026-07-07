"""LLM 网关客户端（OpenAI 兼容）。

所有调用记录 model_call_log 由 services 层负责，本层仅做 API 通信。
"""

from collections.abc import AsyncIterator

from openai import AsyncOpenAI

from app.core.config import settings

_DEFAULT_TIMEOUT = 60.0


class LlmClient:
    def __init__(self) -> None:
        self._client = AsyncOpenAI(
            base_url=settings.llm_base_url or None,
            api_key=settings.llm_api_key or "not-set",
            timeout=_DEFAULT_TIMEOUT,
        )
        self.model = settings.llm_model

    async def chat(
        self,
        messages: list[dict],
        *,
        temperature: float = 0.7,
        max_tokens: int | None = None,
    ) -> str:
        """同步 LLM 调用，返回完整文本。"""
        response = await self._client.chat.completions.create(
            model=self.model,
            messages=messages,  # type: ignore[arg-type]
            temperature=temperature,
            max_tokens=max_tokens,
        )
        content = response.choices[0].message.content or ""
        return content

    async def chat_stream(
        self,
        messages: list[dict],
        *,
        temperature: float = 0.7,
        max_tokens: int | None = None,
    ) -> AsyncIterator[str]:
        """流式 LLM 调用，逐 token 产出。"""
        stream = await self._client.chat.completions.create(
            model=self.model,
            messages=messages,  # type: ignore[arg-type]
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
        )
        async for chunk in stream:  # type: ignore[union-attr]
            delta = chunk.choices[0].delta if chunk.choices else None
            if delta and delta.content:
                yield delta.content
