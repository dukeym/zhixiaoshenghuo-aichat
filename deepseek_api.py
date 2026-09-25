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
