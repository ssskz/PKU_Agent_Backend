#!/bin/bash
# ============================================================
# Plugin Backend Service 快速部署脚本
# ============================================================

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}============================================================${NC}"
echo -e "${BLUE}  Plugin Backend Service 部署脚本${NC}"
echo -e "${BLUE}============================================================${NC}"

# 检查是否为 root 用户
check_root() {
    if [ "$EUID" -eq 0 ]; then
        echo -e "${YELLOW}⚠️  警告：不建议使用 root 用户运行此脚本${NC}"
        read -p "是否继续？(y/N) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
}

# 检查 Python 版本
check_python() {
    echo -e "${BLUE}🔍 检查 Python 版本...${NC}"
    
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}❌ 未找到 python3${NC}"
        echo -e "${YELLOW}请先安装 Python 3.9+${NC}"
        exit 1
    fi
    
    PYTHON_VERSION=$(python3 --version | awk '{print $2}')
    echo -e "${GREEN}✅ Python 版本: $PYTHON_VERSION${NC}"
}

# 检查依赖
check_dependencies() {
    echo -e "${BLUE}🔍 检查系统依赖...${NC}"
    
    DEPS_MISSING=0
    
    # 检查 gcc
    if ! command -v gcc &> /dev/null; then
        echo -e "${YELLOW}⚠️  gcc 未安装${NC}"
        DEPS_MISSING=1
    fi
    
    # 检查 MySQL 开发库
    if ! pkg-config --exists mysqlclient 2>/dev/null; then
        echo -e "${YELLOW}⚠️  MySQL 开发库未安装${NC}"
        DEPS_MISSING=1
    fi
    
    if [ $DEPS_MISSING -eq 1 ]; then
        echo -e "${YELLOW}请安装缺少的依赖：${NC}"
        echo -e "${YELLOW}  Ubuntu/Debian: sudo apt install gcc default-libmysqlclient-dev pkg-config${NC}"
        echo -e "${YELLOW}  CentOS/RHEL: sudo yum install gcc mysql-devel${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ 系统依赖检查完成${NC}"
}

# 创建虚拟环境
create_venv() {
    echo -e "${BLUE}📦 创建虚拟环境...${NC}"
    
    if [ -d "venv" ]; then
        echo -e "${YELLOW}⚠️  虚拟环境已存在，跳过创建${NC}"
    else
        python3 -m venv venv
        echo -e "${GREEN}✅ 虚拟环境创建成功${NC}"
    fi
}

# 安装 Python 依赖
install_requirements() {
    echo -e "${BLUE}📦 安装 Python 依赖...${NC}"
    
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    
    echo -e "${GREEN}✅ 依赖安装完成${NC}"
}

# 配置环境变量
configure_env() {
    echo -e "${BLUE}⚙️  配置环境变量...${NC}"
    
    if [ -f ".env" ]; then
        echo -e "${YELLOW}⚠️  .env 文件已存在${NC}"
        read -p "是否覆盖？(y/N) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo -e "${BLUE}跳过配置，使用现有 .env 文件${NC}"
            return
        fi
    fi
    
    cp env.example .env
    echo -e "${GREEN}✅ .env 文件创建成功${NC}"
    echo -e "${YELLOW}📝 请编辑 .env 文件配置数据库和MQTT连接信息${NC}"
    echo -e "${YELLOW}   nano .env${NC}"
}

# 测试数据库连接
test_database() {
    echo -e "${BLUE}🔍 测试数据库连接...${NC}"
    
    source venv/bin/activate
    
    python3 << EOF
import os
from dotenv import load_dotenv

load_dotenv()

# 读取配置
db_url = os.getenv("DATABASE_URL")
if not db_url:
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = os.getenv("DB_PORT", "3306")
    db_name = os.getenv("DB_NAME", "aiot")
    db_user = os.getenv("DB_USER", "aiot_user")
    db_password = os.getenv("DB_PASSWORD", "password")
    db_url = f"mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

try:
    from sqlalchemy import create_engine
    engine = create_engine(db_url)
    with engine.connect() as conn:
        print("✅ 数据库连接成功")
        exit(0)
except Exception as e:
    print(f"❌ 数据库连接失败: {e}")
    exit(1)
EOF
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ 数据库连接测试通过${NC}"
    else
        echo -e "${RED}❌ 数据库连接测试失败${NC}"
        echo -e "${YELLOW}请检查 .env 文件中的数据库配置${NC}"
        exit 1
    fi
}

# 启动服务
start_service() {
    echo -e "${BLUE}🚀 启动服务...${NC}"
    
    source venv/bin/activate
    
    echo -e "${GREEN}服务启动中...${NC}"
    echo -e "${YELLOW}按 Ctrl+C 停止服务${NC}"
    echo
    
    python main.py
}

# 后台运行服务
background_run() {
    echo -e "${BLUE}📋 配置后台运行...${NC}"
    
    echo -e "${GREEN}✅ 使用以下命令后台运行服务：${NC}"
    echo
    echo -e "${YELLOW}方式1: 使用 nohup${NC}"
    echo -e "  ${GREEN}nohup python main.py > plugin-backend.log 2>&1 &${NC}"
    echo -e "  查看日志: ${GREEN}tail -f plugin-backend.log${NC}"
    echo -e "  停止服务: ${GREEN}pkill -f 'python main.py'${NC}"
    echo
    echo -e "${YELLOW}方式2: 使用 screen${NC}"
    echo -e "  ${GREEN}screen -S plugin-backend${NC}"
    echo -e "  ${GREEN}python main.py${NC}"
    echo -e "  按 Ctrl+A 然后 D 退出screen"
    echo -e "  重新连接: ${GREEN}screen -r plugin-backend${NC}"
}

# 显示帮助
show_help() {
    echo "用法: $0 [命令]"
    echo
    echo "命令:"
    echo "  setup              - 完整安装（创建venv、安装依赖、配置env）"
    echo "  install            - 仅安装依赖"
    echo "  config             - 仅配置环境变量"
    echo "  test-db            - 测试数据库连接"
    echo "  start              - 启动服务（前台运行）"
    echo "  background         - 显示后台运行方法"
    echo "  help               - 显示此帮助信息"
    echo
    echo "示例:"
    echo "  $0 setup           # 首次部署"
    echo "  $0 start           # 启动服务"
    echo "  $0 background      # 查看后台运行方法"
}

# 主流程
main() {
    case "${1:-help}" in
        setup)
            check_root
            check_python
            check_dependencies
            create_venv
            install_requirements
            configure_env
            echo -e "${GREEN}✅ 安装完成！${NC}"
            echo -e "${YELLOW}下一步：${NC}"
            echo -e "  1. 编辑配置文件: ${GREEN}nano .env${NC}"
            echo -e "  2. 测试数据库连接: ${GREEN}$0 test-db${NC}"
            echo -e "  3. 启动服务: ${GREEN}$0 start${NC}"
            ;;
        install)
            check_python
            check_dependencies
            create_venv
            install_requirements
            ;;
        config)
            configure_env
            ;;
        test-db)
            test_database
            ;;
        start)
            start_service
            ;;
        background)
            background_run
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            echo -e "${RED}❌ 未知命令: $1${NC}"
            show_help
            exit 1
            ;;
    esac
}

main "$@"

