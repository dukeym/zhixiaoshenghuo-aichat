import time
from datetime import datetime

import config
from ai_service import AIService
from message_processor import MessageProcessor


def split_message(content: str, max_length: int = 150) -> list[str]:
    """将消息按固定长度拆分。"""

    return [
        content[i:i + max_length]
        for i in range(0, len(content), max_length)
    ]


def get_poll_interval() -> float:
    """高频时间段每 3 秒轮询，其余时间使用默认间隔。"""
    now = datetime.now().time()
    current_minutes = now.hour * 60 + now.minute

    for window in config.FAST_POLL_WINDOWS.split(","):
        start_text, end_text = window.strip().split("-", 1)
        start_hour, start_minute = map(int, start_text.split(":", 1))
        end_hour, end_minute = map(int, end_text.split(":", 1))
        start = start_hour * 60 + start_minute
        end = end_hour * 60 + end_minute

        if start <= current_minutes < end:
            return config.FAST_POLL_INTERVAL

    return config.POLL_INTERVAL


def main():
    processor = MessageProcessor()
    ai = AIService()

    print("================================")
    print("AI Chat Bot 已启动")
    print(f"轮询间隔: {config.POLL_INTERVAL} 秒")
    print(f"AI_SEND_ENABLED: {config.AI_SEND_ENABLED}")
    print("================================")
    print()

    while True:
        try:
            messages = processor.poll()

            for message in messages:
                print("收到新消息")
                print(f"时间: {message['insertTime']}")
                print(f"内容: {message['messageContent']}")
                print(f"ID: {message['messageGuid']}")
                print()

                try:
                    reply = ai.reply_to(message)

                    print("AI 回复:")
                    print(reply)
                    print()

                    if config.AI_SEND_ENABLED:
                        parts = split_message(reply, 150)

                        for index, part in enumerate(parts, start=1):
                            print(
                                f"发送第 {index}/{len(parts)} 条，"
                                f"共 {len(part)} 字"
                            )

                            processor.api.send_message(part)

                            if index < len(parts):
                                time.sleep(1)

                        processor.db.mark_processed(
                            message["messageGuid"]
                        )
                        processor.db.mark_replied(
                            message["messageGuid"]
                        )

                        print("AI 回复已发送")
                    else:
                        print(
                            "AI_SEND_ENABLED=false，"
                            "本次不会实际发送"
                        )

                    print()

                except Exception as exc:
                    print(f"处理消息失败: {exc}")
                    print()

            time.sleep(get_poll_interval())

        except KeyboardInterrupt:
            print()
            print("AI Chat Bot 已停止")
            break

        except Exception as exc:
            print(f"轮询发生错误: {exc}")
            print("稍后继续尝试...")
            time.sleep(get_poll_interval())


if __name__ == "__main__":
    main()
