"""RAG 离线评估仓储。"""

from datetime import UTC, datetime

from sqlalchemy import select

from app.models.eval import RagEvalCase, RagEvalDataset, RagEvalResult, RagEvalRun
from app.repositories.base import BaseRepository


class RagEvalDatasetRepo(BaseRepository[RagEvalDataset]):
    def __init__(self, session):  # noqa: ANN001
        super().__init__(session, RagEvalDataset)


class RagEvalCaseRepo(BaseRepository[RagEvalCase]):
    def __init__(self, session):  # noqa: ANN001
        super().__init__(session, RagEvalCase)

    async def list_by_dataset(self, dataset_id: int) -> list[RagEvalCase]:
        stmt = (
            select(RagEvalCase)
            .where(
                RagEvalCase.dataset_id == dataset_id,
                RagEvalCase.status == "active",
            )
            .order_by(RagEvalCase.id)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())


class RagEvalRunRepo(BaseRepository[RagEvalRun]):
    def __init__(self, session):  # noqa: ANN001
        super().__init__(session, RagEvalRun)

    async def mark_completed(self, run: RagEvalRun) -> None:
        run.status = "completed"
        run.finished_at = datetime.now(UTC)
        await self.session.flush()

    async def mark_failed(self, run: RagEvalRun) -> None:
        run.status = "failed"
        run.finished_at = datetime.now(UTC)
        await self.session.flush()


class RagEvalResultRepo(BaseRepository[RagEvalResult]):
    def __init__(self, session):  # noqa: ANN001
        super().__init__(session, RagEvalResult)

    async def bulk_create(
        self, results: list[RagEvalResult]
    ) -> list[RagEvalResult]:
        return await self.add_all(results)
