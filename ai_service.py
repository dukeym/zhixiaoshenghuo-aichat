import config
from database import Database
from deepseek_api import DeepSeekAPI
from web_search import WebSearch


COMMANDS = {
    "/help": "显示所有可用命令",
    "/model": "显示当前使用的模型",
    "/switch deepseek": "切换到 DeepSeek",
    "/switch xiaomimimo": "切换到小米 MiMo",
    "/clear memory": "清除长期记忆摘要，但保留原始聊天记录",
}


class AIService:
    """负责构建上下文并调用 DeepSeek。"""

    def __init__(self):
        self.db = Database()
        self.deepseek = DeepSeekAPI()
        self.search = WebSearch()
        saved_provider = self.db.get_setting(
            "active_provider",
            "deepseek",
        )
        if saved_provider in {"deepseek", "xiaomimimo"}:
            try:
                self.deepseek.switch(saved_provider)
            except Exception as exc:
                print(f"恢复模型失败，继续使用 DeepSeek: {exc}")
                self.deepseek.switch("deepseek")

    def reply_to(self, message: dict) -> str:
        """针对一条新消息生成回复。"""

        command = message["messageContent"].strip().lower()
        if command == "/help":
            lines = ["可用命令："]
            lines.extend(
                f"{name}：{description}"
                for name, description in COMMANDS.items()
            )
            lines.append("\n普通文字消息会交给当前模型处理。")
            return "\n".join(lines)

        if command == "/model":
            provider = self.deepseek.current_provider()
            model = (
                config.DEEPSEEK_MODEL
                if provider == "deepseek"
                else config.MIMO_MODEL
            )
            names = {
                "deepseek": "DeepSeek",
                "xiaomimimo": "小米 MiMo",
            }
            return f"当前模型：{names.get(provider, provider)}（{model}）"

        if command == "/clear memory":
            self.db.clear_summary()
            return "长期记忆摘要已清除，原始聊天记录仍然保留。"

        if command.startswith("/switch "):
            target = command.split(None, 1)[1].strip()
            aliases = {
                "deepseek": "deepseek",
                "xiaomimimo": "xiaomimimo",
            }
            if target not in aliases:
                return "用法：/switch deepseek 或 /switch xiaomimimo"
            try:
                selected = self.deepseek.switch(aliases[target])
                self.db.save_setting("active_provider", selected)
            except Exception as exc:
                return f"切换失败：{exc}"
            names = {
                "deepseek": "DeepSeek",
                "xiaomimimo": "小米 MiMo",
            }
            return f"已切换到 {names[selected]}（{selected}）。"

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

        search_context = self.search.maybe_search(
            message["messageContent"].strip()
        )
        if search_context:
            messages.append(
                {
                    "role": "system",
                    "content": (
                        "以下是针对当前问题的实时搜索资料，仅作参考。\n"
                        "回答时优先使用可靠来源；如果资料不足，请明确说明。\n"
                        + search_context
                    ),
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
