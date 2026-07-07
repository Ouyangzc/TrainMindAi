"""内部鉴权：校验来自 RuoYi 业务后端的 X-Internal-Token。

AI 服务不做用户级 RBAC（权限在 Java 侧），这里只确认调用方是受信的业务后端。
"""

import hmac

from fastapi import Header, HTTPException, status

from app.core.config import settings


async def verify_internal_token(
    x_internal_token: str = Header(default="", alias="X-Internal-Token"),
) -> None:
    """FastAPI 依赖：常数时间比较 X-Internal-Token。"""
    expected = settings.internal_token
    if not expected or not hmac.compare_digest(x_internal_token, expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid internal token",
        )
