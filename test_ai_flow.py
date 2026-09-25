from ai_service import AIService
from database import Database


def main():
    db = Database()
    ai = AIService()

    fake_message = {
        "messageGuid": "local-ai-test-001",
        "messageContent": "你好，请介绍一下你自己。",
        "place": 1,
        "insertTime": "2026-09-25 16:30:00",
    }

    db.save_message(fake_message)

    print("模拟收到对方消息：")
    print(fake_message["messageContent"])
    print()

    reply = ai.reply_to(fake_message)

    print("DeepSeek 生成的回复：")
    print(reply)
    print()

    print("AI_SEND_ENABLED =", config.AI_SEND_ENABLED)


if __name__ == "__main__":
    import config

    main()
