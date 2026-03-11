"""HTTP 客户端模块"""
import logging
import time
import requests
from typing import Optional, List, Dict, Any
from config import get_config

logger = logging.getLogger(__name__)


class HTTPClient:
    """HTTP 客户端封装"""

    def __init__(self):
        config = get_config()
        self._base_url = config.server_url
        self._token = config.device_token
        self._device_id = config.device_id
        self._verify_ssl = config.server_verify_ssl
        self._timeout = 30
        self._retry_times = 3
        self._retry_delay = 1  # 秒

    def _get_headers(self) -> dict:
        """获取请求头"""
        return {
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json"
        }

    def upload_message(self, text: str, device_id: str = None) -> dict:
        """
        上传文字消息到 HUB

        Args:
            text: 消息内容
            device_id: 设备 ID

        Returns:
            结果字典
        """
        device_id = device_id or self._device_id

        for i in range(self._retry_times):
            try:
                resp = requests.post(
                    f"{self._base_url}/api/v1/upload",
                    headers=self._get_headers(),
                    json={
                        "text": text,
                        "device_id": device_id
                    },
                    timeout=self._timeout,
                    verify=self._verify_ssl
                )

                if resp.status_code == 200:
                    return resp.json()
                elif resp.status_code == 401:
                    logger.error("Token 无效")
                    return {"success": False, "error": "Invalid token"}
                else:
                    logger.warning(f"Upload failed: {resp.status_code}")

            except requests.exceptions.Timeout:
                logger.warning(f"Upload timeout (retry {i+1}/{self._retry_times})")
            except requests.exceptions.ConnectionError:
                logger.warning(f"Connection error (retry {i+1}/{self._retry_times})")
            except Exception as e:
                logger.error(f"Upload error: {e}")
                return {"success": False, "error": str(e)}

            if i < self._retry_times - 1:
                time.sleep(self._retry_delay)

        return {"success": False, "error": "Max retries exceeded"}

    def poll_messages(self, device_id: str = None) -> List[Dict[str, Any]]:
        """
        轮询获取下发消息

        Args:
            device_id: 设备 ID

        Returns:
            消息列表
        """
        device_id = device_id or self._device_id

        try:
            resp = requests.get(
                f"{self._base_url}/api/v1/poll",
                params={"device_id": device_id},
                headers=self._get_headers(),
                timeout=self._timeout,
                verify=self._verify_ssl
            )

            if resp.status_code == 200:
                return resp.json().get("messages", [])
            elif resp.status_code == 401:
                logger.error("Token 无效")
                return []
            else:
                logger.warning(f"Poll failed: {resp.status_code}")
                return []

        except Exception as e:
            logger.error(f"Poll error: {e}")
            return []

    def health_check(self) -> bool:
        """健康检查"""
        try:
            resp = requests.get(
                f"{self._base_url}/health",
                timeout=5,
                verify=self._verify_ssl
            )
            return resp.status_code == 200
        except Exception:
            return False


_client: Optional[HTTPClient] = None


def get_http_client() -> HTTPClient:
    """获取 HTTP 客户端单例"""
    global _client
    if _client is None:
        _client = HTTPClient()
    return _client
