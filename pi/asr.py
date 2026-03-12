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

    def _sign_v3(self, secret_key, timestamp, date, endpoint, action, version, params):
        """V3 签名"""

        # 1. CanonicalURI
        canonical_uri = "/"

        # 2. CanonicalQueryString
        canonical_query_string = ""

        # 3. CanonicalHeaders
        canonical_headers = "content-type:application/json\nhost:asr.tencentcloudapi.com\n"

        # 4. SignedHeaders
        signed_headers = "content-type;host"

        # 5. HashedRequestPayload
        payload = json.dumps(params)
        hashed_payload = hashlib.sha256(payload.encode('utf-8')).hexdigest()

        # 6. CanonicalRequest
        http_method = "POST"
        canonical_request = f"{http_method}\n{canonical_uri}\n{canonical_query_string}\n{canonical_headers}\n{signed_headers}\n{hashed_payload}"

        # 7. StringToSign
        algorithm = "TC3-HMAC-SHA256"
        credential_scope = f"{date}/asr/tc3_request"
        hashed_canonical_request = hashlib.sha256(canonical_request.encode('utf-8')).hexdigest()
        string_to_sign = f"{algorithm}\n{timestamp}\n{credential_scope}\n{hashed_canonical_request}"

        # 8. 计算签名
        def hmac_sha256(key, msg):
            if isinstance(key, bytes):
                return hmac.new(key, msg.encode('utf-8'), hashlib.sha256).digest()
            return hmac.new(key.encode('utf-8'), msg.encode('utf-8'), hashlib.sha256).digest()

        secret_date = hmac_sha256("TC3" + secret_key, date)
        secret_service = hmac_sha256(secret_date, "asr")
        secret_signing = hmac_sha256(secret_service, "tc3_request")
        signature = hmac_sha256(secret_signing, string_to_sign).hex()

        # 9. Authorization
        authorization = f"TC3-HMAC-SHA256 Credential={self.secret_id}/{credential_scope}, SignedHeaders={signed_headers}, Signature={signature}"

        return authorization

    def recognize_from_url(self, url: str, engine_type: str = "16k_zh",
                          voice_format: str = "wav") -> dict:
        """通过 URL 识别语音"""
        timestamp = str(int(time.time()))
        date = time.strftime("%Y-%m-%d", time.localtime(int(timestamp)))

        params = {
            "EngSerViceType": engine_type,
            "SourceType": 0,
            "VoiceFormat": voice_format,
            "Url": url
        }

        authorization = self._sign_v3(self.secret_key, timestamp, date, self.endpoint, self.action, self.version, params)

        headers = {
            "Content-Type": "application/json",
            "Authorization": authorization,
            "X-TC-Action": self.action,
            "X-TC-Version": self.version,
            "X-TC-Timestamp": timestamp
        }

        try:
            resp = requests.post(
                f"https://{self.endpoint}/",
                data=json.dumps(params),
                headers=headers,
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
        """通过音频数据识别语音"""
        # 将音频数据转为 Base64
        if isinstance(audio_data, str):
            audio_bytes = base64.b64decode(audio_data)
        else:
            audio_bytes = audio_data

        audio_base64 = base64.b64encode(audio_bytes).decode("utf-8")
        data_len = len(audio_bytes)

        timestamp = str(int(time.time()))
        date = time.strftime("%Y-%m-%d", time.localtime(int(timestamp)))

        params = {
            "EngSerViceType": engine_type,
            "SourceType": 1,
            "VoiceFormat": voice_format,
            "Data": audio_base64,
            "DataLen": data_len
        }

        authorization = self._sign_v3(self.secret_key, timestamp, date, self.endpoint, self.action, self.version, params)

        headers = {
            "Content-Type": "application/json",
            "Authorization": authorization,
            "X-TC-Action": self.action,
            "X-TC-Version": self.version,
            "X-TC-Timestamp": timestamp
        }

        try:
            resp = requests.post(
                f"https://{self.endpoint}/",
                data=json.dumps(params),
                headers=headers,
                timeout=60
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
