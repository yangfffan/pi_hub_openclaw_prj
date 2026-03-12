"""腾讯云 TTS 语音合成服务"""
import base64
import hashlib
import hmac
import json
import time
import requests
from typing import Optional


class TTSService:
    """腾讯云 TTS 语音合成服务"""

    def __init__(self, secret_id: str, secret_key: str):
        self.secret_id = secret_id
        self.secret_key = secret_key
        self.endpoint = "tts.tencentcloudapi.com"
        self.action = "TextToVoice"
        self.version = "2019-08-23"

    def _sign_v1(self, string_to_sign: str) -> str:
        """V1 签名"""
        return base64.b64encode(
            hmac.new(
                self.secret_key.encode("utf-8"),
                string_to_sign.encode("utf-8"),
                hashlib.sha1
            ).digest()
        ).decode("utf-8")

    def synthesize(self, text: str, voice_type: int = 101001,
                   codec: str = "mp3", sample_rate: int = 16000,
                   speed: float = 0, volume: float = 0) -> dict:
        """
        合成语音

        Args:
            text: 要转换的文字
            voice_type: 音色类型 (默认 101001)
            codec: 音频格式 (mp3, wav, pcm)
            sample_rate: 采样率 (8000, 16000)
            speed: 语速 [-2, 6], 默认 0 (1.0倍)
            volume: 音量 [-10, 10], 默认 0

        Returns:
            包含音频数据的字典
        """
        timestamp = str(int(time.time()))
        nonce = "123456"

        params = {
            "Action": self.action,
            "Version": self.version,
            "Nonce": nonce,
            "SecretId": self.secret_id,
            "Timestamp": timestamp,
            "SignatureMethod": "HmacSHA1",
            "SessionId": f"tts_{timestamp}",
            "Text": text,
            "VoiceType": str(voice_type),
            "Codec": codec,
            "SampleRate": str(sample_rate),
            "Speed": str(speed),
            "Volume": str(volume)
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
                if "Audio" in result["Response"]:
                    # 返回 Base64 编码的音频数据
                    return {
                        "success": True,
                        "audio": result["Response"]["Audio"],
                        "codec": codec
                    }
                elif "Error" in result["Response"]:
                    return {
                        "success": False,
                        "error": result["Response"]["Error"]
                    }
            return {"success": False, "error": "Unknown error"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def synthesize_to_file(self, text: str, output_path: str,
                         voice_type: int = 101001,
                         codec: str = "mp3",
                         sample_rate: int = 16000,
                         speed: float = 0,
                         volume: float = 0) -> bool:
        """
        合成语音并保存到文件

        Args:
            text: 要转换的文字
            output_path: 输出文件路径
            voice_type: 音色类型
            codec: 音频格式
            sample_rate: 采样率
            speed: 语速 [-2, 6]
            volume: 音量 [-10, 10]

        Returns:
            是否成功
        """
        result = self.synthesize(text, voice_type, codec, sample_rate, speed, volume)

        if result.get("success"):
            audio_data = base64.b64decode(result["audio"])
            with open(output_path, "wb") as f:
                f.write(audio_data)
            return True
        else:
            print(f"TTS error: {result.get('error')}")
            return False
