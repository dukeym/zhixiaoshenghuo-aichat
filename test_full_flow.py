import config

from ai_service import AIService
from chat_api import ChatAPI
from database import Database


def main():
    db = Database()
    ai = AIService()
    api = ChatAPI()

    fake_message = {
        "messageGuid": "local-full-test-001",
        "messageContent": "你好，请问你是谁？",
        "place": 1,
        "insertTime": "2026-09-25 16:40:00",
    }

    print("========== 模拟对方消息 ==========")
    print(fake_message["messageContent"])
    print()

    if db.message_exists(fake_message["messageGuid"]):
        print("这条测试消息已经存在数据库。")
        return

    db.save_message(fake_message)

    print("========== 请求 DeepSeek ==========")

    reply = ai.reply_to(fake_message)

    print()
    print("========== AI 回复 ==========")
    print(reply)
    print()

    if config.AI_SEND_ENABLED:
        print("========== 发送到聊天平台 ==========")

        result = api.send_message(reply)

        db.mark_processed(fake_message["messageGuid"])
        db.mark_replied(fake_message["messageGuid"])

        print("发送成功")
        print(result)
    else:
        print("AI_SEND_ENABLED=false")
        print("本次不会发送到聊天平台。")


if __name__ == "__main__":
    main()
