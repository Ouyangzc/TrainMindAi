"""聚合 internal/v1 路由。

业务端点统一挂在 /internal/v1 下并要求 X-Internal-Token；
health 单独挂载、无需鉴权。
"""

from fastapi import APIRouter, Depends

from app.api.internal.v1 import (
    documents,
    eval,
    health,
    kb_tasks,
    kb_versions,
    qa,
    questions,
)
from app.core.security import verify_internal_token

# 健康检查：无鉴权
health_router = APIRouter()
health_router.include_router(health.router)

# 业务内部 API：要求 X-Internal-Token
internal_router = APIRouter(
    prefix="/internal/v1",
    dependencies=[Depends(verify_internal_token)],
)
for _m in (documents, kb_versions, kb_tasks, qa, questions, eval):
    internal_router.include_router(_m.router)
