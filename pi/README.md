# 树莓派客户端

本目录包含树莓派客户端代码。

## 目录结构

```
pi/
├── main.py              # 主程序
├── config.py            # 配置管理
├── http_client.py       # HTTP 客户端
├── recorder.py          # 录音模块
├── player.py            # 播放模块
├── tts.py               # 腾讯云 TTS
├── asr.py               # 腾讯云 ASR
├── config.yaml          # 配置文件
├── assets/              # 本地音效文件
│   ├── zaine.wav       # 在呢
│   ├── heard.wav       # 听到啦
│   ├── understood.wav  # 懂啦
│   ├── thinking.wav    # 我想一下
│   └── ok.wav         # 想好啦
├── test/
│   ├── test_pi.py     # 测试脚本
│   └── test_tts_asr.py # TTS→ASR 往返测试
└── requirements.txt    # Python 依赖
```

> 注意：venv 放在项目根目录，不是 pi 目录下
```

## 安装

```bash
# 在项目根目录使用虚拟环境
cd /path/to/pi_hub_openclaw_prj

# 如果没有 uv，执行：
# curl -LsSf https://astral.sh/uv/install.sh | sh
# uv venv
# uv pip install requests pyyaml

source .venv/bin/activate

# Pi 只需要 requests 和 pyyaml
# (pyaudio 仅在真实树莓派上需要)
```

## 配置

编辑 `config.yaml`:

```yaml
server:
  url: "http://your-server:8443"
  verify_ssl: true

device:
  token: "your-token"
  device_id: "pi_living_room"

audio:
  sample_rate: 16000
  channels: 1
  format: "wav"

poll:
  interval: 2

tencentcloud:
  secret_id: "your-secret-id"
  secret_key: "your-secret-key"
```

## 测试

```bash
source .venv/bin/activate
python3 pi/test/test_pi.py
python3 pi/test/test_tts_asr.py
```

## 运行

```bash
source .venv/bin/activate
python3 pi/main.py
```

程序启动后会：
1. 连接到 HUB 服务器
2. 启动轮询线程监听回复
3. 等待唤醒词（按回车模拟）

## 本地音效

需要在 `assets/` 目录下放置以下音效文件：

| 文件名 | 用途 |
|--------|------|
| zaine.wav | 唤醒响应 "在呢" |
| heard.wav | 录音结束 "听到啦" |
| understood.wav | ASR完成 "懂啦" |
| thinking.wav | 发送消息 "我想一下" |
| ok.wav | 收到回复 "想好啦" |

## 模块说明

- **tts.py**: 腾讯云语音合成
- **asr.py**: 腾讯云语音识别
- **recorder.py**: 录音功能 (pyaudio)
- **player.py**: 播放功能 (pyaudio)
- **http_client.py**: 与 HUB 通信

## TTS 配置说明

在 `config.yaml` 中配置 TTS 参数：

```yaml
tencentcloud:
  secret_id: "你的secret_id"
  secret_key: "你的secret_key"

  tts:
    voice_type: 101001  # 音色类型
    speed: 0            # 语速 [-2, 6]
    volume: 0           # 音量 [-10, 10]
    codec: "mp3"         # 音频格式
    sample_rate: 16000  # 采样率
```

### 可选参数

| 参数 | 类型 | 范围 | 默认值 | 说明 |
|------|------|------|--------|------|
| voice_type | int | - | 101001 | 音色ID |
| speed | float | [-2, 6] | 0 | 语速 (0=1.0倍) |
| volume | float | [-10, 10] | 0 | 音量 |
| codec | string | mp3/wav/pcm | mp3 | 音频格式 |
| sample_rate | int | 8000/16000/24000 | 16000 | 采样率 |

### 常见音色 ID

| voice_type | 名称 |
|------------|------|
| 0 | 青年男声 |
| 1 | 青年女声 |
| 5 | 成熟男声 |
| 101001 | 情感女声（度小美）|

### 语速参考

| speed 值 | 倍数 |
|----------|------|
| -2 | 0.6倍 |
| -1 | 0.8倍 |
| 0 | 1.0倍 |
| 1 | 1.2倍 |
| 2 | 1.5倍 |
| 6 | 2.5倍 |
