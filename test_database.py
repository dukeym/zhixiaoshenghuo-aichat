from database import Database


def main():
    db = Database()

    test_message = {
        "messageGuid": "test-message-001",
        "messageContent": "数据库测试",
        "place": 1,
        "insertTime": "2026-09-25 00:00:00",
    }

    db.save_message(test_message)

    print(
        "第一次查询:",
        db.message_exists("test-message-001"),
    )

    db.save_message(test_message)

    print(
        "第二次查询:",
        db.message_exists("test-message-001"),
    )

    db.mark_processed("test-message-001")
    db.mark_replied("test-message-001")

    print("数据库测试完成")


if __name__ == "__main__":
    main()
