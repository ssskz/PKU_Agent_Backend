#!/bin/bash
# 启动 Flower 监控面板

set -e  # 遇到错误立即退出

echo "🌸 启动 Flower 监控面板..."

# 获取当前脚本所在目录（适配本地和Docker环境）
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 设置Python路径（本地开发环境）
export PYTHONPATH="$SCRIPT_DIR:$SCRIPT_DIR/../backend:${PYTHONPATH:-}"

# 检查celery_app模块是否存在
if ! python -c "import celery_app" 2>/dev/null; then
    echo "❌ 错误: 无法导入 celery_app 模块"
    echo "当前目录: $(pwd)"
    echo "PYTHONPATH: $PYTHONPATH"
    ls -la
    exit 1
fi

# 启动Flower（celery_app已经配置了broker，不需要手动指定）
echo "🚀 正在启动 Flower..."
echo "   端口: ${FLOWER_PORT:-5555}"
echo "   认证: ${FLOWER_BASIC_AUTH:-admin:admin}"
exec celery -A celery_app flower \
  --port=${FLOWER_PORT:-5555} \
  --basic_auth=${FLOWER_BASIC_AUTH:-admin:admin}
