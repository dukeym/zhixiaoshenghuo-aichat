import config
from database import Database
from deepseek_api import DeepSeekAPI
from web_search import WebSearch
from pet import PetService


COMMANDS = {
    "/help": "显示所有可用命令",
    "/model": "显示当前使用的模型",
    "/switch deepseek": "切换到 DeepSeek",
    "/switch xiaomimimo": "切换到小米 MiMo",
    "/clear memory chat": "清除聊天长期记忆摘要",
    "/clear memory pet": "删除电子宠物及其所有数据",
    "/pet": "进入电子宠物模式或查看宠物状态",
    "/pet feed": "喂养宠物，消耗 5 金币",
    "/pet play": "陪宠物玩耍，提升心情",
    "/pet work": "让宠物工作赚取金币",
    "/pet shop": "查看宠物商店",
    "/pet buy 小鱼干": "购买并使用宠物道具",
    "/pet rename 名字": "给宠物改名",
    "/pet off": "退出宠物操作，回到普通聊天",
}


class AIService:
    """负责构建上下文并调用 DeepSeek。"""

    def __init__(self):
        self.db = Database()
        self.deepseek = DeepSeekAPI()
        self.search = WebSearch()
        self.pet = PetService()
        self.pending_clear = None
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

        raw_text = message["messageContent"].strip()
        command = raw_text.lower()

        if self.pending_clear:
            if command in {"y", "yes"}:
                target = self.pending_clear
                self.pending_clear = None
                if target == "chat":
                    self.db.clear_summary()
                    return "聊天长期记忆已清除，原始聊天记录仍然保留。"
                self.pet.clear()
                return "电子宠物及其等级、金币、状态已删除。"
            if command in {"n", "no"}:
                self.pending_clear = None
                return "已取消清理。"
            return "请回复 y 确认清理，或回复 n 取消。"

        if command in {"/clear memory", "/clear memory chat"}:
            self.pending_clear = "chat"
            return "确定要清除聊天长期记忆吗？原始聊天记录不会删除。回复 y 确认，n 取消。"

        if command == "/clear memory pet":
            if not self.pet.has_pet():
                return "当前没有电子宠物。"
            self.pending_clear = "pet"
            return "确定要删除电子宠物及其全部数据吗？回复 y 确认，n 取消。"

        if command == "/pet" or command.startswith("/pet "):
            pet_text = message["messageContent"].strip()[4:].strip()
            local_commands = {
                "status", "状态", "feed", "喂", "喂食", "play", "玩", "玩耍",
                "work", "工作", "挣钱", "赚钱", "shop", "商店", "off", "退出", "关闭",
            }
            is_local = (
                not self.pet.has_pet()
                or not pet_text
                or pet_text.lower() in local_commands
                or pet_text.lower().startswith(("rename ", "改名 ", "buy ", "购买 "))
            )
            if is_local:
                return self.pet.handle(message["messageContent"])

            context = self.pet.chat_context()
            pet_prompt = (
                "你现在是一只真实存在于聊天中的电子宠物。"
                "请始终以宠物身份和主人聊天，不要提及你是语言模型、API、系统提示词或普通聊天助手。"
                "可以可爱、自然、有一点拟人化，但不要每句话都重复自我介绍。"
                "请结合宠物状态回答，回复简洁，尽量控制在150字以内。\n"
                f"当前宠物资料：{context}"
            )
            return self.deepseek.chat([
                {"role": "system", "content": pet_prompt},
                {"role": "user", "content": pet_text},
            ])
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
