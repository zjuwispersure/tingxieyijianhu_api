#!/bin/bash

# 用法: ./build_and_push.sh [dev|prod]
# 默认 prod

set -e

REGISTRY=registry.cn-hangzhou.aliyuncs.com/mini_program/tingxie
ENV=${1:-prod}
TAG=$ENV-$(date +%Y%m%d%H%M%S)
LATEST_TAG=latest

if [ "$ENV" = "dev" ]; then
  GUNICORN_RELOAD="--reload"
else
  GUNICORN_RELOAD=""
fi

echo "[INFO] 构建镜像: $REGISTRY:$TAG (环境: $ENV)"
docker build --build-arg GUNICORN_RELOAD="$GUNICORN_RELOAD" -t $REGISTRY:$TAG .

echo "[INFO] 标记 latest tag: $REGISTRY:$LATEST_TAG"
docker tag $REGISTRY:$TAG $REGISTRY:$LATEST_TAG

echo "[INFO] 登录阿里云镜像仓库"
docker login $REGISTRY

echo "[INFO] 推送镜像: $REGISTRY:$TAG"
docker push $REGISTRY:$TAG

echo "[INFO] 推送 latest 镜像: $REGISTRY:$LATEST_TAG"
docker push $REGISTRY:$LATEST_TAG

echo "[SUCCESS] 镜像已推送: $REGISTRY:$TAG 和 $REGISTRY:$LATEST_TAG"
