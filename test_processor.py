from message_processor import MessageProcessor


def main():
    processor = MessageProcessor()

    messages = processor.poll()

    print(f"发现 {len(messages)} 条新消息")
    print()

    for message in messages:
        print(
            f"[{message['insertTime']}] "
            f"place={message['place']} "
            f"id={message['messageGuid']}"
        )
        print(f"  {message['messageContent']}")
        print()


if __name__ == "__main__":
    main()
