from database import Database


def main():
    db = Database()

    fake_message = {
        "messageGuid": "local-test-incoming-001",
        "messageContent": "你好，这是一条模拟的对方消息",
        "place": 1,
        "insertTime": "2026-09-25 16:00:00",
    }

    if db.message_exists(fake_message["messageGuid"]):
        print("这条模拟消息已经处理过了")
        return

    db.save_message(fake_message)

    print("模拟收到一条对方消息：")
    print(f"内容: {fake_message['messageContent']}")
    print(f"place: {fake_message['place']}")
    print(f"id: {fake_message['messageGuid']}")


if __name__ == "__main__":
    main()
