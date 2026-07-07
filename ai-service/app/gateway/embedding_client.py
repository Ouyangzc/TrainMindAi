"""Embedding 网关客户端（OpenAI 兼容）。

支持批量 embedding，内部处理分片（OpenAI 上限 ~2048 条/请求）。
"""

from openai import AsyncOpenAI

from app.core.config import settings

_BATCH_SIZE = 128


class EmbeddingClient:
    def __init__(self) -> None:
        self._client = AsyncOpenAI(
            base_url=settings.embedding_base_url or None,
            api_key=settings.embedding_api_key or "not-set",
        )
        self.model = settings.embedding_model
        self.dim = settings.embedding_dim

    async def embed(self, texts: list[str]) -> list[list[float]]:
        """文本列表 -> 向量列表。自动按 _BATCH_SIZE 分片。"""
        if not texts:
            return []

        all_embeddings: list[list[float]] = []
        for i in range(0, len(texts), _BATCH_SIZE):
            batch = texts[i : i + _BATCH_SIZE]
            response = await self._client.embeddings.create(
                model=self.model, input=batch
            )
            batch_embeddings = [item.embedding for item in response.data]
            all_embeddings.extend(batch_embeddings)
        return all_embeddings
