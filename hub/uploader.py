"""消息上传处理器"""
import logging
import threading
import time
from typing import Optional

from redis_client import get_redis_client
from openclaw import get_openclaw_client

logger = logging.getLogger(__name__)


class MessageUploader:
    """消息上传处理器

    从上传队列取出消息，发送给 OpenClaw，
    然后将回复存入下发队列
    """

    def __init__(self):
        self._running = False
        self._thread = None

    def start(self):
        """启动处理器"""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        logger.info("Message uploader started")

    def stop(self):
        """停止处理器"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("Message uploader stopped")

    def _run(self):
        """处理主循环"""
        redis_client = get_redis_client()
        openclaw_client = get_openclaw_client()

        while self._running:
            try:
                # 从上传队列取出消息（阻塞等待）
                message = redis_client.pop_upload(timeout=1)

                if not message:
                    continue

                # 获取消息内容
                text = message.get("text")
                device_id = message.get("device_id", "unknown")
                msg_id = message.get("id", "unknown")

                if not text:
                    logger.warning(f"Empty message: {message}")
                    continue

                logger.info(f"Processing upload: {msg_id}, text: {text[:50]}...")

                # 发送给 OpenClaw
                result = openclaw_client.send_message(text)

                if result.get("success"):
                    # 解析 OpenClaw 回复
                    data = result.get("data", {})
                    payloads = data.get("result", {}).get("payloads", [])

                    # 提取回复文本
                    reply_text = None
                    for payload in payloads:
                        if payload.get("text"):
                            reply_text = payload.get("text")
                            break

                    if reply_text:
                        # 存入下发队列
                        download_message = {
                            "id": f"{msg_id}_reply",
                            "text": reply_text,
                            "source": "openclaw",
                            "timestamp": int(time.time())
                        }
                        redis_client.push_download(device_id, download_message)
                        logger.info(f"Reply stored: {reply_text[:50]}...")
                    else:
                        logger.warning(f"No reply text in result: {data}")
                else:
                    # 发送失败，存入错误消息
                    error = result.get("error", "Unknown error")
                    download_message = {
                        "id": f"{msg_id}_error",
                        "text": f"Error: {error}",
                        "source": "system",
                        "timestamp": int(time.time())
                    }
                    redis_client.push_download(device_id, download_message)
                    logger.error(f"OpenClaw error: {error}")

            except Exception as e:
                logger.error(f"Upload processing error: {e}")
                time.sleep(1)  # 错误后等待一下
