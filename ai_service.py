import config
from database import Database
from deepseek_api import DeepSeekAPI


class AIService:
    """负责构建上下文并调用 DeepSeek。"""

    def __init__(self):
        self.db = Database()
        self.deepseek = DeepSeekAPI()

    def reply_to(self, message: dict) -> str:
        """针对一条新消息生成回复。"""

        all_count = self.db.get_message_count()
        if (
            all_count > config.RECENT_MESSAGE_LIMIT
            and all_count % config.SUMMARY_REFRESH_INTERVAL == 0
        ):
            older = self.db.get_recent_messages(limit=all_count)
            older = older[:-config.RECENT_MESSAGE_LIMIT]
            if older:
                summary = self.deepseek.summarize(
                    self.db.get_summary(),
                    [
                        {
                            "role": (
                                "user" if int(item["place"]) == 1
                                else "assistant"
                            ),
                            "content": item["message_content"].strip(),
                        }
                        for item in older
                    ],
                )
                self.db.save_summary(summary)

        history = self.db.get_recent_messages(
            limit=config.RECENT_MESSAGE_LIMIT
        )
        summary = self.db.get_summary()

        messages = [
            {
                "role": "system",
                "content": config.AI_SYSTEM_PROMPT,
            }
        ]

        if summary:
            messages.append(
                {
                    "role": "system",
                    "content": "长期记忆摘要（仅供参考）：\n" + summary,
                }
            )

        for item in history:
            if int(item["place"]) == 1:
                role = "user"
            else:
                role = "assistant"

            messages.append(
                {
                    "role": role,
                    "content": item["message_content"].strip(),
                }
            )

        # 确保当前消息一定存在于上下文中
        current_guid = message["messageGuid"]

        if not any(
            item.get("message_guid") == current_guid
            for item in history
        ):
            messages.append(
                {
                    "role": "user",
                    "content": message["messageContent"].strip(),
                }
            )

        return self.deepseek.chat(messages)
