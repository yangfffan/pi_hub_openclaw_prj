"""Redis 客户端模块"""
import json
import redis
from typing import Optional, List, Dict, Any
from config import get_config


class RedisClient:
    """Redis 客户端封装"""

    UPLOAD_QUEUE_KEY = "hub:upload:queue"
    DOWNLOAD_QUEUE_PREFIX = "hub:download:"

    def __init__(self):
        config = get_config()
        self._client = redis.from_url(config.redis_url, decode_responses=True)

    @property
    def client(self) -> redis.Redis:
        return self._client

    def push_upload(self, message: Dict[str, Any]) -> int:
        """推送到上传队列"""
        return self._client.rpush(self.UPLOAD_QUEUE_KEY, json.dumps(message))

    def pop_upload(self, timeout: int = 0) -> Optional[Dict[str, Any]]:
        """从上传队列取出消息（阻塞）"""
        if timeout > 0:
            result = self._client.blpop(self.UPLOAD_QUEUE_KEY, timeout=timeout)
            if result:
                return json.loads(result[1])
            return None
        else:
            result = self._client.lpop(self.UPLOAD_QUEUE_KEY)
            if result:
                return json.loads(result)
            return None

    def get_upload_queue_length(self) -> int:
        """获取上传队列长度"""
        return self._client.llen(self.UPLOAD_QUEUE_KEY)

    def push_download(self, device_id: str, message: Dict[str, Any]) -> int:
        """推送到指定设备的下发队列"""
        key = f"{self.DOWNLOAD_QUEUE_PREFIX}{device_id}"
        return self._client.rpush(key, json.dumps(message))

    def pop_download(self, device_id: str, timeout: int = 0) -> Optional[Dict[str, Any]]:
        """从指定设备的下发队列取出消息"""
        key = f"{self.DOWNLOAD_QUEUE_PREFIX}{device_id}"
        if timeout > 0:
            result = self._client.blpop(key, timeout=timeout)
            if result:
                return json.loads(result[1])
            return None
        else:
            result = self._client.lpop(key)
            if result:
                return json.loads(result)
            return None

    def get_download_messages(self, device_id: str, max_count: int = 10) -> List[Dict[str, Any]]:
        """获取指定设备的所有下发消息（不删除）"""
        key = f"{self.DOWNLOAD_QUEUE_PREFIX}{device_id}"
        messages = self._client.lrange(key, 0, -1)
        # 删除已获取的消息
        self._client.delete(key)
        return [json.loads(msg) for msg in messages]

    def get_download_queue_length(self, device_id: str) -> int:
        """获取指定设备的下发队列长度"""
        key = f"{self.DOWNLOAD_QUEUE_PREFIX}{device_id}"
        return self._client.llen(key)


_redis_client: Optional[RedisClient] = None


def get_redis_client() -> RedisClient:
    """获取 Redis 客户端单例"""
    global _redis_client
    if _redis_client is None:
        _redis_client = RedisClient()
    return _redis_client
