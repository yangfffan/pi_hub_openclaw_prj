#!/usr/bin/env python3
"""语音唤醒模块

使用 Picovoice Porcupine 实现语音唤醒词检测
支持自定义唤醒词文件

用法:
    wake = WakeWordDetector()
    wake.start()
    # 检测到唤醒词后会调用回调函数
"""
import sys
import os
import logging
import threading
import time

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(__file__))

logger = logging.getLogger(__name__)

# 唤醒词文件路径
WAKE_WORD_FILE = os.path.join(os.path.dirname(__file__), "assets", "xiaoke_zh_raspberry-pi_v4_0_0.ppn")
# 中文声学模型
PORCUPINE_MODEL = os.path.join(os.path.dirname(__file__), "assets", "porcupine_params_zh.pv")


class WakeWordDetector:
    """语音唤醒词检测器"""

    def __init__(self, keywords: list = None, sensitivity: float = 0.5):
        """
        初始化唤醒词检测器

        Args:
            keywords: 唤醒词列表，默认 ["小克小克"]
            sensitivity: 灵敏度 [0, 1]，越高越容易唤醒
        """
        self.keywords = keywords or ["小克小克"]
        self.sensitivity = sensitivity
        self._porcupine = None
        self._audio = None
        self._running = False
        self._thread = None
        self._callback = None

    def _init_porcupine(self):
        """初始化 Porcupine"""
        try:
            import pvporcupine
            import pyaudio

            # 优先从环境变量读取，其次从配置文件
            access_key = os.environ.get("PICOVOICE_ACCESS_KEY", "")

            if not access_key:
                # 尝试从配置读取
                try:
                    sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
                    from config import get_config
                    config = get_config()
                    access_key = getattr(config, 'picovoice_access_key', '')
                except:
                    pass

            if not access_key:
                logger.warning("未设置 PICOVOICE_ACCESS_KEY 环境变量")
                logger.warning("请从 https://console.picovoice.ai/ 获取免费 API Key")
                return False

            # 检查唤醒词文件和中文模型是否存在
            if os.path.exists(WAKE_WORD_FILE) and os.path.exists(PORCUPINE_MODEL):
                logger.info(f"使用自定义唤醒词文件: {WAKE_WORD_FILE}")
                logger.info(f"使用中文模型: {PORCUPINE_MODEL}")
                self._porcupine = pvporcupine.create(
                    access_key=access_key,
                    keyword_paths=[WAKE_WORD_FILE],
                    model_path=PORCUPINE_MODEL,
                    sensitivities=[self.sensitivity]
                )
            elif os.path.exists(WAKE_WORD_FILE):
                logger.warning("中文模型不存在，使用英文模型")
                self._porcupine = pvporcupine.create(
                    access_key=access_key,
                    keyword_paths=[WAKE_WORD_FILE],
                    sensitivities=[self.sensitivity]
                )
            else:
                logger.warning(f"唤醒词文件不存在: {WAKE_WORD_FILE}")
                logger.warning("使用内置唤醒词 'porcupine'")
                self._porcupine = pvporcupine.create(
                    access_key=access_key,
                    keywords=["porcupine"],
                    sensitivities=[self.sensitivity]
                )

            self._audio = pyaudio.PyAudio()
            logger.info("Porcupine 初始化成功")
            return True

        except ImportError:
            logger.error("请安装 pvporcupine: pip install pvporcupine")
            return False
        except Exception as e:
            logger.error(f"Porcupine 初始化失败: {e}")
            return False

    def start(self, callback=None):
        """
        启动唤醒词检测

        Args:
            callback: 检测到唤醒词后的回调函数
        """
        if self._running:
            logger.warning("唤醒词检测已在运行")
            return

        self._callback = callback

        if not self._init_porcupine():
            logger.warning("使用模拟模式（按回车键触发）")
            self._running = True
            return

        self._running = True
        self._thread = threading.Thread(target=self._detect_loop, daemon=True)
        self._thread.start()
        logger.info("唤醒词检测已启动")

    def _detect_loop(self):
        """检测循环 - 带音量预检测的唤醒词检测"""
        import pyaudio
        import numpy as np

        # 默认阈值
        silence_threshold = 200
        silence_buffer = 0.5  # 静音缓冲时间（秒），静音0.5秒后才退出唤醒词检测
        speech_timeout = 3.0  # 连续检测到声音3秒后自动停止唤醒词检测

        stream = None
        try:
            sample_rate = self._porcupine.sample_rate

            # 先用简单模式监听音量
            stream = self._audio.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=sample_rate,
                input=True,
                frames_per_buffer=512
            )

            logger.info(f"开始监听唤醒词... (采样率: {sample_rate})")
            logger.info(f"音量阈值: {silence_threshold}, 语音超时: {speech_timeout}秒")

            wake_word_active = False
            speech_start_time = None
            speech_frames = 0
            last_sound_time = 0

            while self._running:
                try:
                    pcm = stream.read(512, exception_on_overflow=False)
                    audio_data = np.frombuffer(pcm, dtype=np.int16)

                    # 计算音量
                    volume = np.abs(audio_data).mean()

                    if volume > silence_threshold:
                        # 检测到声音，启动唤醒词检测
                        if not wake_word_active:
                            logger.info(f"检测到声音 (音量: {volume:.0f})，开始唤醒词检测")
                            wake_word_active = True
                            speech_start_time = time.time()
                            speech_frames = 0
                            last_sound_time = time.time()

                        # 更新最后有声音的时间
                        last_sound_time = time.time()

                        # 处理唤醒词
                        result = self._porcupine.process(audio_data)

                        if result >= 0:
                            logger.info("检测到唤醒词!")
                            wake_word_active = False
                            speech_start_time = None
                            if self._callback:
                                self._callback()
                        else:
                            speech_frames += 1
                            # 超时检测
                            if speech_start_time and (time.time() - speech_start_time) > speech_timeout:
                                logger.info("语音超时，停止唤醒词检测")
                                wake_word_active = False
                                speech_start_time = None
                    else:
                        # 静音
                        if wake_word_active:
                            # 静音缓冲时间内不退出
                            if time.time() - last_sound_time > silence_buffer:
                                logger.info("声音结束，停止唤醒词检测")
                                wake_word_active = False
                                speech_start_time = None

                except Exception as e:
                    logger.error(f"检测错误: {e}")
                    time.sleep(0.1)

        except Exception as e:
            logger.error(f"监听错误: {e}")
        finally:
            if stream:
                stream.stop_stream()
                stream.close()

    def stop(self):
        """停止唤醒词检测"""
        self._running = False

        if self._thread:
            self._thread.join(timeout=2)

        if self._porcupine:
            self._porcupine.delete()
            self._porcupine = None

        if self._audio:
            self._audio.terminate()
            self._audio = None

        logger.info("唤醒词检测已停止")

    def is_running(self) -> bool:
        """检查是否正在运行"""
        return self._running


# 简单的唤醒测试（不使用 Porcupine）
class SimpleWakeDetector:
    """简单的唤醒词检测器（基于能量阈值）

    这是一个简化版本，不依赖 Porcupine
    适合测试和开发
    """

    def __init__(self, threshold: int = 500):
        """
        初始化

        Args:
            threshold: 声音能量阈值
        """
        self.threshold = threshold
        self._running = False
        self._thread = None
        self._callback = None
        self._audio = None
        self._chunk = 1024

    def start(self, callback=None):
        """启动检测"""
        if self._running:
            return

        self._callback = callback
        self._running = True

        try:
            import pyaudio
            self._audio = pyaudio.PyAudio()
            self._thread = threading.Thread(target=self._detect_loop, daemon=True)
            self._thread.start()
            logger.info("简单唤醒检测已启动 (能量阈值模式)")
        except ImportError:
            logger.warning("pyaudio 未安装，使用模拟模式")
            self._running = True
            self._thread = threading.Thread(target=self._simulate_loop, daemon=True)
            self._thread.start()

    def _detect_loop(self):
        """基于能量的检测循环"""
        try:
            import pyaudio
            import numpy as np

            stream = self._audio.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=16000,
                input=True,
                frames_per_buffer=self._chunk
            )

            logger.info("开始监听声音...")

            silence_count = 0
            speech_count = 0

            while self._running:
                try:
                    data = stream.read(self._chunk, exception_on_overflow=False)
                    # 计算能量
                    audio_data = np.frombuffer(data, dtype=np.int16)
                    energy = np.abs(audio_data).mean()

                    if energy > self.threshold:
                        speech_count += 1
                        silence_count = 0

                        # 持续检测到声音一段时间后触发
                        if speech_count > 10:  # 约 640ms
                            logger.info("检测到声音!")
                            if self._callback:
                                self._callback()
                            speech_count = 0
                    else:
                        silence_count += 1
                        speech_count = 0

                except Exception as e:
                    logger.error(f"检测错误: {e}")

        except Exception as e:
            logger.error(f"监听错误: {e}")
        finally:
            if stream:
                try:
                    stream.stop_stream()
                    stream.close()
                except:
                    pass

    def _simulate_loop(self):
        """模拟循环（用于测试）"""
        while self._running:
            time.sleep(1)

    def stop(self):
        """停止检测"""
        self._running = False

        if self._thread:
            self._thread.join(timeout=2)

        if self._audio:
            try:
                self._audio.terminate()
            except:
                pass
            self._audio = None


if __name__ == "__main__":
    # 测试代码
    logging.basicConfig(level=logging.INFO)

    def on_wake():
        print("\n>>> 唤醒词检测到! <<<\n")

    print("测试唤醒词检测器")
    print("按 Ctrl+C 退出")
    print("注意: 需要设置 PICOVOICE_ACCESS_KEY 环境变量才能使用 Porcupine")
    print()

    # 使用简单模式
    detector = SimpleWakeDetector(threshold=300)
    detector.start(callback=on_wake)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n退出...")
    finally:
        detector.stop()
