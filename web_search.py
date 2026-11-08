import re
from datetime import datetime, timedelta

import requests

import config


SEARCH_WORDS = (
    "帮我搜", "搜索", "查一下", "查查", "最新", "今天", "现在",
    "新闻", "天气", "价格", "票价", "汇率", "比赛", "赛程",
    "比分", "战况", "赛况", "nba", "篮球",
    "政策", "公告", "最近", "实时", "缅甸",
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

        if self._looks_like_sports(query):
            sports_result = self._sports_scores(query)
            if sports_result:
                return sports_result

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

    def search(self, query: str) -> str:
        """强制搜索，不要求查询包含实时关键词。"""
        original = self.should_search
        try:
            self.should_search = lambda _query: True
            return self.maybe_search(query)
        finally:
            self.should_search = original

    @staticmethod
    def _clean(value: str) -> str:
        return re.sub(r"\s+", " ", value or "").strip()

    @staticmethod
    def _looks_like_news(query: str) -> bool:
        return any(word in query for word in ("新闻", "公告", "最新消息"))

    @staticmethod
    def _looks_like_sports(query: str) -> bool:
        text = query.lower()
        return any(word in text for word in (
            "nba", "篮球", "比分", "战况", "赛况", "比赛结果",
        ))

    @staticmethod
    def _sports_scores(query: str = "") -> str:
        """读取指定日期的 ESPN scoreboard，避免模型自行猜日期。"""
        target_date = datetime.now().date()
        if any(word in query.lower() for word in ("昨天", "yesterday")):
            target_date -= timedelta(days=1)
        elif any(word in query.lower() for word in ("明天", "tomorrow")):
            target_date += timedelta(days=1)
        date_text = target_date.strftime("%Y%m%d")
        try:
            response = requests.get(
                "https://site.api.espn.com/apis/site/v2/sports/"
                "basketball/nba/scoreboard",
                params={"dates": date_text},
                timeout=config.SEARCH_TIMEOUT,
                headers={"User-Agent": "Mozilla/5.0"},
            )
            response.raise_for_status()
            events = response.json().get("events", [])
        except Exception as exc:
            print(f"NBA 实时比分接口失败，改用网页搜索: {exc}")
            return ""

        if not events:
            return f"NBA {target_date.isoformat()} 没有比赛，或当天还没有发布赛程。"

        lines = [f"NBA {target_date.isoformat()} 比分："]
        for event in events:
            competition = (event.get("competitions") or [{}])[0]
            status = event.get("status", {}).get("type", {})
            detail = status.get("detail") or status.get("shortDetail") or "状态未知"
            teams = []
            for competitor in competition.get("competitors", []):
                team = competitor.get("team", {})
                name = team.get("displayName") or team.get("abbreviation", "球队")
                score = competitor.get("score", "-")
                teams.append(f"{name} {score}")
            if teams:
                lines.append(f"{'，'.join(teams)}（{detail}）")
        return "\n".join(lines)

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
