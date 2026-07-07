---
name: fastapi-ai-service-decisions
description: Locked architecture decisions for the missing Python FastAPI AI service in TrainMindAi
metadata:
  type: project
---

TrainMindAi = 企业级知识助教系统. Three pieces: RuoYi-Vue (Spring Boot 3.5/Java 17 业务后端, PostgreSQL `ruoyi`@5432, Redis@6379 db0, port 8080, JWT-HS512 secret `abcdefghijklmnopqrstuvwxyz` + Redis `login_tokens:{uuid}` 存 LoginUser), RuoYi-Vue3 (前端), and a **Python FastAPI AI service to be built**. Design doc: `docs/AI服务技术设计（FastAPI）.md` (companion to `docs/企业级知识助教系统落地方案.md`).

Confirmed decisions (2026-06-17):
1. **拓扑**: Java 单网关(BFF) + FastAPI 内网. 权限只在 Java; FastAPI 信任 `X-Internal-Token` + Java 传入的已解析上下文(user_id/course_ids/kb_version_id). SSE 由 Java 透传.
2. **DB**: 同实例同库 `ruoyi` + 独立 schema `ai` + pgvector 扩展. Alembic 只管 ai schema. AI 流水线表(chunk/index/检索日志/eval)归 FastAPI 写, 业务表归 Java.
3. **向量库**: MVP pgvector, 用 `VectorStore` 抽象接口留 Qdrant 后路.
4. **模型**: OpenAI 兼容网关. Embedding=bge-m3 (dim 1024), LLM=云 API. `EMBEDDING_BASE_URL` 与 `LLM_BASE_URL` 分离(便于 bge 先私有化). 换 embedding 模型必登记 `embedding_index_version`.
5. **Worker**: `kb_build_task` 数据库轮询(FOR UPDATE SKIP LOCKED) + 同镜像独立进程. Redis 仅缓存/信号. 后期升级 arq/RabbitMQ.

中文检索坑: PG 默认不分中文词, 用 jieba 预分词写 tsvector. 阶段对齐落地方案 §17 阶段1 MVP. See [[trainmindai-project]].
