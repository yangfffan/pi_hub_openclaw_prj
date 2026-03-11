"""录音模块"""
import wave
import logging
import threading
import pyaudio
from typing import Optional

logger = logging.getLogger(__name__)

# 录音参数
CHUNK = 1024
FORMAT = pyaudio.paInt16
SILENCE_THRESHOLD = 500  # 静音阈值
SILENCE_DURATION = 1.5  # 静音持续多少秒认为录音结束


class Recorder:
    """录音模块"""

    def __init__(self, sample_rate: int = 16000, channels: int = 1):
        self.sample_rate = sample_rate
        self.channels = channels
        self._audio = None
        self._stream = None
        self._recording = False

    def _init_audio(self):
        """初始化音频设备"""
        if self._audio is None:
            self._audio = pyaudio.PyAudio()

    def record_to_file(self, filename: str, max_duration: int = 30) -> bool:
        """
        录音并保存到文件

        Args:
            filename: 输出文件名
            max_duration: 最大录音时长（秒）

        Returns:
            是否成功
        """
        self._init_audio()

        try:
            # 打开流
            self._stream = self._audio.open(
                format=FORMAT,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=CHUNK
            )

            logger.info("开始录音...")
            frames = []
            silence_count = 0
            max_chunks = int(self.sample_rate / CHUNK * max_duration)

            self._recording = True
            chunk_count = 0

            while self._recording and chunk_count < max_chunks:
                data = self._stream.read(CHUNK, exception_on_overflow=False)
                frames.append(data)
                chunk_count += 1

                # 检查是否静音
                import numpy as np
                audio_data = np.frombuffer(data, dtype=np.int16)
                if np.abs(audio_data).mean() < SILENCE_THRESHOLD:
                    silence_count += 1
                else:
                    silence_count = 0

                # 静音持续一定时长后停止
                if silence_count > (self.sample_rate / CHUNK * SILENCE_DURATION):
                    logger.info("检测到静音，停止录音")
                    break

            # 停止并保存
            self._stream.stop_stream()
            self._stream.close()
            self._stream = None

            # 保存为 WAV 文件
            with wave.open(filename, 'wb') as wf:
                wf.setnchannels(self.channels)
                wf.setsampwidth(2)  # 16位
                wf.setframerate(self.sample_rate)
                wf.writeframes(b''.join(frames))

            logger.info(f"录音已保存: {filename}")
            return True

        except Exception as e:
            logger.error(f"录音失败: {e}")
            return False

    def record_to_bytes(self, max_duration: int = 30) -> Optional[bytes]:
        """
        录音并返回字节数据

        Args:
            max_duration: 最大录音时长

        Returns:
            WAV 格式的音频数据
        """
        self._init_audio()

        try:
            self._stream = self._audio.open(
                format=FORMAT,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=CHUNK
            )

            logger.info("开始录音...")
            frames = []
            silence_count = 0
            max_chunks = int(self.sample_rate / CHUNK * max_duration)

            self._recording = True
            chunk_count = 0

            while self._recording and chunk_count < max_chunks:
                data = self._stream.read(CHUNK, exception_on_overflow=False)
                frames.append(data)
                chunk_count += 1

                import numpy as np
                audio_data = np.frombuffer(data, dtype=np.int16)
                if np.abs(audio_data).mean() < SILENCE_THRESHOLD:
                    silence_count += 1
                else:
                    silence_count = 0

                if silence_count > (self.sample_rate / CHUNK * SILENCE_DURATION):
                    logger.info("检测到静音，停止录音")
                    break

            self._stream.stop_stream()
            self._stream.close()
            self._stream = None

            # 转换为 WAV 格式字节
            import io
            buffer = io.BytesIO()
            with wave.open(buffer, 'wb') as wf:
                wf.setnchannels(self.channels)
                wf.setsampwidth(2)
                wf.setframerate(self.sample_rate)
                wf.writeframes(b''.join(frames))

            return buffer.getvalue()

        except Exception as e:
            logger.error(f"录音失败: {e}")
            return None

    def stop(self):
        """停止录音"""
        self._recording = False

    def close(self):
        """关闭音频设备"""
        if self._stream:
            self._stream.close()
        if self._audio:
            self._audio.terminate()
        self._audio = None
        self._stream = None
