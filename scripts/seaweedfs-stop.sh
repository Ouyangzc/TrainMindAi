#!/usr/bin/env bash
set -euo pipefail

# 停止本地 SeaweedFS 开发服务。
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PID_FILE="$ROOT_DIR/.tools/seaweedfs.pid"

if [[ ! -f "$PID_FILE" ]]; then
  echo "未找到 SeaweedFS PID 文件，服务可能未启动"
  exit 0
fi

PID="$(cat "$PID_FILE")"
if kill -0 "$PID" 2>/dev/null; then
  kill "$PID"
  echo "已停止 SeaweedFS，PID=$PID"
else
  echo "PID=$PID 不存在，清理 PID 文件"
fi

rm -f "$PID_FILE"
