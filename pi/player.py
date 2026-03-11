"""音频播放模块"""
import wave
import logging
import pyaudio
from typing import Optional
import io

logger = logging.getLogger(__name__)

CHUNK = 1024


class Player:
    """音频播放模块"""

    def __init__(self):
        self._audio = None

    def _init_audio(self):
        """初始化音频设备"""
        if self._audio is None:
            self._audio = pyaudio.PyAudio()

    def play_file(self, filename: str) -> bool:
        """
        播放 WAV 文件

        Args:
            filename: 文件路径

        Returns:
            是否成功
        """
        self._init_audio()

        try:
            wf = wave.open(filename, 'rb')

            stream = self._audio.open(
                format=self._audio.get_format_from_width(wf.getsampwidth()),
                channels=wf.getnchannels(),
                rate=wf.getframerate(),
                output=True
            )

            logger.info(f"播放: {filename}")

            data = wf.readframes(CHUNK)
            while data:
                stream.write(data)
                data = wf.readframes(CHUNK)

            stream.stop_stream()
            stream.close()
            wf.close()

            return True

        except Exception as e:
            logger.error(f"播放失败: {e}")
            return False

    def play_bytes(self, audio_data: bytes) -> bool:
        """
        播放音频字节数据

        Args:
            audio_data: WAV 格式的音频数据

        Returns:
            是否成功
        """
        self._init_audio()

        try:
            buffer = io.BytesIO(audio_data)
            wf = wave.open(buffer, 'rb')

            stream = self._audio.open(
                format=self._audio.get_format_from_width(wf.getsampwidth()),
                channels=wf.getnchannels(),
                rate=wf.getframerate(),
                output=True
            )

            logger.info("播放音频数据")

            data = wf.readframes(CHUNK)
            while data:
                stream.write(data)
                data = wf.readframes(CHUNK)

            stream.stop_stream()
            stream.close()
            wf.close()

            return True

        except Exception as e:
            logger.error(f"播放失败: {e}")
            return False

    def close(self):
        """关闭音频设备"""
        if self._audio:
            self._audio.terminate()
        self._audio = None
