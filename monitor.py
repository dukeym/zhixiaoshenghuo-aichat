import os
import subprocess
import time
import argparse
from datetime import datetime

import requests

from chat_api import ChatAPI
from app_logging import get_logger


logger = get_logger("monitor")


DEFAULT_INTERVAL = 3
ALERT_COOLDOWN = 1800
SUCCESS_NOTIFY_INTERVAL = 100
OPENCLAW_TARGET = "o9cq801auUysbBD-UsbzsDbNiHz4@im.wechat"
OPENCLAW_CHANNEL = os.getenv(
    "OPENCLAW_CHANNEL",
    "openclaw-weixin",
)
OPENCLAW_WINDOWS_CWD = os.getenv(
    "OPENCLAW_WINDOWS_CWD",
    "/mnt/c/Users/gm328",
)
NTFY_TOPIC = os.getenv("NTFY_TOPIC", "")


def notify(text: str):
    """通过 Windows 侧 OpenClaw CLI 给微信发送提醒。"""
    if NTFY_TOPIC and notify_ntfy(text):
        return

    if not OPENCLAW_TARGET:
        logger.warning("未配置 OPENCLAW_TARGET，只在终端显示提醒")
        return

    command = [
        "cmd.exe", "/c", "openclaw", "message", "send",
        "--channel", OPENCLAW_CHANNEL,
        "--target", OPENCLAW_TARGET,
        "--message", text,
    ]
    try:
        subprocess.run(
            command,
            check=True,
            timeout=30,
            capture_output=True,
            text=True,
            **({"cwd": OPENCLAW_WINDOWS_CWD} if os.path.isdir(OPENCLAW_WINDOWS_CWD) else {}),
        )
        logger.info("微信提醒已发送")
    except Exception as exc:
        logger.warning("cmd.exe 调用 OpenClaw 失败：%s，尝试 PowerShell", exc)
        try:
            escaped = text.replace("'", "''")
            powershell_command = (
                "openclaw message send "
                f"--channel '{OPENCLAW_CHANNEL}' "
                f"--target '{OPENCLAW_TARGET}' "
                f"--message '{escaped}'"
            )
            subprocess.run(
                ["powershell.exe", "-NoProfile", "-Command", powershell_command],
                check=True,
                timeout=30,
                capture_output=True,
                text=True,
                **({"cwd": OPENCLAW_WINDOWS_CWD} if os.path.isdir(OPENCLAW_WINDOWS_CWD) else {}),
            )
            logger.info("微信提醒已发送（PowerShell）")
        except Exception as fallback_exc:
            logger.exception("OpenClaw 两种调用方式都失败：%s", fallback_exc)


def notify_ntfy(text: str) -> bool:
    """通过 ntfy 推送到手机；禁用环境代理，避免代理握手失败。"""
    try:
        session = requests.Session()
        session.trust_env = False
        response = session.post(
            f"https://ntfy.sh/{NTFY_TOPIC}",
            data=text.encode("utf-8"),
            headers={"Title": "chat-monitor"},
            timeout=15,
        )
        response.raise_for_status()
        logger.info("ntfy 通知已发送")
        return True
    except Exception as exc:
        logger.exception("ntfy 通知发送失败：%s", exc)
        return False


def parse_args():
    parser = argparse.ArgumentParser(description="聊天历史接口监控")
    parser.add_argument(
        "-t", "--interval",
        type=float,
        default=DEFAULT_INTERVAL,
        help="轮询间隔秒数，默认 3 秒",
    )
    args = parser.parse_args()
    if args.interval <= 0:
        parser.error("轮询间隔必须大于 0")
    return args


def main():
    interval = parse_args().interval
    api = ChatAPI()
    last_error = None
    last_alert_at = 0.0
    success_count = 0

    logger.info("历史记录接口监控已启动")
    logger.info("轮询间隔：%s 秒", interval)

    while True:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        try:
            history = api.get_history(page_size=1)
            success_count += 1
            if api.last_auto_refresh:
                message = (
                    "检测到一次 103 登录状态异常，已自动刷新主页并恢复。"
                    f"时间：{now}"
                )
                logger.warning(message)
                notify(message)
            if success_count % SUCCESS_NOTIFY_INTERVAL == 0:
                notify(
                    "历史接口监控进度："
                    f"已成功轮询 {success_count} 次。时间：{now}"
                )
            if last_error is not None:
                message = f"聊天平台历史接口已恢复正常。时间：{now}"
                logger.info(message)
                notify(message)
                last_error = None
            else:
                logger.info("接口正常，返回 %s 条记录", len(history))
            time.sleep(interval)
        except Exception as exc:
            error_text = str(exc)
            error_key = error_text[:300]
            message = (
                "聊天平台历史接口异常，机器人可能无法收到新消息。\n"
                f"时间：{now}\n"
                f"错误：{error_text[:500]}"
            )
            logger.error(message)

            if (
                error_key != last_error
                or time.time() - last_alert_at >= ALERT_COOLDOWN
            ):
                notify(message)
                last_error = error_key
                last_alert_at = time.time()

            time.sleep(interval)


if __name__ == "__main__":
    main()
