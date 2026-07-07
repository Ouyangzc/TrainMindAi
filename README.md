# TrainMindAi

TrainMindAi 是一个 monorepo，包含 Python AI 服务、Java 业务后台和 Vue 前端三个可独立启动的子项目。

## 项目结构

```text
TrainMindAi/
  ai-service/          # Python FastAPI AI 服务
  TrainMindBackend/    # Java Spring Boot 业务后台
  TrainMindFront/      # Vue3 TypeScript 前端
  docs/                # 方案与设计文档
  memory/              # 项目过程资料
```

## 启动入口

### Python AI 服务

```bash
cd ai-service
cp .env.example .env
uv sync
uv run uvicorn app.main:app --reload --port 8000
```

### Java 业务后台

```bash
cd TrainMindBackend
mvn clean package
```

后台具体运行方式以 `TrainMindBackend/README.md` 和本地配置为准。

### Vue3 前端

```bash
cd TrainMindFront
yarn
yarn dev
```

## 说明

- 根目录 Git 仓库用于统一管理三个子项目源码。
- 各子项目依赖、构建产物和本地环境文件不提交到仓库。
- 原子项目 README 保留在各自目录内。
