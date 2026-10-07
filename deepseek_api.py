from openai import OpenAI

import config


class DeepSeekAPI:
    """DeepSeek API 客户端。"""

    def __init__(self):
        self.client = OpenAI(
            api_key=config.DEEPSEEK_API_KEY,
            base_url="https://api.deepseek.com",
            timeout=30.0,
            max_retries=0,
        )

    def chat(
        self,
        messages: list[dict],
    ) -> str:
        """根据聊天上下文生成 AI 回复。"""

        print("正在请求 DeepSeek...")

        try:
            response = self.client.chat.completions.create(
                model=config.DEEPSEEK_MODEL,
                messages=messages,
                stream=False,
                temperature=0.7,
            )
        except Exception as exc:
            raise RuntimeError(
                f"DeepSeek 请求失败: {exc}"
            ) from exc

        content = response.choices[0].message.content

        if not content:
            raise RuntimeError(
                "DeepSeek 没有返回有效内容"
            )

        return content

    def summarize(self, existing_summary: str, messages: list[dict]) -> str:
        """将较早的对话压缩为稳定的长期记忆摘要。"""
        material = "\n".join(
            f"{item['role']}: {item['content']}"
            for item in messages
        )
        prompt = (
            "请把下面的聊天内容整理成简洁的长期记忆摘要。\n"
            "只保留用户长期偏好、身份背景、重要事实、未完成事项和明确约定。\n"
            "不要记录密码、密钥等敏感信息；不要猜测；没有内容时写‘暂无长期记忆’。\n"
            "已有摘要：\n"
            f"{existing_summary or '暂无长期记忆'}\n\n"
            "新增聊天：\n"
            f"{material}"
        )
        response = self.client.chat.completions.create(
            model=config.DEEPSEEK_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "你是一个严谨的对话记忆整理器，只输出摘要。",
                },
                {"role": "user", "content": prompt},
            ],
            stream=False,
            temperature=0.2,
        )
        content = response.choices[0].message.content
        if not content:
            raise RuntimeError("DeepSeek 没有返回有效摘要")
        return content.strip()
