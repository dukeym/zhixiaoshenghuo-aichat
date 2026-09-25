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

        history = self.db.get_recent_messages(limit=20)

        messages = [
            {
                "role": "system",
                "content": config.AI_SYSTEM_PROMPT,
            }
        ]

        for item in history:
            if int(item["place"]) == 1:
                role = "user"
            else:
                role = "assistant"

            messages.append(
                {
                    "role": role,
                    "content": item["message_content"],
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
                    "content": message["messageContent"],
                }
            )

        return self.deepseek.chat(messages)
