import re

import requests

import config


SEARCH_WORDS = (
    "帮我搜", "搜索", "查一下", "查查", "最新", "今天", "现在",
    "新闻", "天气", "价格", "票价", "汇率", "比赛", "赛程",
    "政策", "公告", "最近", "实时",
)

LOCAL_WORDS = (
    "天气", "学校", "班级", "邯郸", "河北", "附近", "周边", "交通",
    "活动", "餐馆", "公交", "医院", "开学",
)

class WebSearch:
    """只在问题明显需要实时信息时调用搜索服务。"""

    def should_search(self, query: str) -> bool:
        normalized = query.strip()
        return any(word in normalized for word in SEARCH_WORDS)

    def maybe_search(self, query: str) -> str:
        if not config.SEARCH_ENABLED or not self.should_search(query):
            return ""

        if config.SEARCH_PROVIDER != "tavily":
            print(f"暂不支持搜索服务: {config.SEARCH_PROVIDER}")
            return ""

        if not config.TAVILY_API_KEY:
            print("未配置 TAVILY_API_KEY，跳过联网搜索")
            return ""

        try:
            search_query = self._build_query(query)
            time_range = self._get_time_range(query)
            topic = "news" if self._looks_like_news(query) else "general"
            response = requests.post(
                "https://api.tavily.com/search",
                json={
                    "api_key": config.TAVILY_API_KEY,
                    "query": search_query,
                    "topic": topic,
                    "search_depth": "basic",
                    "max_results": config.SEARCH_MAX_RESULTS,
                    "include_answer": False,
                    "include_raw_content": False,
                    **({"country": config.SEARCH_COUNTRY} if topic == "general" else {}),
                    **({"time_range": time_range} if time_range else {}),
                },
                timeout=config.SEARCH_TIMEOUT,
            )
            response.raise_for_status()
            results = response.json().get("results", [])
        except Exception as exc:
            print(f"联网搜索失败，继续使用本地知识: {exc}")
            return ""

        lines = []
        for index, item in enumerate(results[:config.SEARCH_MAX_RESULTS], start=1):
            title = self._clean(item.get("title", ""))
            content = self._clean(item.get("content", ""))[
                :config.SEARCH_SNIPPET_MAX_LENGTH
            ]
            url = item.get("url", "")
            if title and content:
                lines.append(f"{index}. {title}\n摘要：{content}\n来源：{url}")
        return "\n\n".join(lines)

    @staticmethod
    def _clean(value: str) -> str:
        return re.sub(r"\s+", " ", value or "").strip()

    @staticmethod
    def _looks_like_news(query: str) -> bool:
        return any(word in query for word in ("新闻", "公告", "最新消息"))

    @staticmethod
    def _build_query(query: str) -> str:
        if any(word in query for word in LOCAL_WORDS):
            return f"{query} {config.SEARCH_LOCATION}"
        return query

    @staticmethod
    def _get_time_range(query: str) -> str:
        if any(word in query for word in ("今天", "今日", "当天")):
            return "day"
        if any(word in query for word in ("本周", "这周", "最近一周")):
            return "week"
        if any(word in query for word in ("本月", "这个月", "最近一个月")):
            return "month"
        return ""
