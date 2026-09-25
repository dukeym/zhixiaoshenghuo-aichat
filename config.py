import os


from dotenv import load_dotenv


load_dotenv()


def get_required_env(name: str) -> str:
    """读取必填环境变量，缺失时直接报错。"""
    value = os.getenv(name)

    if not value:
        raise RuntimeError(
            f"缺少环境变量: {name}"
        )

    return value


# =========================
# 聊天平台
# =========================

CHAT_BASE_URL = get_required_env(
    "CHAT_BASE_URL"
)

CHAT_AUTHORIZATION = get_required_env(
    "CHAT_AUTHORIZATION"
)

CHAT_COOKIE = os.getenv(
    "CHAT_COOKIE",
    ""
)

UNIT_GUID = get_required_env(
    "UNIT_GUID"
)

GUARDIAN_ID = get_required_env(
    "GUARDIAN_ID"
)

STUDENT_ID = get_required_env(
    "STUDENT_ID"
)

STUDENT_GUID = get_required_env(
    "STUDENT_GUID"
)

LOGIN_GUID = get_required_env(
    "LOGIN_GUID"
)


# =========================
# DeepSeek
# =========================

DEEPSEEK_API_KEY = get_required_env(
    "DEEPSEEK_API_KEY"
)

DEEPSEEK_MODEL = os.getenv(
    "DEEPSEEK_MODEL",
    "deepseek-chat"
)


# =========================
# Bot
# =========================

POLL_INTERVAL = float(
    os.getenv("POLL_INTERVAL", "3")
)

AI_SEND_ENABLED = (
    os.getenv("AI_SEND_ENABLED", "false").lower()
    == "true"
)

AI_SYSTEM_PROMPT = os.getenv(
    "AI_SYSTEM_PROMPT",
    "你是一个友好、自然、简洁的聊天助手。请你尽量用简洁的语言回复，不要有多余语气话等，另外要求除外。",
)
