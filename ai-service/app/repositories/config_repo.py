"""配置表仓储：ChunkStrategy / RetrievalStrategyConfig / PromptTemplate。"""

from sqlalchemy import select

from app.models.config_tables import (
    ChunkStrategy,
    PromptTemplate,
    RetrievalStrategyConfig,
)
from app.repositories.base import BaseRepository


class ChunkStrategyRepo(BaseRepository[ChunkStrategy]):
    def __init__(self, session):  # noqa: ANN001
        super().__init__(session, ChunkStrategy)

    async def get_enabled(self) -> list[ChunkStrategy]:
        stmt = (
            select(ChunkStrategy)
            .where(ChunkStrategy.enabled.is_(True))
            .order_by(ChunkStrategy.strategy_code, ChunkStrategy.strategy_version)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())


class RetrievalStrategyConfigRepo(BaseRepository[RetrievalStrategyConfig]):
    def __init__(self, session):  # noqa: ANN001
        super().__init__(session, RetrievalStrategyConfig)

    async def get_enabled(self) -> list[RetrievalStrategyConfig]:
        stmt = (
            select(RetrievalStrategyConfig)
            .where(RetrievalStrategyConfig.enabled.is_(True))
            .order_by(
                RetrievalStrategyConfig.strategy_code,
                RetrievalStrategyConfig.strategy_version,
            )
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_default(self) -> RetrievalStrategyConfig | None:
        """按 id 升序取第一个启用的策略，作为默认。"""
        stmt = (
            select(RetrievalStrategyConfig)
            .where(RetrievalStrategyConfig.enabled.is_(True))
            .order_by(RetrievalStrategyConfig.id)
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()


class PromptTemplateRepo(BaseRepository[PromptTemplate]):
    def __init__(self, session):  # noqa: ANN001
        super().__init__(session, PromptTemplate)

    async def get_by_scenario(
        self, scenario: str, enabled: bool = True
    ) -> list[PromptTemplate]:
        stmt = (
            select(PromptTemplate)
            .where(
                PromptTemplate.scenario == scenario,
                PromptTemplate.enabled.is_(enabled),
            )
            .order_by(PromptTemplate.prompt_code, PromptTemplate.prompt_version)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
