# Hub 服务

本目录包含服务器端 HUB 服务的代码。

## 目录结构

```
hub/
├── main.py              # FastAPI 应用入口
├── config.py            # 配置管理
├── api.py               # 消息 API
├── redis_client.py      # Redis 客户端
├── openclaw.py          # OpenClaw CLI 封装
├── poller.py            # OpenClaw 轮询线程
├── uploader.py          # 消息处理线程
├── test/
│   └── test_hub.py     # Hub 测试脚本
├── config.yaml          # 配置文件
└── requirements.txt     # Python 依赖
```

## 安装

```bash
# 在项目根目录创建虚拟环境
cd /path/to/pi_hub_openclaw_prj

# 如果没有 uv，执行：
# curl -LsSf https://astral.sh/uv/install.sh | sh

uv venv
source .venv/bin/activate

# 安装依赖
uv pip install -r hub/requirements.txt
```

## 配置

编辑 `config.yaml`:

```yaml
server:
  host: "0.0.0.0"
  port: 8443
  ssl:
    enabled: false

openclaw:
  gateway_url: "http://localhost:18789"
  agent_id: "main"
  poll_interval: 1

redis:
  url: "redis://localhost:6379/0"

security:
  token: "your-secret-token"
```

## 启动

```bash
source .venv/bin/activate
python3 hub/main.py
```

## 测试

```bash
source .venv/bin/activate
python3 hub/test/test_hub.py
```

## API 接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/health` | GET | 健康检查 |
| `/api/v1/upload` | POST | 上传消息 |
| `/api/v1/poll` | GET | 轮询消息 |

详细 API 说明见项目根目录的 README.md
