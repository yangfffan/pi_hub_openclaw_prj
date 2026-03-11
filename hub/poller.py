"""OpenClaw 轮询器"""
import logging
import threading
import time
from typing import Set

from config import get_config
from redis_client import get_redis_client
from openclaw import get_openclaw_client

logger = logging.getLogger(__name__)


class OpenClawPoller:
    """OpenClaw 消息轮询器"""

    def __init__(self):
        config = get_config()
        self._interval = config.openclaw_poll_interval
        self._running = False
        self._thread = None
        self._seen_messages: Set[str] = set()  # 用于去重

    def start(self):
        """启动轮询器"""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        logger.info("OpenClaw poller started")

    def stop(self):
        """停止轮询器"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("OpenClaw poller stopped")

    def _run(self):
        """轮询主循环"""
        redis_client = get_redis_client()
        openclaw_client = get_openclaw_client()

        while self._running:
            try:
                # 读取最近消息
                messages = openclaw_client.read_messages(limit=10)

                for msg in messages:
                    msg_id = msg.get("id") or msg.get("messageId")
                    if not msg_id:
                        continue

                    # 跳过已处理的消息
                    if msg_id in self._seen_messages:
                        continue

                    # 获取消息文本
                    text = msg.get("text") or msg.get("message", {}).get("body", "")
                    if not text:
                        continue

                    # 标记为已处理
                    self._seen_messages.add(msg_id)

                    # 只保留最近1000条记录
                    if len(self._seen_messages) > 1000:
                        self._seen_messages = set(list(self._seen_messages)[-1000:])

                    # 获取来源设备（如果有）
                    source = msg.get("source") or msg.get("from") or "unknown"

                    # 存入下发队列（广播给所有设备，或可以设计特定设备）
                    # 这里简化为广播给所有设备
                    download_message = {
                        "id": msg_id,
                        "text": text,
                        "source": source,
                        "timestamp": int(time.time())
                    }

                    # 存入默认设备队列
                    redis_client.push_download("default", download_message)
                    logger.info(f"New message from OpenClaw: {msg_id}, text: {text[:50]}...")

            except Exception as e:
                logger.error(f"Polling error: {e}")

            time.sleep(self._interval)
