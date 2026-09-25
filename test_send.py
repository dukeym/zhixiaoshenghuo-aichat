import time

from chat_api import ChatAPI


def main():
    api = ChatAPI()

    content = (
        "你好，我想测试一下这个聊天机器人的长消息分段功能。"
        "最近我正在整理一些学习上的事情，也想顺便看看这个机器人在处理较长内容时是否能够正常工作。"
        "如果一条消息超过聊天系统允许的长度，机器人应该按照设定的规则自动把内容拆分成多条消息发送。"
        "现在这段文字故意写得比较长，主要就是为了进行实际测试。"
        "如果程序运行正常，你应该能够连续收到三条消息，而且每条消息的长度都不会超过一百个字。"
        "这样就可以确认消息拆分、连续发送以及聊天平台接口这几个部分是否都正常。"
        "测试完成以后，再换成真实的聊天内容就可以了。"
    )

    print(f"准备发送，共 {len(content)} 字")
    print(content)
    print()

    parts = [
        content[i:i + 100]
        for i in range(0, len(content), 100)
    ]

    for index, part in enumerate(parts, start=1):
        print(
            f"发送第 {index}/{len(parts)} 条，"
            f"共 {len(part)} 字"
        )

        api.send_message(part)

        if index < len(parts):
            print("等待 1 秒...")
            time.sleep(1)

    print("测试发送完成")


if __name__ == "__main__":
    main()
