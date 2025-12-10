# AIOT 外部插件服务

简洁的IoT设备控制API，专为外部插件（如Coze、GPT、Claude等AI助手）设计。

## ✨ 特点

- **🎯 简单易用**：只需设备UUID，参数极少
- **🔓 无需认证**：不需要token，降低使用门槛
- **📦 统一响应**：标准化的JSON响应格式
- **🚀 高性能**：基于FastAPI异步框架
- **📖 自动文档**：内置Swagger UI和OpenAPI规范

---

## 🚀 快速开始

### 1. 安装依赖

```bash
cd plugin-service
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
# 复制环境变量模板
cp env.example .env

# 编辑配置文件
vim .env  # 或使用你喜欢的编辑器
```

**重要配置项**：
- `BACKEND_URL` - 后端API服务地址（默认：http://localhost:8000）
- `BACKEND_API_KEY` - 后端内部API密钥（必须与后端的 `INTERNAL_API_KEY` 保持一致）

### 3. 启动服务

```bash
python main.py
```

服务将在 `http://localhost:9000` 启动

### 3. 访问文档

- **Swagger UI**: http://localhost:9000/docs
- **ReDoc**: http://localhost:9000/redoc
- **OpenAPI JSON**: http://localhost:9000/openapi.json

---

## 📖 API接口说明

### 基础信息

- **基础URL**: `http://localhost:9000`
- **响应格式**: JSON
- **认证方式**: 无需认证，仅需设备UUID

### 标准响应格式

```json
{
  "code": 200,
  "msg": "响应消息",
  "data": {
    // 响应数据
  }
}
```

---

## 🌡️ 1. 获取传感器数据

获取指定设备的传感器数据（温度、湿度等）

### 接口

```
GET /plugin/sensor-data
```

### 参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| uuid | string | 是 | 设备UUID |
| sensor | string | 是 | 传感器名称 |

### 支持的传感器

- `温度` / `temperature` - DHT11温度传感器
- `湿度` / `humidity` - DHT11湿度传感器
- `DS18B20` / `DS18B20温度` - DS18B20温度传感器

### 示例

**请求：**
```bash
curl "http://localhost:9000/plugin/sensor-data?uuid=df13f23c-71c9-46ab-8eb1-715f3127fce2&sensor=温度"
```

**响应：**
```json
{
  "code": 200,
  "msg": "获取传感器数据成功",
  "data": {
    "device_uuid": "df13f23c-71c9-46ab-8eb1-715f3127fce2",
    "sensor_name": "DHT11温度",
    "value": 24.5,
    "unit": "°C",
    "timestamp": "2025-11-11T07:30:00Z"
  }
}
```

---

## 🎮 2. 控制设备端口

控制设备的LED、继电器、舵机、PWM等端口

### 接口

```
POST /plugin/control
```

### 请求体

```json
{
  "device_uuid": "设备UUID",
  "port_type": "端口类型",
  "port_id": 端口ID,
  "action": "动作",
  "value": 设置值（可选）
}
```

### 参数说明

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| device_uuid | string | 是 | 设备UUID |
| port_type | string | 是 | 端口类型：led/relay/servo/pwm |
| port_id | integer | 是 | 端口ID（1-4） |
| action | string | 是 | 动作：on/off/set |
| value | integer | 否 | 设置值（舵机角度/PWM占空比等） |

### 支持的端口类型

#### LED灯 (`led`)
- **端口ID**: 1-4
- **动作**: `on`（打开）、`off`（关闭）

#### 继电器 (`relay`)
- **端口ID**: 1-2
- **动作**: `on`（打开）、`off`（关闭）

#### 舵机 (`servo`)
- **端口ID**: 1
- **动作**: `set`（设置角度）
- **value**: 0-180（角度值）

#### PWM输出 (`pwm`)
- **端口ID**: 2
- **动作**: `set`（设置占空比）
- **value**: 0-100（占空比百分比）

### 示例

#### 打开LED

**请求：**
```bash
curl -X POST "http://localhost:9000/plugin/control" \
  -H "Content-Type: application/json" \
  -d '{
    "device_uuid": "df13f23c-71c9-46ab-8eb1-715f3127fce2",
    "port_type": "led",
    "port_id": 1,
    "action": "on"
  }'
```

**响应：**
```json
{
  "code": 200,
  "msg": "控制命令发送成功",
  "data": {
    "device_uuid": "df13f23c-71c9-46ab-8eb1-715f3127fce2",
    "port_type": "led",
    "port_id": 1,
    "action": "on",
    "value": null,
    "result": "success"
  }
}
```

#### 设置舵机角度

**请求：**
```bash
curl -X POST "http://localhost:9000/plugin/control" \
  -H "Content-Type: application/json" \
  -d '{
    "device_uuid": "df13f23c-71c9-46ab-8eb1-715f3127fce2",
    "port_type": "servo",
    "port_id": 1,
    "action": "set",
    "value": 90
  }'
```

---

## 🎯 3. 执行预设指令

执行预定义的设备控制序列

### 接口

```
POST /plugin/preset
```

### 请求体

```json
{
  "device_uuid": "设备UUID",
  "preset_name": "预设名称",
  "parameters": {
    // 预设参数（可选）
  }
}
```

### 支持的预设指令

#### LED预设

##### `led_blink` - LED闪烁

**参数：**
- `led_id`: LED编号（1-4），默认1
- `count`: 闪烁次数，默认3
- `on_time`: 亮灯时间（ms），默认500
- `off_time`: 灭灯时间（ms），默认500

**示例：**
```json
{
  "device_uuid": "df13f23c-71c9-46ab-8eb1-715f3127fce2",
  "preset_name": "led_blink",
  "parameters": {
    "led_id": 1,
    "count": 5,
    "on_time": 500,
    "off_time": 500
  }
}
```

##### `led_wave` - LED流水灯

**参数：**
- `interval_ms`: 间隔时间（ms），默认200
- `cycles`: 循环次数，默认3
- `reverse`: 是否反向，默认false

**示例：**
```json
{
  "device_uuid": "df13f23c-71c9-46ab-8eb1-715f3127fce2",
  "preset_name": "led_wave",
  "parameters": {
    "interval_ms": 200,
    "cycles": 3,
    "reverse": false
  }
}
```

#### 继电器预设

##### `relay_timed` - 继电器定时开关

**参数：**
- `relay_id`: 继电器编号（1-2），默认1
- `duration_ms`: 持续时间（ms），默认5000

**示例：**
```json
{
  "device_uuid": "df13f23c-71c9-46ab-8eb1-715f3127fce2",
  "preset_name": "relay_timed",
  "parameters": {
    "relay_id": 1,
    "duration_ms": 5000
  }
}
```

#### 舵机预设

##### `servo_rotate` - 舵机旋转

**参数：**
- `servo_id`: 舵机编号（1），默认1
- `start_angle`: 起始角度（0-180），默认0
- `end_angle`: 结束角度（0-180），默认180
- `duration_ms`: 持续时间（ms），默认2000

**示例：**
```json
{
  "device_uuid": "df13f23c-71c9-46ab-8eb1-715f3127fce2",
  "preset_name": "servo_rotate",
  "parameters": {
    "servo_id": 1,
    "start_angle": 0,
    "end_angle": 180,
    "duration_ms": 2000
  }
}
```

##### `servo_swing` - 舵机摆动（摇尾巴效果）

**参数：**
- `servo_id`: 舵机编号（1），默认1
- `center_angle`: 中心角度（0-180），默认90
- `swing_range`: 摆动幅度（度），默认30
- `speed`: 摆动速度（ms），默认100
- `cycles`: 摆动次数，默认5

**示例：**
```json
{
  "device_uuid": "df13f23c-71c9-46ab-8eb1-715f3127fce2",
  "preset_name": "servo_swing",
  "parameters": {
    "servo_id": 1,
    "center_angle": 90,
    "swing_range": 30,
    "speed": 100,
    "cycles": 5
  }
}
```

#### PWM预设

##### `pwm_fade` - PWM渐变

**参数：**
- `pwm_id`: PWM通道（2），默认2
- `start_duty`: 起始占空比（0-100），默认0
- `end_duty`: 结束占空比（0-100），默认100
- `duration_ms`: 持续时间（ms），默认2000
- `frequency`: PWM频率（Hz），默认5000

##### `pwm_breathe` - PWM呼吸灯

**参数：**
- `pwm_id`: PWM通道（2），默认2
- `min_duty`: 最小占空比（0-100），默认0
- `max_duty`: 最大占空比（0-100），默认100
- `period_ms`: 呼吸周期（ms），默认2000
- `cycles`: 循环次数，默认3
- `frequency`: PWM频率（Hz），默认5000

##### `pwm_pulse` - PWM脉冲

**参数：**
- `pwm_id`: PWM通道（2），默认2
- `duty_high`: 高电平占空比（0-100），默认100
- `duty_low`: 低电平占空比（0-100），默认0
- `high_time_ms`: 高电平时间（ms），默认100
- `low_time_ms`: 低电平时间（ms），默认100
- `cycles`: 脉冲次数，默认5
- `frequency`: PWM频率（Hz），默认5000

---

## 🔧 配置说明

### 后端服务地址

在 `main.py` 中修改后端服务地址：

```python
BACKEND_URL = "http://localhost:8000"
```

### 端口配置

默认端口：`9000`

修改启动端口：

```python
uvicorn.run(
    "main:app",
    host="0.0.0.0",
    port=9000,  # 修改此处
    reload=True
)
```

---

## 🌐 集成到外部平台

### Coze（扣子）平台

1. 登录 [Coze平台](https://www.coze.cn/)
2. 创建或编辑Bot
3. 点击"添加插件" → "API插件"
4. 选择"导入OpenAPI Schema"
5. 上传 `openapi.json` 文件
6. 配置服务器URL（如需公网访问，使用ngrok或frp）
7. 保存并测试

### GPT Actions

1. 在GPT配置中添加Action
2. 导入 `openapi.json`
3. 配置Authentication为"None"
4. 保存并测试

### Claude MCP

参考Claude的Model Context Protocol文档进行集成。

---

## 🔒 安全建议

⚠️ **重要**：此服务设计为内部使用或受信任的外部插件调用。

### 生产环境安全措施

如需在生产环境使用，建议：

1. **添加认证机制**
   ```python
   from fastapi import Header, HTTPException
   
   async def verify_api_key(x_api_key: str = Header(...)):
       if x_api_key != "your-secret-key":
           raise HTTPException(status_code=401, detail="Invalid API Key")
   ```

2. **限制访问IP**
   - 使用防火墙或Nginx配置白名单
   - 只允许特定IP访问

3. **使用HTTPS**
   - 部署时配置SSL证书
   - 使用反向代理（Nginx/Caddy）

4. **速率限制**
   - 使用slowapi或类似工具限制请求频率
   - 防止滥用

---

## 🚀 部署指南

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
  --bind 0.0.0.0:9000 \
  --access-logfile - \
  --error-logfile -
```

#### 方法二：使用 Docker

创建 `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 9000

CMD ["python", "main.py"]
```

构建并运行：

```bash
# 构建镜像
docker build -t aiot-plugin-service .

# 运行容器
docker run -d \
  --name plugin-service \
  -p 9000:9000 \
  --env-file .env \
  aiot-plugin-service
```

#### 方法三：使用 systemd（Linux）

创建 `/etc/systemd/system/aiot-plugin.service`:

```ini
[Unit]
Description=AIOT Plugin Service
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/plugin-service
Environment="PATH=/path/to/venv/bin"
ExecStart=/path/to/venv/bin/gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:9000
Restart=always

[Install]
WantedBy=multi-user.target
```

启动服务：

```bash
sudo systemctl daemon-reload
sudo systemctl enable aiot-plugin
sudo systemctl start aiot-plugin
```

### 环境变量配置

创建 `.env` 文件：

```bash
# 服务配置
PORT=9000
HOST=0.0.0.0
LOG_LEVEL=INFO

# 后端服务配置（重要）
BACKEND_URL=http://localhost:8000
BACKEND_API_KEY=your-internal-api-key

# CORS配置
CORS_ENABLED=true
CORS_ORIGINS=*
```

**重要**：`BACKEND_API_KEY` 必须与后端服务的 `INTERNAL_API_KEY` 保持一致。

### 健康检查

```bash
# 检查服务状态
curl http://localhost:9000/health

# 查看API文档
curl http://localhost:9000/docs
```

---

## 📝 错误码说明

| 错误码 | 说明 |
|--------|------|
| 200 | 成功 |
| 400 | 请求参数错误 |
| 404 | 设备或资源不存在 |
| 500 | 服务器内部错误 |

---

## 🧪 测试示例

### 使用curl测试

```bash
# 1. 获取温度数据
curl "http://localhost:9000/plugin/sensor-data?uuid=df13f23c-71c9-46ab-8eb1-715f3127fce2&sensor=温度"

# 2. 打开LED
curl -X POST "http://localhost:9000/plugin/control" \
  -H "Content-Type: application/json" \
  -d '{"device_uuid":"df13f23c-71c9-46ab-8eb1-715f3127fce2","port_type":"led","port_id":1,"action":"on"}'

# 3. LED闪烁
curl -X POST "http://localhost:9000/plugin/preset" \
  -H "Content-Type: application/json" \
  -d '{"device_uuid":"df13f23c-71c9-46ab-8eb1-715f3127fce2","preset_name":"led_blink","parameters":{"led_id":1,"count":3}}'
```

### 使用Python测试

```python
import requests

BASE_URL = "http://localhost:9000"
DEVICE_UUID = "df13f23c-71c9-46ab-8eb1-715f3127fce2"

# 获取温度
response = requests.get(
    f"{BASE_URL}/plugin/sensor-data",
    params={"uuid": DEVICE_UUID, "sensor": "温度"}
)
print(response.json())

# 控制LED
response = requests.post(
    f"{BASE_URL}/plugin/control",
    json={
        "device_uuid": DEVICE_UUID,
        "port_type": "led",
        "port_id": 1,
        "action": "on"
    }
)
print(response.json())

# 执行预设
response = requests.post(
    f"{BASE_URL}/plugin/preset",
    json={
        "device_uuid": DEVICE_UUID,
        "preset_name": "led_blink",
        "parameters": {"led_id": 1, "count": 5}
    }
)
print(response.json())
```

---

## 📚 相关文档

- **主项目**: [AIOT-Admin-Server](../)
- **固件文档**: [../firmware/aiot-esp32/README.md](../firmware/aiot-esp32/README.md)
- **后端API**: [../backend/README.md](../backend/README.md)
- **FastAPI文档**: https://fastapi.tiangolo.com/

---

## 🆘 常见问题

### Q: 设备UUID在哪里获取？

A: 在主系统的前端页面 → 设备列表中查看，或通过后端API `/api/devices` 获取。

### Q: 如何添加新的预设指令？

A: 在 `main.py` 的 `preset_map` 字典中添加新的预设配置。

### Q: 服务无法连接到后端？

A: 检查 `BACKEND_URL` 配置是否正确，确保后端服务（默认8000端口）正在运行。

### Q: 如何允许外网访问？

A: 使用 ngrok、frp 或配置公网服务器的反向代理（Nginx）。

---

## 📄 License

MIT License

---

## 👥 贡献

欢迎提交Issue和Pull Request！

---

**🎉 享受简洁的IoT控制体验！**

