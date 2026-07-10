#!/usr/bin/env bash
set -euo pipefail

# 本地 SeaweedFS 开发服务启动脚本。
# 二进制和数据目录位于 .tools/，该目录已被 .gitignore 忽略。
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WEED_BIN="$ROOT_DIR/.tools/seaweedfs/weed"
DATA_DIR="$ROOT_DIR/.tools/seaweedfs-data"
LOG_DIR="$ROOT_DIR/.tools/logs"
PID_FILE="$ROOT_DIR/.tools/seaweedfs.pid"
LOG_FILE="$LOG_DIR/seaweedfs.log"

if [[ ! -x "$WEED_BIN" ]]; then
  echo "未找到 SeaweedFS 二进制：$WEED_BIN" >&2
  echo "请先下载并解压 SeaweedFS 到 .tools/seaweedfs/weed" >&2
  exit 1
fi

if [[ -f "$PID_FILE" ]] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
  echo "SeaweedFS 已在运行，PID=$(cat "$PID_FILE")"
  exit 0
fi

mkdir -p "$DATA_DIR" "$LOG_DIR"

AWS_ACCESS_KEY_ID="${SEAWEEDFS_ACCESS_KEY:-trainmind}" \
AWS_SECRET_ACCESS_KEY="${SEAWEEDFS_SECRET_KEY:-trainmind-secret}" \
S3_BUCKET="${SEAWEEDFS_BUCKET:-trainmind-docs}" \
setsid "$WEED_BIN" mini \
  -dir="$DATA_DIR" \
  -ip=127.0.0.1 \
  -ip.bind=127.0.0.1 \
  -master.port=9333 \
  -volume.port=9340 \
  -filer.port=8888 \
  -s3.port=8333 \
  -s3.port.iceberg=0 \
  -webdav=false \
  -admin.password="${SEAWEEDFS_ADMIN_PASSWORD:-trainmind-admin}" \
  >"$LOG_FILE" 2>&1 < /dev/null &

echo "$!" > "$PID_FILE"
echo "SeaweedFS 已启动，PID=$(cat "$PID_FILE")"
echo "S3 Endpoint: http://localhost:8333"
echo "Filer UI:    http://localhost:8888"
echo "Master UI:   http://localhost:9333"
echo "Admin UI:    http://localhost:23646"
echo "日志文件:    $LOG_FILE"
