from chat_api import ChatAPI


def main():
    api = ChatAPI()

    messages = api.get_history()

    print(f"获取到 {len(messages)} 条消息")
    print()

    for message in messages:
        print(
            f"[{message['insertTime']}] "
            f"place={message['place']} "
            f"id={message['messageGuid']}"
        )

        print(
            f"  {message['messageContent']}"
        )

        print()


if __name__ == "__main__":
    main()
