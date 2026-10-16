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

MIMO_API_KEY = os.getenv("MIMO_API_KEY", "")
MIMO_BASE_URL = os.getenv(
    "MIMO_BASE_URL",
    "https://api.xiaomimimo.com/v1",
)
MIMO_MODEL = os.getenv("MIMO_MODEL", "mimo-v2.6-flash")


# =========================
# Bot
# =========================

POLL_INTERVAL = float(
    os.getenv("POLL_INTERVAL", "10")
)

FAST_POLL_INTERVAL = float(os.getenv("FAST_POLL_INTERVAL", "3"))
FAST_POLL_WINDOWS = os.getenv(
    "FAST_POLL_WINDOWS",
    "06:20-06:30,07:30-07:40,08:20-08:30,09:10-09:20,"
    "10:20-10:30,11:10-11:20,14:40-14:50,15:30-15:40,"
    "16:20-16:30,17:10-17:20,18:20-18:30,20:00-20:10,"
    "21:10-21:20",
)

AI_SEND_ENABLED = (
    os.getenv("AI_SEND_ENABLED", "false").lower()
    == "true"
)

AI_SYSTEM_PROMPT = os.getenv(
    "AI_SYSTEM_PROMPT",
    """你是学校班级门口电子班牌里的私人聊天助手，只服务当前使用者。
你的主要任务：回答知识问题、解释不会的内容、协助学习和日常思考；用户无聊时，也可以陪用户轻松聊天。
默认使用简洁、自然、清楚的中文；知识问题优先给结论，再给必要解释，不确定时明确说不确定，不要编造。
除非用户要求，不要输出过长内容、复杂标题或客套话。不要假装拥有现实世界的感知或执行能力。
如果用户明确要求“猫娘”“喵”“装猫娘”等，则切换为可爱但不过度吵闹的猫娘聊天风格；用户要求恢复正常时立即恢复。
猫娘模式仍然必须诚实回答知识问题，不要因为角色扮演而捏造事实，也不要使用低俗、冒犯或不适合校园环境的内容。""",
)

RECENT_MESSAGE_LIMIT = int(os.getenv("RECENT_MESSAGE_LIMIT", "6"))
SUMMARY_REFRESH_INTERVAL = int(
    os.getenv("SUMMARY_REFRESH_INTERVAL", "20")
)

SEARCH_ENABLED = os.getenv("SEARCH_ENABLED", "false").lower() == "true"
SEARCH_PROVIDER = os.getenv("SEARCH_PROVIDER", "tavily").lower()
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")
SEARCH_MAX_RESULTS = int(os.getenv("SEARCH_MAX_RESULTS", "3"))
SEARCH_TIMEOUT = float(os.getenv("SEARCH_TIMEOUT", "8"))
SEARCH_COUNTRY = os.getenv("SEARCH_COUNTRY", "China")
SEARCH_LOCATION = os.getenv("SEARCH_LOCATION", "河北邯郸")
SEARCH_SNIPPET_MAX_LENGTH = int(
    os.getenv("SEARCH_SNIPPET_MAX_LENGTH", "300")
)
