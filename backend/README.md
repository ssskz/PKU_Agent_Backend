# 后端服务

基于 FastAPI 的物联网设备管理后端服务。

## 技术栈

- **FastAPI** - Web 框架
- **SQLAlchemy** - ORM
- **MySQL** - 数据库
- **MQTT** - 消息队列

## 快速开始

### 1. 安装依赖

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. 配置环境

```bash
cp .env.example .env
# 编辑 .env 文件，配置数据库、MQTT 等
```

### 3. 初始化数据库

使用 SQL 脚本手动导入数据库结构和初始数据。请参考 `../SQL/` 目录。

### 4. 启动服务

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 5. 访问文档

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 项目结构

```
backend/
├── app/
│   ├── api/          # API 路由
│   ├── core/         # 核心配置
│   ├── models/       # 数据模型
│   ├── schemas/      # Pydantic 模式
│   ├── services/     # 业务逻辑
│   └── utils/        # 工具函数
├── main.py           # 应用入口
└── requirements.txt  # Python 依赖
```

## 环境变量

主要配置项：

- `DATABASE_URL` - MySQL 数据库连接
- `SERVER_BASE_URL` - 服务器基础URL（用于生成固件下载链接）
- `SECRET_KEY` - JWT 密钥（至少32字符）
- `MQTT_BROKER_HOST` - MQTT 服务器地址
- `MQTT_USERNAME` / `MQTT_PASSWORD` - MQTT 认证

详细配置请参考 `.env.example`。

## API 文档

启动服务后访问：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

主要 API 端点：
- `/api/auth/*` - 认证相关
- `/api/devices/*` - 设备管理（使用 UUID）
- `/api/products/*` - 产品管理
- `/api/users/*` - 用户管理
- `/api/firmware/*` - 固件管理
- `/api/dashboard/*` - 仪表盘

## 部署

### 开发环境

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 生产环境

#### 方法一：使用 Gunicorn

```bash
# 安装 Gunicorn
pip install gunicorn

# 启动服务
gunicorn main:app \
  -w 4 \
  -k uvicorn.workers.UvicornWorker \
  -b 0.0.0.0:8000 \
  --access-logfile - \
  --error-logfile -
```

#### 方法二：使用 Docker

```bash
# 构建镜像
docker build -t aiot-backend .

# 运行容器
docker run -d \
  --name aiot-backend \
  -p 8000:8000 \
  --env-file .env \
  aiot-backend
```

#### 方法三：使用 systemd（Linux）

创建 `/etc/systemd/system/aiot-backend.service`:

```ini
[Unit]
Description=AIOT Backend Service
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/backend
Environment="PATH=/path/to/venv/bin"
ExecStart=/path/to/venv/bin/gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
Restart=always

[Install]
WantedBy=multi-user.target
```

启动服务：

```bash
sudo systemctl daemon-reload
sudo systemctl enable aiot-backend
sudo systemctl start aiot-backend
```

### 环境变量配置

生产环境需要配置以下环境变量：

```bash
# 数据库
DATABASE_URL=mysql+pymysql://user:password@host:3306/database

# 服务器地址（重要：用于生成固件下载链接）
SERVER_BASE_URL=https://your-domain.com

# JWT密钥（必须至少32字符）
SECRET_KEY=your-very-long-secret-key-at-least-32-characters

# MQTT配置
MQTT_BROKER_HOST=mqtt.example.com
MQTT_USERNAME=mqtt_user
MQTT_PASSWORD=mqtt_password
```

### 健康检查

```bash
# 检查服务状态
curl http://localhost:8000/health

# 检查API文档
curl http://localhost:8000/docs
```
