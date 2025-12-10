# 设备配置服务 (Device Provisioning Service)

独立的轻量级服务，为物联网设备提供启动配置信息。

## 🎯 功能概述

### 1. 设备配置获取 `/device/info`
设备启动后通过MAC地址一次性获取所有配置：
- **设备凭证**: UUID、Device ID、Device Secret
- **MQTT配置**: 服务器地址、端口、主题等
- **API配置**: 后端服务器地址、接口端点
- **固件更新**: 检查是否有新版本

### 2. 固件更新检查 `/firmware/check`
设备可定期检查是否有新固件版本

### 3. 健康检查 `/health`
用于监控服务状态

## 📋 工作流程

```
┌─────────────┐
│  ESP32设备  │
└──────┬──────┘
       │ 1. WiFi配置
       │    用户输入: http://provision.example.com
       ↓
┌──────────────────────────────────────┐
│  配网页面保存服务器地址到NVS           │
│  地址: http://provision.example.com   │
└──────┬───────────────────────────────┘
       │ 2. 重启后读取地址
       ↓
┌──────────────────────────────────────┐
│  ESP32: 拼接完整URL                   │
│  POST http://provision.example.com/device/info │
│  Body: { "mac_address": "AA:BB:CC:DD:EE:FF" }  │
└──────┬───────────────────────────────┘
       │ 3. 获取配置响应
       ↓
┌──────────────────────────────────────┐
│  Provisioning Service 返回:          │
│  {                                   │
│    "device_uuid": "xxx",             │
│    "device_secret": "xxx",           │
│    "mqtt_config": {                  │
│      "broker": "mqtt.example.com",   │
│      "port": 1883,                   │
│      "topics": { ... }               │
│    },                                │
│    "api_config": { ... },            │
│    "firmware_update": { ... }        │
│  }                                   │
└──────┬───────────────────────────────┘
       │ 4. 使用配置连接MQTT
       ↓
┌──────────────────────────────────────┐
│  ESP32连接到MQTT服务器                │
│  订阅控制主题，发布数据                │
└──────────────────────────────────────┘
```

## 🚀 快速开始

### 1. 安装依赖

```bash
cd provisioning-service
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
# 复制环境变量模板
cp env.example .env

# 编辑配置
vim .env
```

**关键配置**:
```bash
# 数据库（使用主系统数据库）
PROVISIONING_DB_URL=mysql+pymysql://root:password@localhost:3306/aiot_device

# MQTT服务器（设备连接到这里）
MQTT_BROKER=demo.aiot.hello1023.com
MQTT_PORT=1883

# 主API服务器
API_SERVER=http://demo.aiot.hello1023.com

# 服务端口
PORT=8001
```

### 3. 启动服务

```bash
# 开发模式
python main.py

# 生产模式
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8001
```

### 4. 验证服务

```bash
# 健康检查
curl http://localhost:8001/health

# 测试设备配置获取
curl -X POST http://localhost:8001/device/info \
  -H "Content-Type: application/json" \
  -d '{
    "mac_address": "AA:BB:CC:DD:EE:FF",
    "firmware_version": "1.0.0"
  }'
```

## 📡 API文档

### 1. 获取设备配置

**端点**: `POST /device/info`

**请求**:
```json
{
  "mac_address": "AA:BB:CC:DD:EE:FF",
  "firmware_version": "1.0.0",
  "hardware_version": "ESP32-S3"
}
```

**响应**:
```json
{
  "device_id": "AIOT-ESP32-12345678",
  "device_uuid": "550e8400-e29b-41d4-a716-446655440000",
  "device_secret": "abc123def456...",
  "mac_address": "AA:BB:CC:DD:EE:FF",
  "mqtt_config": {
    "broker": "mqtt.example.com",
    "port": 1883,
    "use_ssl": false,
    "url": "mqtt://mqtt.example.com:1883",
    "username": "AIOT-ESP32-12345678",
    "password": "abc123def456...",
    "client_id": "550e8400-e29b-41d4-a716-446655440000",
    "topics": {
      "data": "devices/550e8400-e29b-41d4-a716-446655440000/data",
      "control": "devices/550e8400-e29b-41d4-a716-446655440000/control",
      "status": "devices/550e8400-e29b-41d4-a716-446655440000/status"
    }
  },
  "api_config": {
    "server": "http://api.example.com",
    "endpoints": {
      "register": "http://api.example.com/api/devices/register",
      "data_upload": "http://api.example.com/api/devices/data/upload",
      "status_update": "http://api.example.com/api/devices/status/update"
    }
  },
  "firmware_update": {
    "available": true,
    "version": "1.1.0",
    "download_url": "http://ota.example.com/firmware/1.1.0.bin",
    "file_size": 1048576,
    "checksum": "sha256:abc123...",
    "changelog": "修复了一些bug"
  },
  "message": "设备配置获取成功",
  "timestamp": "2025-11-06T10:30:00.123456"
}
```

### 2. 检查固件更新

**端点**: `POST /firmware/check`

**请求**:
```json
{
  "mac_address": "AA:BB:CC:DD:EE:FF",
  "current_version": "1.0.0",
  "product_id": 1
}
```

**响应**:
```json
{
  "update_available": true,
  "current_version": "1.0.0",
  "latest_version": "1.1.0",
  "download_url": "http://ota.example.com/firmware/1.1.0.bin",
  "file_size": 1048576,
  "checksum": "sha256:abc123...",
  "changelog": "修复了一些bug",
  "message": "有新版本可用"
}
```

### 3. 健康检查

**端点**: `GET /health`

**响应**:
```json
{
  "status": "healthy",
  "timestamp": "2025-11-06T10:30:00.123456",
  "version": "1.0.0"
}
```

## 🛡️ 安全特性

### 1. 速率限制
- **IP级别**: 每个IP每分钟最多10次请求
- **MAC级别**: 每个MAC地址有独立的限制
- **自动清理**: 定期清理过期记录

### 2. 防止时序攻击
- 查询成功和失败的响应时间一致（最小100ms）
- 攻击者无法通过响应时间判断MAC是否存在

### 3. 访问日志
- 记录所有请求（IP、MAC、时间、结果）
- 便于审计和异常检测

### 4. 设备状态管理
- 支持设备禁用功能
- 记录设备最后访问时间

## 🔧 部署指南

### 开发环境

```bash
python main.py
```

### 生产环境

#### 方法一：使用 Gunicorn（推荐）

```bash
# 安装 Gunicorn
pip install gunicorn

# 启动服务
gunicorn main:app \
  -w 4 \
  -k uvicorn.workers.UvicornWorker \
  -b 0.0.0.0:8001 \
  --access-logfile - \
  --error-logfile -
```

#### 方法二：使用 systemd（Linux）

创建 `/etc/systemd/system/aiot-provisioning.service`:

```ini
[Unit]
Description=AIOT Device Provisioning Service
After=network.target mysql.service

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/provisioning-service
Environment="PATH=/path/to/venv/bin"
EnvironmentFile=/path/to/provisioning-service/.env
ExecStart=/path/to/venv/bin/gunicorn main:app \
    -w 4 \
    -k uvicorn.workers.UvicornWorker \
    -b 0.0.0.0:8001
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

启动服务:

```bash
sudo systemctl daemon-reload
sudo systemctl enable aiot-provisioning
sudo systemctl start aiot-provisioning
```

#### 方法三：使用 Docker

创建 `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8001

CMD ["gunicorn", "main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:8001"]
```

构建和运行:

```bash
# 构建镜像
docker build -t aiot-provisioning .

# 运行容器
docker run -d \
  --name aiot-provisioning \
  -p 8001:8001 \
  --env-file .env \
  aiot-provisioning
```

#### 方法四：Nginx 反向代理

```nginx
server {
    listen 80;
    server_name provision.example.com;

    location / {
        proxy_pass http://127.0.0.1:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        proxy_connect_timeout 10s;
        proxy_send_timeout 10s;
        proxy_read_timeout 10s;
    }
}
```

### 环境变量配置

关键配置项：

```bash
# 数据库（使用主系统数据库）
PROVISIONING_DB_URL=mysql+pymysql://user:password@host:3306/database

# MQTT服务器（设备连接到这里）
MQTT_BROKER=mqtt.example.com
MQTT_PORT=1883
MQTT_USE_SSL=false

# 主API服务器
API_SERVER=http://api.example.com
OTA_SERVER=http://api.example.com

# 服务端口
PORT=8001

# 速率限制
RATE_LIMIT_REQUESTS=10
RATE_LIMIT_WINDOW=60
```

### 健康检查

```bash
# 检查服务状态
curl http://localhost:8001/health

# 测试设备配置获取
curl -X POST http://localhost:8001/device/info \
  -H "Content-Type: application/json" \
  -d '{"mac_address": "AA:BB:CC:DD:EE:FF"}'
```

## 📊 监控和日志

### 查看日志

```bash
# Systemd服务日志
sudo journalctl -u aiot-provisioning -f

# 应用日志
tail -f /var/log/aiot-provisioning/app.log
```

### 监控指标

建议监控以下指标：
- 请求速率（QPS）
- 响应时间
- 错误率（404、429、500）
- 设备查询成功率
- 速率限制触发次数

### 告警建议

```
- QPS突然增加 > 1000 → 可能受到攻击
- 404错误率 > 50% → MAC枚举攻击
- 429错误增加 → 速率限制触发频繁
- 响应时间 > 1s → 性能问题
```

## 🔍 故障排查

### 问题1: 设备无法获取配置

**检查**:
1. 设备MAC地址是否已在数据库注册
2. 服务是否正常运行 `curl http://localhost:8001/health`
3. 网络连接是否正常
4. 查看服务日志是否有错误

### 问题2: 速率限制过于严格

**解决**:
调整 `.env` 中的配置:
```bash
RATE_LIMIT_REQUESTS=20  # 增加限制
RATE_LIMIT_WINDOW=60
```

### 问题3: 数据库连接失败

**检查**:
1. 数据库服务是否运行
2. 数据库连接字符串是否正确
3. 数据库用户权限是否足够
4. 防火墙是否允许连接

## 💡 最佳实践

### 1. 数据库

- **共享数据库**: 与主系统共用数据库，但使用只读账号（提升安全性）
- **连接池**: 已配置自动连接池管理
- **定期备份**: 虽然只读，但建议定期备份主数据库

### 2. 性能优化

- **缓存**: 可添加Redis缓存热点设备配置
- **负载均衡**: 部署多个实例，使用Nginx负载均衡
- **CDN**: 固件下载URL可以使用CDN加速

### 3. 安全加固

- **HTTPS**: 生产环境必须使用HTTPS
- **防火墙**: 只开放必要端口
- **IP白名单**: 如果设备IP范围固定，可配置白名单
- **监控告警**: 接入监控系统，及时发现异常

### 4. 高可用

- **多实例部署**: 至少2个实例
- **健康检查**: 配置负载均衡器健康检查
- **自动重启**: 使用Systemd自动重启失败的服务
- **数据备份**: 定期备份数据库

## 📝 更新日志

### v1.0.0 (2025-11-06)

- ✅ 初始版本
- ✅ 设备配置获取接口
- ✅ 固件更新检查接口
- ✅ 速率限制功能
- ✅ 访问日志记录
- ✅ 健康检查接口

## 🤝 贡献

欢迎提交Issue和Pull Request！

## 📄 许可证

MIT License

---

**维护者**: AIOT团队  
**联系方式**: support@aiot.example.com

