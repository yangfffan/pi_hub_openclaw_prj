#!/usr/bin/env python3
"""生成树莓派所需的音效文件

根据 config.yaml 中的 TTS 配置，生成以下音效文件：
- zaine.wav     ("在呢")
- heard.wav     ("听到啦")
- understood.wav ("懂啦")
- thinking.wav  ("我想一下")
- ok.wav        ("想好啦")

用法:
    python gen_assets.py
"""
import sys
import os
import base64

sys.path.insert(0, os.path.dirname(__file__))

from config import get_config
from tts import TTSService


# 要生成的音效配置
ASSETS = [
    ("在呢", "zaine.wav"),
    ("听到啦", "heard.wav"),
    ("懂啦", "understood.wav"),
    ("我想一下", "thinking.wav"),
    ("想好啦", "ok.wav"),
]


def main():
    """生成所有音效文件"""
    config = get_config()

    if not config.tencentcloud_secret_id:
        print("错误: 请先配置腾讯云 SecretId")
        print("编辑 pi/config.yaml 填入你的 API Key")
        sys.exit(1)

    # 创建 TTS 服务
    tts = TTSService(
        config.tencentcloud_secret_id,
        config.tencentcloud_secret_key
    )

    # 确保 assets 目录存在
    assets_dir = os.path.join(os.path.dirname(__file__), "assets")
    os.makedirs(assets_dir, exist_ok=True)

    print("=" * 50)
    print("生成树莓派音效文件")
    print("=" * 50)
    print(f"音色: {config.tts_voice_type}")
    print(f"语速: {config.tts_speed}")
    print(f"音量: {config.tts_volume}")
    print(f"编码: {config.tts_codec}")
    print(f"采样率: {config.tts_sample_rate}")
    print("=" * 50)

    # 生成所有文件
    success_count = 0
    for text, filename in ASSETS:
        output_path = os.path.join(assets_dir, filename)
        print(f"\n生成: {filename} ({text})")

        result = tts.synthesize(
            text,
            voice_type=config.tts_voice_type,
            codec=config.tts_codec,
            sample_rate=config.tts_sample_rate,
            speed=config.tts_speed,
            volume=config.tts_volume
        )

        if result.get("success"):
            # 解码并保存
            audio_data = base64.b64decode(result["audio"])
            with open(output_path, "wb") as f:
                f.write(audio_data)
            print(f"  ✓ 已保存: {output_path} ({len(audio_data)} bytes)")
            success_count += 1
        else:
            error = result.get("error", "Unknown error")
            print(f"  ✗ 失败: {error}")

    print("\n" + "=" * 50)
    print(f"完成: {success_count}/{len(ASSETS)} 文件生成成功")
    print("=" * 50)

    if success_count != len(ASSETS):
        sys.exit(1)


if __name__ == "__main__":
    main()
