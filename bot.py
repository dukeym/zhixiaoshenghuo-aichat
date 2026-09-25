import time

import config
from ai_service import AIService
from message_processor import MessageProcessor


def split_message(content: str, max_length: int = 100) -> list[str]:
    """将消息按固定长度拆分。"""

    return [
        content[i:i + max_length]
        for i in range(0, len(content), max_length)
    ]


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
                        parts = split_message(reply, 100)

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

            time.sleep(config.POLL_INTERVAL)

        except KeyboardInterrupt:
            print()
            print("AI Chat Bot 已停止")
            break

        except Exception as exc:
            print(f"轮询发生错误: {exc}")
            print("稍后继续尝试...")
            time.sleep(config.POLL_INTERVAL)


if __name__ == "__main__":
    main()
