"""stub 工具：尚未实现的端点统一返回 501。"""

from fastapi import HTTPException, status


def not_implemented(feature: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail=f"{feature} 尚未实现（脚手架阶段）",
    )
