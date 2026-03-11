#!/usr/bin/env python3
"""TTS <-> ASR 往返测试

测试流程：
1. TTS: 文字 -> 语音
2. ASR: 语音 -> 文字
3. 对比: 原始文字 vs 识别结果

用法:
    python test_tts_asr.py
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from config import get_config
from tts import TTSService
from asr import ASRService


def test_tts_asr_roundtrip():
    """TTS -> ASR 往返测试"""
    print("\n" + "=" * 50)
    print("TTS <-> ASR 往返测试")
    print("=" * 50)

    config = get_config()

    if not config.tencentcloud_secret_id:
        print("✗ 未配置腾讯云 SecretId")
        return False

    tts = TTSService(config.tencentcloud_secret_id, config.tencentcloud_secret_key)
    asr = ASRService(config.tencentcloud_secret_id, config.tencentcloud_secret_key)

    # 测试文字
    test_texts = [
        "你好世界",
        "今天天气不错",
        "树莓派语音助手"
    ]

    results = []

    for text in test_texts:
        print(f"\n测试文字: {text}")
        print("-" * 30)

        # 1. TTS: 文字 -> 语音
        print("1. TTS 合成...")
        tts_result = tts.synthesize(text)

        if not tts_result.get("success"):
            print(f"✗ TTS 失败: {tts_result.get('error')}")
            continue

        audio_data = tts_result["audio"]
        print(f"   ✓ TTS 成功，音频大小: {len(audio_data)} bytes")

        # 2. ASR: 语音 -> 文字 (使用 Base64 数据)
        print("2. ASR 识别...")
        asr_result = asr.recognize_from_data(
            audio_data,
            engine_type="16k_zh",
            voice_format="mp3"
        )

        if not asr_result.get("success"):
            print(f"✗ ASR 失败: {asr_result.get('error')}")
            continue

        recognized_text = asr_result.get("text", "")
        print(f"   ✓ ASR 成功，识别结果: {recognized_text}")

        # 3. 对比结果
        print("3. 对比结果...")
        # 去除标点符号再对比
        import re
        orig_clean = re.sub(r'[，。？！,\.!?\s]', '', text)
        recog_clean = re.sub(r'[，。？！,\.!?\s]', '', recognized_text)

        if orig_clean == recog_clean:
            print(f"   ✓ 匹配成功!")
            results.append(True)
        else:
            print(f"   ✗ 不匹配")
            print(f"      原始: {orig_clean}")
            print(f"      识别: {recog_clean}")
            results.append(False)

    # 总结
    print("\n" + "=" * 50)
    print("测试总结")
    print("=" * 50)

    passed = sum(results)
    total = len(results)

    print(f"通过: {passed}/{total}")

    if passed == total:
        print("\n✓ 所有往返测试通过!")
    else:
        print(f"\n✗ {total - passed} 个测试失败")

    return passed == total


def main():
    """主函数"""
    result = test_tts_asr_roundtrip()
    sys.exit(0 if result else 1)


if __name__ == "__main__":
    main()
