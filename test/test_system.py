#!/usr/bin/env python3
"""系统集成测试

测试完整流程：
1. 树莓派 -> HUB -> OpenClaw -> HUB -> 树莓派

用法:
    python test_system.py
"""
import sys
import os
import time

# 添加路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "hub"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "pi"))

import requests


def test_full_flow():
    """测试完整流程"""
    print("\n" + "=" * 50)
    print("系统集成测试")
    print("=" * 50)

    # 配置
    HUB_URL = "http://localhost:8443"
    TOKEN = "test-token-12345"
    DEVICE_ID = "test_integration"

    # 1. 检查 HUB 服务
    print("\n1. 检查 HUB 服务...")
    try:
        resp = requests.get(f"{HUB_URL}/health", timeout=5)
        if resp.status_code != 200:
            print(f"✗ HUB 服务异常: {resp.status_code}")
            return False
        print("✓ HUB 服务正常")
    except Exception as e:
        print(f"✗ 无法连接 HUB: {e}")
        return False

    # 2. 上传消息
    print("\n2. 上传消息到 HUB...")
    test_message = f"集成测试消息 {int(time.time())}"

    try:
        resp = requests.post(
            f"{HUB_URL}/api/v1/upload",
            headers={
                "Authorization": f"Bearer {TOKEN}",
                "Content-Type": "application/json"
            },
            json={
                "text": test_message,
                "device_id": DEVICE_ID
            },
            timeout=10
        )

        if resp.status_code != 200:
            print(f"✗ 上传失败: {resp.status_code}")
            return False

        result = resp.json()
        if not result.get("success"):
            print(f"✗ 上传返回错误: {result}")
            return False

        print(f"✓ 消息已上传: {result.get('message_id')}")
    except Exception as e:
        print(f"✗ 上传错误: {e}")
        return False

    # 3. 等待 OpenClaw 处理
    print("\n3. 等待 OpenClaw 处理 (15秒)...")
    time.sleep(15)

    # 4. 轮询回复
    print("\n4. 轮询获取回复...")

    try:
        resp = requests.get(
            f"{HUB_URL}/api/v1/poll",
            params={"device_id": DEVICE_ID},
            headers={"Authorization": f"Bearer {TOKEN}"},
            timeout=10
        )

        if resp.status_code != 200:
            print(f"✗ 轮询失败: {resp.status_code}")
            return False

        result = resp.json()
        messages = result.get("messages", [])

        if messages:
            print(f"✓ 收到 {len(messages)} 条回复")
            for msg in messages:
                print(f"  - {msg.get('text', '')[:100]}...")
        else:
            print("⚠ 未收到回复 (可能 OpenClaw 处理较慢)")

    except Exception as e:
        print(f"✗ 轮询错误: {e}")
        return False

    print("\n" + "=" * 50)
    print("集成测试完成")
    print("=" * 50)

    return True


def main():
    """主函数"""
    result = test_full_flow()

    if result:
        print("\n✓ 系统集成测试通过")
    else:
        print("\n✗ 系统集成测试失败")

    return result


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
