# TrainMindAi AI 服务（FastAPI）

企业级知识助教系统的 Python AI 服务，负责文档解析、Chunk、Embedding、混合检索、RAG 问答、出题/诊断/评分、RAG 评估。作为**内网服务**由 RuoYi（Spring Boot）业务后端调用，权限由业务后端负责。

设计文档：
- `../docs/AI服务技术设计（FastAPI）.md`
- `../docs/AI服务表结构设计（ai-schema）.md`

> 当前为**脚手架 + 数据库迁移**阶段：core 基础设施、分层目录、抽象接口与 stub 路由已就位，`ai` schema 的 16 张表可通过 Alembic 建出。解析/检索/RAG 等业务逻辑尚未实现（services 为占位）。

## 环境要求

- Python 3.12，[uv](https://docs.astral.sh/uv/)
- PostgreSQL（与 RuoYi 共享实例）+ **pgvector 扩展**
- Redis、MinIO（运行业务时需要；启动 API 本身不强依赖）

## 快速开始

```bash
cd ai-service
cp .env.example .env          # 按需修改连接串与网关地址
uv sync                       # 安装依赖

# 启动 API
uv run uvicorn app.main:app --reload --port 8000
# 健康检查： GET http://localhost:8000/health/live
# 接口文档： http://localhost:8000/docs

# 启动 Worker（轮询 kb_build_task）
uv run python -m app.workers.worker
```

## 数据库迁移（Alembic）

```bash
# 离线生成 DDL（无需活库，便于评审）
uv run alembic upgrade head --sql

# 对活库执行（需 PostgreSQL 可用且已装 pgvector）
uv run alembic upgrade head
uv run alembic downgrade base   # 回滚
```

迁移只管理 `ai` schema；业务表（`public`）由 RuoYi 管理，AI 表通过松耦合普通列（无跨 schema 外键）引用。

## 质量检查

```bash
uv run pytest
uv run ruff check .
uv run mypy app
```
