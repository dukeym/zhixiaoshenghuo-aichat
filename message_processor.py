from chat_api import ChatAPI
from database import Database


class MessageProcessor:
    """负责获取、去重和筛选聊天消息。"""

    def __init__(self):
        self.api = ChatAPI()
        self.db = Database()

    def poll(self):
        """轮询一次聊天记录，返回新的对方消息。"""

        messages = self.api.get_history()

        new_messages = []

        for message in messages:
            message_guid = message["messageGuid"]

            if self.db.message_exists(message_guid):
                continue

            # 先保存所有新消息
            self.db.save_message(message)

            # 只有 place=1 才交给 AI
            if int(message["place"]) == 1:
                new_messages.append(message)

        return new_messages
