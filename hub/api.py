"""消息相关 API"""
import logging
from typing import Optional
from fastapi import APIRouter, Header, HTTPException, Query
from pydantic import BaseModel

from redis_client import get_redis_client
from config import get_config

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["message"])


class UploadRequest(BaseModel):
    """上传消息请求"""
    text: str
    device_id: Optional[str] = None


class UploadResponse(BaseModel):
    """上传消息响应"""
    success: bool
    message_id: Optional[str] = None
    error: Optional[str] = None


class PollResponse(BaseModel):
    """轮询响应"""
    messages: list


def verify_token(authorization: Optional[str]) -> bool:
    """验证 Token"""
    config = get_config()
    expected_token = config.security_token

    if not expected_token:
        return True  # 未配置 Token 时跳过验证

    if not authorization:
        return False

    # 解析 Bearer token
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return False

    return parts[1] == expected_token


@router.post("/upload", response_model=UploadResponse)
async def upload_message(
    request: UploadRequest,
    authorization: Optional[str] = Header(None)
):
    """
    上传文字消息

    树莓派将 ASR 转换后的文字上传到 HUB
    """
    # 验证 Token
    if not verify_token(authorization):
        raise HTTPException(status_code=401, detail="Invalid or missing token")

    redis_client = get_redis_client()

    # 生成消息 ID
    import time
    message_id = f"msg_{int(time.time() * 1000)}"

    # 构建消息
    message = {
        "id": message_id,
        "text": request.text,
        "device_id": request.device_id or "unknown",
        "timestamp": int(time.time())
    }

    try:
        # 推送到上传队列
        redis_client.push_upload(message)
        logger.info(f"Uploaded message: {message_id}, text: {request.text[:50]}...")

        return UploadResponse(
            success=True,
            message_id=message_id
        )
    except Exception as e:
        logger.error(f"Failed to upload message: {e}")
        return UploadResponse(
            success=False,
            error=str(e)
        )


@router.get("/poll", response_model=PollResponse)
async def poll_messages(
    device_id: str = Query(..., description="设备ID"),
    authorization: Optional[str] = Header(None)
):
    """
    轮询获取下发消息

    树莓派轮询获取 HUB 下发的文字消息
    """
    # 验证 Token
    if not verify_token(authorization):
        raise HTTPException(status_code=401, detail="Invalid or missing token")

    redis_client = get_redis_client()

    try:
        # 获取下发消息
        messages = redis_client.get_download_messages(device_id)
        logger.info(f"Poll: device_id={device_id}, messages_count={len(messages)}")

        return PollResponse(messages=messages)
    except Exception as e:
        logger.error(f"Failed to poll messages: {e}")
        return PollResponse(messages=[])
