"""腾讯云 ASR 语音识别服务"""
import base64
import hashlib
import hmac
import json
import time
import requests
from typing import Optional


class ASRService:
    """腾讯云 ASR 一句话识别服务"""

    def __init__(self, secret_id: str, secret_key: str):
        self.secret_id = secret_id
        self.secret_key = secret_key
        self.endpoint = "asr.tencentcloudapi.com"
        self.action = "SentenceRecognition"
        self.version = "2019-06-14"
        self.region = ""  # ASR 不需要 region

    def _sign_v1(self, string_to_sign: str) -> str:
        """V1 签名"""
        return base64.b64encode(
            hmac.new(
                self.secret_key.encode("utf-8"),
                string_to_sign.encode("utf-8"),
                hashlib.sha1
            ).digest()
        ).decode("utf-8")

    def recognize_from_url(self, url: str, engine_type: str = "16k_zh",
                          voice_format: str = "wav") -> dict:
        """
        通过 URL 识别语音

        Args:
            url: 语音文件的 URL 地址
            engine_type: 引擎类型，如 16k_zh, 16k_en 等
            voice_format: 音频格式，如 wav, pcm, mp3 等

        Returns:
            识别结果字典
        """
        timestamp = str(int(time.time()))
        nonce = "123456"

        # 构造请求参数
        params = {
            "Action": self.action,
            "Version": self.version,
            "Nonce": nonce,
            "SecretId": self.secret_id,
            "Timestamp": timestamp,
            "SignatureMethod": "HmacSHA1",
            "EngSerViceType": engine_type,
            "SourceType": "0",  # 0 = URL
            "VoiceFormat": voice_format,
            "Url": url
        }

        # 排序并签名
        sorted_params = sorted(params.items())
        canonical_query_string = "&".join([f"{k}={v}" for k, v in sorted_params])
        string_to_sign = f"GET{self.endpoint}/?{canonical_query_string}"

        params["Signature"] = self._sign_v1(string_to_sign)

        try:
            resp = requests.get(
                f"https://{self.endpoint}/",
                params=params,
                timeout=30
            )
            result = resp.json()

            if "Response" in result:
                if "Result" in result["Response"]:
                    return {
                        "success": True,
                        "text": result["Response"]["Result"],
                        "duration": result["Response"].get("AudioDuration", 0)
                    }
                elif "Error" in result["Response"]:
                    return {
                        "success": False,
                        "error": result["Response"]["Error"]
                    }
            return {"success": False, "error": "Unknown error"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def recognize_from_data(self, audio_data: bytes, engine_type: str = "16k_zh",
                            voice_format: str = "wav") -> dict:
        """
        通过音频数据识别语音

        Args:
            audio_data: 音频二进制数据
            engine_type: 引擎类型
            voice_format: 音频格式

        Returns:
            识别结果字典
        """
        # 将音频数据转为 Base64
        # audio_data 可能是 str(Base64) 或 bytes，需要统一处理
        if isinstance(audio_data, str):
            # 如果是 Base64 字符串，先解码再重新编码
            audio_bytes = base64.b64decode(audio_data)
        else:
            audio_bytes = audio_data
        audio_base64 = base64.b64encode(audio_bytes).decode("utf-8")
        data_len = len(audio_bytes)

        timestamp = str(int(time.time()))
        nonce = "123456"

        params = {
            "Action": self.action,
            "Version": self.version,
            "Nonce": nonce,
            "SecretId": self.secret_id,
            "Timestamp": timestamp,
            "SignatureMethod": "HmacSHA1",
            "EngSerViceType": engine_type,
            "SourceType": "1",  # 1 = 语音数据
            "VoiceFormat": voice_format,
            "Data": audio_base64,
            "DataLen": data_len
        }

        sorted_params = sorted(params.items())
        canonical_query_string = "&".join([f"{k}={v}" for k, v in sorted_params])
        string_to_sign = f"GET{self.endpoint}/?{canonical_query_string}"

        params["Signature"] = self._sign_v1(string_to_sign)

        try:
            resp = requests.get(
                f"https://{self.endpoint}/",
                params=params,
                timeout=30
            )
            result = resp.json()

            if "Response" in result:
                if "Result" in result["Response"]:
                    return {
                        "success": True,
                        "text": result["Response"]["Result"],
                        "duration": result["Response"].get("AudioDuration", 0)
                    }
                elif "Error" in result["Response"]:
                    return {
                        "success": False,
                        "error": result["Response"]["Error"]
                    }
            return {"success": False, "error": "Unknown error"}

        except Exception as e:
            return {"success": False, "error": str(e)}
