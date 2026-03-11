"""OpenClaw CLI 封装模块"""
import subprocess
import json
import logging
from typing import Optional, Dict, Any, List
from config import get_config

logger = logging.getLogger(__name__)


class OpenClawClient:
    """OpenClaw CLI 客户端封装"""

    def __init__(self):
        config = get_config()
        self._agent_id = config.openclaw_agent_id

    def send_message(self, message: str) -> Dict[str, Any]:
        """
        发送消息给 Agent 并获取回复

        Args:
            message: 要发送的消息文本

        Returns:
            包含结果的字典
        """
        cmd = [
            "openclaw",
            "agent",
            "--agent", self._agent_id,
            "-m", message,
            "--json"
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5分钟超时
            )

            if result.returncode != 0:
                logger.error(f"OpenClaw CLI error: {result.stderr}")
                return {
                    "success": False,
                    "error": result.stderr or "Unknown error",
                    "returncode": result.returncode
                }

            # 解析 JSON 输出
            try:
                output = json.loads(result.stdout)
                return {
                    "success": True,
                    "data": output
                }
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse OpenClaw output: {e}")
                return {
                    "success": False,
                    "error": f"Failed to parse output: {e}",
                    "raw_output": result.stdout
                }

        except subprocess.TimeoutExpired:
            logger.error("OpenClaw command timeout")
            return {
                "success": False,
                "error": "Command timeout"
            }
        except Exception as e:
            logger.error(f"OpenClaw command failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def read_messages(self, channel: str = "telegram", limit: int = 10) -> List[Dict[str, Any]]:
        """
        读取最近的消息

        Args:
            channel: 频道名称
            limit: 返回消息数量

        Returns:
            消息列表
        """
        cmd = [
            "openclaw",
            "message",
            "read",
            "--channel", channel,
            "--limit", str(limit),
            "--json"
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode != 0:
                logger.error(f"OpenClaw message read error: {result.stderr}")
                return []

            try:
                messages = json.loads(result.stdout)
                return messages if isinstance(messages, list) else []
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse messages: {e}")
                return []

        except Exception as e:
            logger.error(f"Failed to read messages: {e}")
            return []


_openclaw_client: Optional[OpenClawClient] = None


def get_openclaw_client() -> OpenClawClient:
    """获取 OpenClaw 客户端单例"""
    global _openclaw_client
    if _openclaw_client is None:
        _openclaw_client = OpenClawClient()
    return _openclaw_client
