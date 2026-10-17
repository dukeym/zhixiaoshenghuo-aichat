import uuid
from datetime import datetime

from ai_service import AIService
from database import Database


def main():
    # 终端测试使用独立数据库，避免污染正式班牌聊天记录。
    service = AIService(db=Database("terminal_chat.db"))

    print("终端模拟聊天已启动")
    print("输入 /switch deepseek 或 /switch xiaomimimo 切换模型")
    print("输入 /quit 退出")
    print()

    while True:
        try:
            content = input("你：").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n终端模拟聊天已退出")
            break

        if not content:
            continue

        if content == "/quit":
            print("终端模拟聊天已退出")
            break

        message = {
            "messageGuid": "terminal-" + str(uuid.uuid4()),
            "messageContent": content,
            "insertTime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "place": 1,
        }

        try:
            service.db.save_message(message)
            reply = service.reply_to(message)
            print("AI：" + reply)
            print()
        except Exception as exc:
            print(f"AI 请求失败：{exc}\n")


if __name__ == "__main__":
    main()
