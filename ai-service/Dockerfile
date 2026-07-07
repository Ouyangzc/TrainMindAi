# TrainMindAi AI 服务镜像。API 与 Worker 共用此镜像，靠 command 区分。
FROM python:3.12-slim

# uv：单二进制包管理
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

WORKDIR /app

# 先装依赖（利用层缓存）
COPY pyproject.toml uv.lock* ./
RUN uv sync --no-install-project --no-dev || uv sync --no-dev

# 再拷源码
COPY . .

EXPOSE 8000

# 默认起 API；Worker 用：command: ["uv","run","python","-m","app.workers.worker"]
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
