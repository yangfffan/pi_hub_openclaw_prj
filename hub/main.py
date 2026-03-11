"""FastAPI 应用入口"""
import logging
import threading
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI

from config import get_config
from api import router as message_router
from redis_client import get_redis_client
from openclaw import get_openclaw_client
from poller import OpenClawPoller
from uploader import MessageUploader

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# 存储轮询器和上传器实例
poller: OpenClawPoller = None
uploader: MessageUploader = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    global poller, uploader

    logger.info("Starting HUB service...")

    # 初始化 Redis
    redis_client = get_redis_client()
    logger.info(f"Redis connected: {redis_client.client.ping()}")

    # 启动 OpenClaw 轮询器
    poller = OpenClawPoller()
    poller.start()
    logger.info("OpenClaw poller started")

    # 启动消息上传处理器
    uploader = MessageUploader()
    uploader.start()
    logger.info("Message uploader started")

    yield

    # 关闭
    logger.info("Stopping HUB service...")
    if poller:
        poller.stop()
    if uploader:
        uploader.stop()
    logger.info("HUB service stopped")


# 创建 FastAPI 应用
app = FastAPI(
    title="Pi Hub OpenClaw",
    description="树莓派语音代理 HUB 服务",
    version="1.0.0",
    lifespan=lifespan
)

# 注册路由
app.include_router(message_router)


@app.get("/")
async def root():
    """健康检查"""
    return {
        "status": "ok",
        "service": "Pi Hub OpenClaw"
    }


@app.get("/health")
async def health():
    """健康检查"""
    # 检查 Redis
    redis_ok = False
    try:
        redis_client = get_redis_client()
        redis_ok = redis_client.client.ping()
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")

    return {
        "status": "ok" if redis_ok else "error",
        "redis": "ok" if redis_ok else "error"
    }


def main():
    """主函数"""
    import uvicorn
    config = get_config()

    logger.info(f"Starting server on {config.server_host}:{config.server_port}")

    uvicorn.run(
        app,
        host=config.server_host,
        port=config.server_port,
        log_level="info"
    )


if __name__ == "__main__":
    main()
