import time

import config
from ai_service import AIService
from database import Database
from message_processor import MessageProcessor


def main():
    processor = MessageProcessor()
    ai = AIService()
    db = Database()

    fake_message = {
        "messageGuid": "local-auto-test-001",
        "messageContent": (
            "你好，这是一次完整自动回复测试。"
            "我想测试机器人能不能正确识别一条来自对方的消息，"
            "然后把消息交给 DeepSeek API 进行处理，"
            "接收到 DeepSeek 的回复以后，"
            "再自动把回复发送回聊天系统。"
        ),
        "place": 1,
        "insertTime": "2026-09-25 12:00:00",
    }

    print("================================")
    print("开始完整自动回复测试")
    print("================================")
    print()

    # 模拟收到对方消息
    print("模拟收到对方消息:")
    print(fake_message["messageContent"])
    print()

    # 保存到数据库
    if not db.message_exists(fake_message["messageGuid"]):
        db.save_message(fake_message)
        print("消息已保存到 SQLite")
    else:
        print("这条测试消息已经存在")
        print("如果要重新测试，请修改 messageGuid")
        return

    # place=1，模拟对方消息
    if int(fake_message["place"]) != 1:
        print("不是对方消息，测试结束")
        return

    print()
    print("识别为对方消息")
    print("开始请求 DeepSeek...")
    print()

    try:
        # 调用 DeepSeek
        reply = ai.reply_to(fake_message)

        print("DeepSeek 回复:")
        print(reply)
        print()

        if not config.AI_SEND_ENABLED:
            print("AI_SEND_ENABLED=false")
            print("不会实际发送")
            return

        # 按 100 字拆分
        parts = [
            reply[i:i + 100]
            for i in range(0, len(reply), 100)
        ]

        print(f"准备发送，共 {len(parts)} 条")
        print()

        for index, part in enumerate(parts, start=1):
            print(
                f"发送第 {index}/{len(parts)} 条，"
                f"共 {len(part)} 字"
            )

            processor.api.send_message(part)

            if index < len(parts):
                time.sleep(1)

        db.mark_processed(
            fake_message["messageGuid"]
        )

        db.mark_replied(
            fake_message["messageGuid"]
        )

        print()
        print("================================")
        print("完整自动回复测试成功")
        print("================================")

    except Exception as exc:
        print()
        print("测试失败:")
        print(exc)


if __name__ == "__main__":
    main()
