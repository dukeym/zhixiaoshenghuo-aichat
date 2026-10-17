import os
import subprocess
import time
from datetime import datetime

from chat_api import ChatAPI


NORMAL_INTERVAL = 3
ERROR_INTERVAL = 3
ALERT_COOLDOWN = 1800
OPENCLAW_TARGET = "o9cq801auUysbBD-UsbzsDbNiHz4@im.wechat"
OPENCLAW_CHANNEL = os.getenv(
    "OPENCLAW_CHANNEL",
    "openclaw-weixin",
)


def notify(text: str):
    """通过 Windows 侧 OpenClaw CLI 给微信发送提醒。"""
    if not OPENCLAW_TARGET:
        print("未配置 OPENCLAW_TARGET，只在终端显示提醒")
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
        )
        print("微信提醒已发送")
    except Exception as exc:
        print(f"微信提醒发送失败：{exc}")


def main():
    api = ChatAPI()
    last_error = None
    last_alert_at = 0.0

    print("历史记录接口监控已启动")
    print(f"正常间隔：{NORMAL_INTERVAL} 秒，异常间隔：{ERROR_INTERVAL} 秒")

    while True:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        try:
            history = api.get_history(page_size=1)
            if last_error is not None:
                message = f"聊天平台历史接口已恢复正常。时间：{now}"
                print(message)
                notify(message)
                last_error = None
            else:
                print(f"[{now}] 接口正常，返回 {len(history)} 条记录")
            time.sleep(NORMAL_INTERVAL)
        except Exception as exc:
            error_text = str(exc)
            error_key = error_text[:300]
            message = (
                "聊天平台历史接口异常，机器人可能无法收到新消息。\n"
                f"时间：{now}\n"
                f"错误：{error_text[:500]}"
            )
            print(message)

            if (
                error_key != last_error
                or time.time() - last_alert_at >= ALERT_COOLDOWN
            ):
                notify(message)
                last_error = error_key
                last_alert_at = time.time()

            time.sleep(ERROR_INTERVAL)


if __name__ == "__main__":
    main()
