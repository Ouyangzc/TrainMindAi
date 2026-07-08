#!/usr/bin/env bash

# 项目本地 Linux 工具链。
# 在当前工作区运行后端、前端或 ai-service 验证命令前，先 source 本文件。
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

export JAVA_HOME="$ROOT_DIR/.tools/jdk-17"
export MAVEN_HOME="$ROOT_DIR/.tools/maven"
export COREPACK_HOME="$ROOT_DIR/.tools/corepack"
export PATH="$ROOT_DIR/.tools/bin:$MAVEN_HOME/bin:$ROOT_DIR/.tools/node/bin:$JAVA_HOME/bin:$PATH"

yarn() {
  corepack yarn "$@"
}
