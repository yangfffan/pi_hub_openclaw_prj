"""配置管理模块"""
import os
import yaml
from pathlib import Path
from functools import lru_cache


class Config:
    """树莓派配置类"""

    def __init__(self, config_path: str = None):
        if config_path is None:
            # 默认使用当前目录下的 config.yaml
            config_path = Path(__file__).parent / "config.yaml"

        if os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                self._config = yaml.safe_load(f)
        else:
            self._config = {}

    @property
    def server_url(self) -> str:
        return self._config.get("server", {}).get("url", "http://localhost:8443")

    @property
    def server_verify_ssl(self) -> bool:
        return self._config.get("server", {}).get("verify_ssl", True)

    @property
    def device_token(self) -> str:
        return self._config.get("device", {}).get("token", "")

    @property
    def device_id(self) -> str:
        return self._config.get("device", {}).get("device_id", "pi_default")

    @property
    def poll_interval(self) -> int:
        return self._config.get("poll", {}).get("interval", 2)

    @property
    def audio_sample_rate(self) -> int:
        return self._config.get("audio", {}).get("sample_rate", 16000)

    @property
    def audio_channels(self) -> int:
        return self._config.get("audio", {}).get("channels", 1)

    @property
    def audio_format(self) -> str:
        return self._config.get("audio", {}).get("format", "wav")

    @property
    def tencentcloud_secret_id(self) -> str:
        return self._config.get("tencentcloud", {}).get("secret_id", "")

    @property
    def tencentcloud_secret_key(self) -> str:
        return self._config.get("tencentcloud", {}).get("secret_key", "")

    @property
    def tts_voice_type(self) -> int:
        return self._config.get("tencentcloud", {}).get("tts", {}).get("voice_type", 101001)

    @property
    def tts_speed(self) -> float:
        return self._config.get("tencentcloud", {}).get("tts", {}).get("speed", 0)

    @property
    def tts_volume(self) -> float:
        return self._config.get("tencentcloud", {}).get("tts", {}).get("volume", 0)

    @property
    def tts_codec(self) -> str:
        return self._config.get("tencentcloud", {}).get("tts", {}).get("codec", "mp3")

    @property
    def tts_sample_rate(self) -> int:
        return self._config.get("tencentcloud", {}).get("tts", {}).get("sample_rate", 16000)

    @property
    def picovoice_access_key(self) -> str:
        return self._config.get("picovoice", {}).get("access_key", "")


@lru_cache()
def get_config() -> Config:
    """获取配置单例"""
    return Config()
