"""检索日志 / 模型调用日志仓储。"""

from app.models.logs import ModelCallLog, QaRetrievalLog
from app.repositories.base import BaseRepository


class QaRetrievalLogRepo(BaseRepository[QaRetrievalLog]):
    def __init__(self, session):  # noqa: ANN001
        super().__init__(session, QaRetrievalLog)

    async def bulk_create(self, logs: list[QaRetrievalLog]) -> list[QaRetrievalLog]:
        return await self.add_all(logs)


class ModelCallLogRepo(BaseRepository[ModelCallLog]):
    def __init__(self, session):  # noqa: ANN001
        super().__init__(session, ModelCallLog)

    async def log_call(
        self,
        *,
        scenario: str | None = None,
        provider: str | None = None,
        model: str | None = None,
        message_id: int | None = None,
        request_id: str | None = None,
        prompt_tokens: int | None = None,
        completion_tokens: int | None = None,
        total_tokens: int | None = None,
        latency_ms: int | None = None,
        success: bool = True,
        error_code: str | None = None,
        error_message: str | None = None,
    ) -> ModelCallLog:
        log = ModelCallLog(
            scenario=scenario,
            provider=provider,
            model=model,
            message_id=message_id,
            request_id=request_id,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            latency_ms=latency_ms,
            success=success,
            error_code=error_code,
            error_message=error_message,
        )
        return await self.add(log)
