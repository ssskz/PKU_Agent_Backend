#!/bin/bash
# 启动 Celery Worker

echo "🚀 启动 Celery Worker..."

# 设置Python路径
export PYTHONPATH="$PWD:$PWD/../backend:$PYTHONPATH"

# 创建日志目录
mkdir -p logs

# 启动Worker（使用 solo pool，适合本地开发环境，Python 3.12+ 兼容）
celery -A celery_app worker \
  --loglevel=info \
  --pool=solo \
  --concurrency=1 \
  --max-tasks-per-child=50 \
  --logfile=logs/celery_worker.log

echo "✅ Celery Worker 已启动"
