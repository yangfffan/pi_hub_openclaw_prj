"""配置管理模块"""
import os
import yaml
from pathlib import Path
from functools import lru_cache


class Config:
    """HUB 配置类"""

    def __init__(self, config_path: str = None):
        if config_path is None:
            # 默认使用当前目录下的 config.yaml
            config_path = Path(__file__).parent / "config.yaml"

        with open(config_path, "r", encoding="utf-8") as f:
            self._config = yaml.safe_load(f)

    @property
    def server_host(self) -> str:
        return self._config.get("server", {}).get("host", "0.0.0.0")

    @property
    def server_port(self) -> int:
        return self._config.get("server", {}).get("port", 8443)

    @property
    def server_ssl_enabled(self) -> bool:
        return self._config.get("server", {}).get("ssl", {}).get("enabled", False)

    @property
    def server_ssl_cert(self) -> str:
        return self._config.get("server", {}).get("ssl", {}).get("cert", "")

    @property
    def server_ssl_key(self) -> str:
        return self._config.get("server", {}).get("ssl", {}).get("key", "")

    @property
    def openclaw_gateway_url(self) -> str:
        return self._config.get("openclaw", {}).get("gateway_url", "http://localhost:18789")

    @property
    def openclaw_agent_id(self) -> str:
        return self._config.get("openclaw", {}).get("agent_id", "main")

    @property
    def openclaw_poll_interval(self) -> int:
        return self._config.get("openclaw", {}).get("poll_interval", 1)

    @property
    def redis_url(self) -> str:
        return self._config.get("redis", {}).get("url", "redis://localhost:6379/0")

    @property
    def security_token(self) -> str:
        return self._config.get("security", {}).get("token", "")


@lru_cache()
def get_config() -> Config:
    """获取配置单例"""
    return Config()
