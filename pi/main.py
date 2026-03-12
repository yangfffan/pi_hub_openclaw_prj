#!/usr/bin/env python3
"""树莓派主程序"""
import os
import sys
import logging
import threading
import time
import base64
import wave
import io

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(__file__))

from config import get_config
from http_client import get_http_client
from recorder import Recorder
from player import Player
from tts import TTSService
from asr import ASRService
from wake import WakeWordDetector

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# 本地音效路径
ASSETS_DIR = os.path.join(os.path.dirname(__file__), "assets")


class PiClient:
    """树莓派客户端"""

    def __init__(self):
        self.config = get_config()
        self.http_client = get_http_client()
        self.recorder = Recorder(
            sample_rate=self.config.audio_sample_rate,
            channels=self.config.audio_channels
        )
        self.player = Player()
        self.tts = TTSService(
            self.config.tencentcloud_secret_id,
            self.config.tencentcloud_secret_key
        )
        self.asr = ASRService(
            self.config.tencentcloud_secret_id,
            self.config.tencentcloud_secret_key
        )
        # 使用 Picovoice 唤醒词检测
        self.wake_detector = WakeWordDetector(sensitivity=0.7)

        self._running = False
        self._poll_thread = None
        self._current_message = None  # 当前正在处理的消息

    def play_sound(self, name: str) -> bool:
        """播放本地音效"""
        sound_file = os.path.join(ASSETS_DIR, f"{name}.wav")
        if os.path.exists(sound_file):
            return self.player.play_file(sound_file)
        else:
            logger.warning(f"音效文件不存在: {sound_file}")
            return False

    def _poll_loop(self):
        """轮询下发消息的循环"""
        logger.info("开始轮询线程...")

        while self._running:
            try:
                messages = self.http_client.poll_messages()

                for msg in messages:
                    msg_id = msg.get("id")
                    text = msg.get("text")

                    # 跳过已处理的消息
                    if msg_id == self._current_message:
                        continue

                    logger.info(f"收到新消息: {text[:50]}...")

                    # 1. 播放 "想好啦" 音效
                    self.play_sound("ok")

                    # 2. TTS 转换并播放
                    self._current_message = msg_id
                    self._play_tts(text)

                    # 3. 播放完成后清除标记
                    self._current_message = None

            except Exception as e:
                logger.error(f"轮询错误: {e}")

            time.sleep(self.config.poll_interval)

        logger.info("轮询线程结束")

    def _play_tts(self, text: str):
        """播放 TTS"""
        logger.info(f"TTS 转换: {text[:50]}...")

        # 调用 TTS 服务，使用配置中的参数
        result = self.tts.synthesize(
            text,
            codec=self.config.tts_codec,
            sample_rate=self.config.tts_sample_rate
        )

        if result.get("success"):
            audio_data = base64.b64decode(result["audio"])
            self.player.play_bytes(audio_data)
            logger.info("TTS 播放完成")
        else:
            logger.error(f"TTS 失败: {result.get('error')}")

    def start(self):
        """启动客户端"""
        logger.info("启动树莓派客户端...")

        # 健康检查
        if not self.http_client.health_check():
            logger.error("无法连接到 HUB 服务")
            return

        logger.info("连接到 HUB 成功")

        # 启动轮询线程
        self._running = True
        self._poll_thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._poll_thread.start()

        # 主循环：等待唤醒词 -> 录音 -> 上传
        self._main_loop()

    def _main_loop(self):
        """主循环"""
        logger.info("主循环启动，等待唤醒词...")

        # 启动唤醒词检测
        # 如果 Porcupine 不可用，会使用简单模式
        # 可以通过设置 PICOVOICE_ACCESS_KEY 环境变量启用真正的唤醒词
        self.wake_detector.start(callback=self._handle_wake)

        while self._running:
            # 使用简单能量检测时，回调会自动触发
            # 这里主线程可以做一些其他事情
            import os
            # 检查是否有退出信号文件
            if os.path.exists("/tmp/pi_client_stop"):
                logger.info("检测到停止信号")
                break
            time.sleep(1)

        self.wake_detector.stop()

    def _handle_wake(self):
        """处理唤醒（回调函数）"""
        logger.info("========== 唤醒流程开始 ==========")

        # 1. 播放 "在呢" 音效
        logger.info("1. 播放: 在呢")
        self.play_sound("zaine")

        # 2. 开始录音
        logger.info("2. 开始录音...")
        audio_data = self.recorder.record_to_bytes(max_duration=30)

        if not audio_data:
            logger.error("录音失败")
            return

        # 3. 播放 "听到啦" 音效
        logger.info("3. 播放: 听到啦")
        self.play_sound("heard")

        # 4. ASR 语音识别
        logger.info("4. ASR 语音识别...")
        try:
            asr_result = self.asr.recognize_from_data(audio_data)

            if asr_result.get("success"):
                text = asr_result.get("text", "")
                logger.info(f"识别结果: {text}")

                # 添加提示语，让LLM回复适合语音播放
                voice_hint = "（本消息通过语音设备发送，请回复也适合语音播放，仅用自然语言文字消息，不要包含列表或链接等难以被语音播放理解的内容）"
                text = text + voice_hint
                logger.info(f"添加提示后: {text}")
            else:
                # ASR 失败，使用默认消息
                logger.error(f"ASR 失败: {asr_result.get('error')}")
                text = "你好"
        except Exception as e:
            logger.error(f"ASR 异常: {e}")
            text = "你好"

        # 5. 播放 "懂啦" 音效
        logger.info("5. 播放: 懂啦")
        self.play_sound("understood")

        # 6. 发送到 HUB
        logger.info("6. 发送到 HUB...")
        result = self.http_client.upload_message(text)

        if result.get("success"):
            logger.info(f"消息已发送: {result.get('message_id')}")

            # 7. 播放 "我想一下" 音效
            logger.info("7. 播放: 我想一下")
            self.play_sound("thinking")
        else:
            logger.error(f"发送失败: {result.get('error')}")

        logger.info("========== 唤醒流程结束 ==========")

    def stop(self):
        """停止客户端"""
        logger.info("停止客户端...")
        self._running = False

        # 停止唤醒检测
        self.wake_detector.stop()

        if self._poll_thread:
            self._poll_thread.join(timeout=5)

        self.recorder.close()
        self.player.close()


def main():
    """主函数"""
    client = PiClient()

    try:
        client.start()
    except KeyboardInterrupt:
        logger.info("收到退出信号")
    finally:
        client.stop()


if __name__ == "__main__":
    main()
