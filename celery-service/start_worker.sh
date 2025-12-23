#!/bin/bash
# 启动 Celery Worker

echo "🚀 启动 Celery Worker..."

# 激活后端虚拟环境并设置路径
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"
BACKEND_DIR="$SCRIPT_DIR/../backend"
VENV_ACTIVATE="$BACKEND_DIR/venv/bin/activate"
if [ -f "$VENV_ACTIVATE" ]; then
  source "$VENV_ACTIVATE"
  echo "🐍 已激活后端虚拟环境: $VENV_ACTIVATE"
else
  echo "❌ 未找到后端虚拟环境: $VENV_ACTIVATE"
  echo "请在 $BACKEND_DIR 创建 venv 并安装依赖: python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
  exit 1
fi

# 设置Python路径
export PYTHONPATH="$SCRIPT_DIR:$BACKEND_DIR:$PYTHONPATH"

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
