# AIOT 插件后端服务

专门为外部插件提供设备操作服务，直接访问数据库和MQTT，不依赖主backend服务。

## 架构设计

```
外部LLM/插件
    ↓
plugin-service (端口9000) - 接收外部请求
    ↓
plugin-backend-service (端口9001) - 处理设备操作
    ↓
数据库 + MQTT - 直接访问资源
```

## 功能特性

- ✅ 直接访问数据库读取传感器数据
- ✅ 直接通过MQTT控制设备
- ✅ 独立运行，避免与主backend服务冲突
- ✅ 高性能，无需HTTP中转
- ✅ 简化架构，避免循环依赖

## 安装部署

### 1. 安装依赖

```bash
cd plugin-backend-service
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
cp .env.example .env
nano .env
```

配置以下内容：
```env
# 数据库连接（两种方式任选其一）

# 方式1：使用单独的配置项（推荐）
DB_HOST=localhost
DB_PORT=3306
DB_NAME=aiot
DB_USER=aiot_user
DB_PASSWORD=your_password

# 方式2：使用完整的连接字符串
# DATABASE_URL=mysql+pymysql://aiot_user:your_password@localhost:3306/aiot

# MQTT连接
MQTT_BROKER=localhost
MQTT_PORT=1883

# MQTT认证（可选，留空表示匿名访问）
MQTT_USERNAME=
MQTT_PASSWORD=

# 如果需要认证，填写用户名密码：
# MQTT_USERNAME=your_username
# MQTT_PASSWORD=your_password
```

### 3. 启动服务

```bash
# 开发模式
python main.py

# 生产模式
uvicorn main:app --host 0.0.0.0 --port 9001 --workers 2
```

### 4. systemd 服务（推荐）

创建 `/etc/systemd/system/plugin-backend.service`:

```ini
[Unit]
Description=AIOT Plugin Backend Service
After=network.target mysql.service

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/plugin-backend-service
Environment="PATH=/path/to/venv/bin"
EnvironmentFile=/path/to/plugin-backend-service/.env
ExecStart=/path/to/venv/bin/python main.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

启动服务：
```bash
sudo systemctl daemon-reload
sudo systemctl enable plugin-backend
sudo systemctl start plugin-backend
sudo systemctl status plugin-backend
```

## API接口

### 1. 健康检查
```http
GET /health
```

### 2. 获取传感器数据
```http
GET /api/sensor-data?device_uuid={uuid}&sensor={sensor_name}
```

### 3. 控制设备
```http
POST /api/control
Content-Type: application/json

{
  "device_uuid": "xxx",
  "port_type": "led",
  "port_id": 1,
  "action": "on"
}
```

## 测试

```bash
# 健康检查
curl http://localhost:9001/health

# 查询传感器
curl "http://localhost:9001/api/sensor-data?device_uuid=xxx&sensor=温度"

# 控制设备
curl -X POST http://localhost:9001/api/control \
  -H "Content-Type: application/json" \
  -d '{"device_uuid":"xxx","port_type":"led","port_id":1,"action":"on"}'
```

## 日志

查看日志：
```bash
# systemd 服务
sudo journalctl -u plugin-backend -f

# 或查看标准输出
tail -f /var/log/plugin-backend.log
```

## 故障排除

### 数据库连接失败
- 检查数据库配置（DB_HOST、DB_PORT、DB_USER、DB_PASSWORD、DB_NAME）
- 确保数据库服务运行：`sudo systemctl status mysql`
- 验证用户名密码：`mysql -h localhost -u aiot_user -p aiot`
- 检查数据库是否存在：`SHOW DATABASES;`

### MQTT连接失败
- 检查 MQTT_BROKER 地址
- 确保MQTT服务运行：`sudo systemctl status mosquitto`
- 测试连接：`mosquitto_sub -h localhost -t test`
- 如果MQTT需要认证，填写 MQTT_USERNAME 和 MQTT_PASSWORD
- 如果MQTT允许匿名访问，留空 MQTT_USERNAME 和 MQTT_PASSWORD

### 端口占用
```bash
# 检查端口
netstat -tlnp | grep 9001

# 修改 .env 中的 SERVICE_PORT
```

