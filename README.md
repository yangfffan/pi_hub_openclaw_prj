# 树莓派远程语音代理 - HUB 服务

本项目实现树莓派与 OpenClaw 的语音交互 HUB 服务。

## 系统架构

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   树莓派    │────▶│    HUB      │────▶│  OpenClaw   │
│  (语音IO)   │     │  (消息转发)  │     │   (LLM)     │
└─────────────┘     └─────────────┘     └─────────────┘
      ▲                   │
      │                   ▼
      │            ┌─────────────┐
      └────────────│   Redis    │
                   │  (消息队列) │
                   └─────────────┘
```

## 项目结构

```
pi_hub_openclaw_prj/
├── venv/                       # 共享虚拟环境
├── hub/                        # HUB 服务端
│   ├── main.py                # FastAPI 入口
│   ├── config.py              # 配置管理
│   ├── api.py                 # 消息 API
│   ├── redis_client.py        # Redis 客户端
│   ├── openclaw.py            # OpenClaw CLI 封装
│   ├── poller.py              # OpenClaw 轮询线程
│   ├── uploader.py            # 消息处理线程
│   ├── test/
│   │   └── test_hub.py       # 测试脚本
│   ├── config.yaml           # 配置文件
│   └── requirements.txt      # Python 依赖
│
├── pi/                        # 树莓派客户端
│   ├── main.py               # 主程序
│   ├── config.py             # 配置管理
│   ├── http_client.py        # HTTP 客户端
│   ├── recorder.py           # 录音模块
│   ├── player.py             # 播放模块
│   ├── tts.py                # 腾讯云 TTS
│   ├── asr.py                # 腾讯云 ASR
│   ├── assets/               # 本地音效文件
│   ├── test/
│   │   ├── test_pi.py       # 测试脚本
│   │   └── test_tts_asr.py  # TTS→ASR 往返测试
│   └── requirements.txt      # Python 依赖
│
├── test/
│   └── test_system.py        # 系统集成测试
│
└── doc/
    ├── 需求文档.md
    └── 技术方案.md
```

## 环境要求

### 服务器端 (HUB)

- Ubuntu 24.04
- Python 3.10+
- Redis
- OpenClaw (已安装并配置 API Key)
- 网络可访问 OpenClaw Gateway (localhost:18789)

### 树莓派端

- 树莓派 5
- Raspberry Pi OS
- USB 麦克风
- USB 音箱

## 安装步骤

### 1. 安装 Redis

```bash
sudo apt-get update
sudo apt-get install -y redis-server
sudo redis-server --daemonize yes
```

### 2. 安装依赖

```bash
# 创建共享虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装 HUB 依赖
pip install -r hub/requirements.txt

# 安装 Pi 依赖 (可选，服务器上不需要 pyaudio)
pip install requests pyyaml
```

### 3. 配置 HUB

编辑 `hub/config.yaml`:

```yaml
server:
  host: "0.0.0.0"
  port: 8443
  ssl:
    enabled: false  # 开发环境

openclaw:
  gateway_url: "http://localhost:18789"
  agent_id: "main"
  poll_interval: 1

redis:
  url: "redis://localhost:6379/0"

security:
  token: "your-secret-token"  # 修改为你的 token
```

### 4. 启动 HUB 服务

```bash
source venv/bin/activate
python3 hub/main.py
```

服务启动后监听 `http://0.0.0.0:8443`

### 5. 验证服务

```bash
# 健康检查
curl http://localhost:8443/health

# 输出: {"status":"ok","redis":"ok"}
```

## 测试

### 运行测试脚本

```bash
source venv/bin/activate

# HUB 测试
python3 hub/test/test_hub.py

# Pi 测试
python3 pi/test/test_pi.py

# TTS→ASR 往返测试
python3 pi/test/test_tts_asr.py

# 系统集成测试
python3 test/test_system.py
```

### 手动测试 API

```bash
TOKEN="your-secret-token"

# 1. 上传消息
curl -X POST http://localhost:8443/api/v1/upload \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"text": "你好", "device_id": "test_pi"}'

# 2. 等待 10-15 秒让 OpenClaw 处理

# 3. 轮询获取回复
curl "http://localhost:8443/api/v1/poll?device_id=test_pi" \
  -H "Authorization: Bearer $TOKEN"
```

### 测试完整流程 (Python)

```python
import requests
import time

TOKEN = "your-secret-token"
DEVICE_ID = "test_pi"

# 上传消息
resp = requests.post(
    "http://localhost:8443/api/v1/upload",
    headers={
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json"
    },
    json={
        "text": "你好，请介绍一下你自己",
        "device_id": DEVICE_ID
    }
)
print(f"上传: {resp.json()}")

# 等待处理
time.sleep(15)

# 轮询回复
resp = requests.get(
    f"http://localhost:8443/api/v1/poll?device_id={DEVICE_ID}",
    headers={"Authorization": f"Bearer {TOKEN}"}
)
print(f"回复: {resp.json()}")
```

## API 接口

### POST /api/v1/upload

上传文字消息

**请求头:**
```
Authorization: Bearer <token>
Content-Type: application/json
```

**请求体:**
```json
{
  "text": "消息内容",
  "device_id": "设备ID"
}
```

**响应:**
```json
{
  "success": true,
  "message_id": "msg_xxx"
}
```

### GET /api/v1/poll

轮询获取下发消息

**参数:**
- `device_id`: 设备ID

**请求头:**
```
Authorization: Bearer <token>
```

**响应:**
```json
{
  "messages": [
    {
      "id": "msg_xxx",
      "text": "回复内容",
      "timestamp": 1234567890
    }
  ]
}
```

### GET /health

健康检查

**响应:**
```json
{
  "status": "ok",
  "redis": "ok"
}
```

## 常见问题

### 1. OpenClaw API Key 无效

确保已在 OpenClaw 配置有效的 LLM API Key。测试:

```bash
openclaw agent --agent main -m "你好" --json
```

### 2. Redis 连接失败

```bash
# 启动 Redis
sudo redis-server --daemonize yes

# 测试连接
redis-cli ping
# 应输出: PONG
```

### 3. 端口被占用

```bash
# 查看端口占用
lsof -i :8443

# 杀死进程
kill <PID>
```

## 相关文档

- [需求文档](./doc/需求文档.md)
- [技术方案](./doc/技术方案.md)
