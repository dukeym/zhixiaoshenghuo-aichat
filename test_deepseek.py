from deepseek_api import DeepSeekAPI


def main():
    api = DeepSeekAPI()

    messages = [
        {
            "role": "system",
            "content": "你是一个友好、自然、简洁的聊天助手。",
        },
        {
            "role": "user",
            "content": "你好，请用一句话介绍一下你自己。",
        },
    ]

    print("发送给 DeepSeek:")
    print(messages[-1]["content"])
    print()

    reply = api.chat(messages)

    print("DeepSeek 回复:")
    print(reply)


if __name__ == "__main__":
    main()
