#!/usr/bin/env python3
"""Hub 测试脚本

测试内容：
1. Redis 连接
2. OpenClaw CLI
3. API 接口

用法:
    cd hub
    source venv/bin/activate
    python test/test_hub.py
"""
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from config import get_config
from redis_client import get_redis_client
from openclaw import get_openclaw_client
import subprocess


def test_redis():
    """测试 Redis"""
    print("\n" + "=" * 50)
    print("测试 Redis 连接")
    print("=" * 50)

    try:
        client = get_redis_client()
        result = client.client.ping()
        print(f"✓ Redis 连接: {result}")

        # 测试队列操作
        client.client.set("test_key", "test_value")
        value = client.client.get("test_key")
        client.client.delete("test_key")
        print(f"✓ Redis 读写: {value}")

        return True
    except Exception as e:
        print(f"✗ Redis 错误: {e}")
        return False


def test_openclaw_cli():
    """测试 OpenClaw CLI"""
    print("\n" + "=" * 50)
    print("测试 OpenClaw CLI")
    print("=" * 50)

    try:
        result = subprocess.run(
            ["openclaw", "--version"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            print(f"✓ OpenClaw 版本: {result.stdout.strip()}")
        else:
            print(f"✗ OpenClaw 错误: {result.stderr}")
            return False

        # 测试 agent 命令
        client = get_openclaw_client()
        result = client.send_message("你好")

        if result.get("success"):
            print(f"✓ OpenClaw agent 命令成功")
        else:
            print(f"✗ OpenClaw agent 失败: {result.get('error')}")
            return False

        return True
    except Exception as e:
        print(f"✗ OpenClaw 错误: {e}")
        return False


def test_openclaw_read():
    """测试 OpenClaw 读取消息"""
    print("\n" + "=" * 50)
    print("测试 OpenClaw 读取消息")
    print("=" * 50)

    try:
        client = get_openclaw_client()
        messages = client.read_messages(limit=5)
        print(f"✓ 成功读取 {len(messages)} 条消息")
        return True
    except Exception as e:
        print(f"✗ 读取消息错误: {e}")
        return False


def test_api_health():
    """测试 API 健康检查"""
    print("\n" + "=" * 50)
    print("测试 API 健康检查")
    print("=" * 50)

    try:
        import requests
        config = get_config()
        resp = requests.get(
            f"http://{config.server_host}:{config.server_port}/health",
            timeout=5
        )
        if resp.status_code == 200:
            print(f"✓ 健康检查: {resp.json()}")
            return True
        else:
            print(f"✗ 健康检查失败: {resp.status_code}")
            return False
    except Exception as e:
        print(f"✗ API 错误: {e}")
        return False


def test_api_upload():
    """测试 API 上传"""
    print("\n" + "=" * 50)
    print("测试 API 上传")
    print("=" * 50)

    try:
        import requests
        import time

        config = get_config()
        token = config.security_token

        resp = requests.post(
            f"http://{config.server_host}:{config.server_port}/api/v1/upload",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            },
            json={
                "text": f"测试消息 {int(time.time())}",
                "device_id": "test_device"
            },
            timeout=10
        )

        if resp.status_code == 200:
            result = resp.json()
            print(f"✓ 上传成功: {result}")
            return True
        else:
            print(f"✗ 上传失败: {resp.status_code}")
            return False
    except Exception as e:
        print(f"✗ API 错误: {e}")
        return False


def test_api_poll():
    """测试 API 轮询"""
    print("\n" + "=" * 50)
    print("测试 API 轮询")
    print("=" * 50)

    try:
        import requests

        config = get_config()
        token = config.security_token

        resp = requests.get(
            f"http://{config.server_host}:{config.server_port}/api/v1/poll",
            params={"device_id": "test_device"},
            headers={"Authorization": f"Bearer {token}"},
            timeout=10
        )

        if resp.status_code == 200:
            result = resp.json()
            print(f"✓ 轮询成功: {len(result.get('messages', []))} 条消息")
            return True
        else:
            print(f"✗ 轮询失败: {resp.status_code}")
            return False
    except Exception as e:
        print(f"✗ API 错误: {e}")
        return False


def main():
    """主函数"""
    print("=" * 50)
    print("Hub 服务测试")
    print("=" * 50)

    results = {}

    results["Redis"] = test_redis()
    results["OpenClaw CLI"] = test_openclaw_cli()
    results["OpenClaw Read"] = test_openclaw_read()
    results["API Health"] = test_api_health()
    results["API Upload"] = test_api_upload()
    results["API Poll"] = test_api_poll()

    # 总结
    print("\n" + "=" * 50)
    print("测试总结")
    print("=" * 50)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for name, result in results.items():
        status = "✓ 通过" if result else "✗ 失败"
        print(f"  {name}: {status}")

    print(f"\n总计: {passed}/{total} 通过")


if __name__ == "__main__":
    main()
