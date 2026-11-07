import requests
from http.cookies import SimpleCookie

import config
from app_logging import get_logger


logger = get_logger("chat_api")


class ChatAPI:
    """聊天平台 API 客户端。"""

    HISTORY_PATH = (
        "/main/api/v1/guardian/"
        "guardianGetMessageVxDetails"
    )

    SEND_MESSAGE_PATH = (
        "/main/leave/msg/"
        "guardian-sent-message"
    )
    HOME_URL = "https://shujuxiaoyuan.com/parent/"
    LOGIN_BY_DING_PATH = "/main/ding/V4LoginByDingUserId"

    def __init__(self):
        self.session = requests.Session()

        # User-Agent 尽量模拟你抓包时使用的客户端环境。
        self.session.headers.update({
            "Accept": "application/json, text/plain, */*",
            "Content-Type": "application/json",
            "Origin": "https://shujuxiaoyuan.com",
            "X-Requested-With": "com.alibaba.android.rimet",
        })

        self.session.headers["authorization"] = (
            config.CHAT_AUTHORIZATION
        )

        if config.CHAT_COOKIE:
            # 不把 Cookie 固定写入请求头。登录主页会下发新的 acw_tc，
            # 交给 Session 的 CookieJar 管理后，后续请求才能自动使用新值。
            parsed_cookie = SimpleCookie()
            parsed_cookie.load(config.CHAT_COOKIE)
            for name, morsel in parsed_cookie.items():
                self.session.cookies.set(name, morsel.value)

    def get_history(
        self,
        page_num: int = 1,
        page_size: int = 20,
    ) -> list[dict]:
        """获取聊天历史记录。"""

        url = (
            config.CHAT_BASE_URL
            + self.HISTORY_PATH
        )

        payload = {
            "messageContent": {
                "pageNum": page_num,
                "pageSize": page_size,
                "searchInfo": {
                    "guardianId": config.GUARDIAN_ID,
                    "studentId": config.STUDENT_ID,
                    "studentGuid": config.STUDENT_GUID,
                    "unitGuid": config.UNIT_GUID,
                    "loginGuid": config.LOGIN_GUID,
                    "leavingMessageType": 0,
                },
            }
        }

        result = self._history_request(url, payload)

        if result.get("messageCode") != 200:
            raise RuntimeError(
                "聊天平台返回错误: "
                + str(result)
            )

        content = result.get(
            "messageContent",
            {},
        )

        return content.get("data", [])

    def _history_request(self, url: str, payload: dict) -> dict:
        response = self.session.post(
            url,
            params={"unitGuid": config.UNIT_GUID},
            json=payload,
            timeout=15,
        )
        response.raise_for_status()
        result = response.json()
        if result.get("messageCode") == 103:
            logger.warning("历史接口返回 103，先刷新智校生活主页再重试")
            self.refresh_homepage()
            response = self.session.post(
                url,
                params={"unitGuid": config.UNIT_GUID},
                json=payload,
                timeout=15,
            )
            response.raise_for_status()
            result = response.json()
        return result

    def refresh_homepage(self) -> bool:
        """模拟打开智校生活主页，刷新主页状态和服务器下发的 Cookie。"""
        try:
            response = self.session.get(
                self.HOME_URL,
                headers={"Referer": self.HOME_URL},
                timeout=15,
                allow_redirects=True,
            )
            response.raise_for_status()
            if config.DING_CORP_ID:
                login_response = self.session.post(
                    config.CHAT_BASE_URL + self.LOGIN_BY_DING_PATH,
                    params={"unitGuid": config.UNIT_GUID},
                    json={
                        "messageContent": {
                            "dingUserId": config.GUARDIAN_ID,
                            "corpId": config.DING_CORP_ID,
                        }
                    },
                    timeout=15,
                )
                login_response.raise_for_status()
                login_result = login_response.json()
                if login_result.get("messageCode") != 200:
                    logger.warning(
                        "用户登录状态刷新返回：%s",
                        login_result.get("messageCode"),
                    )
                else:
                    token = (
                        login_result.get("messageContent", {})
                        .get("token")
                    )
                    if token:
                        self.session.headers["authorization"] = token
                    logger.info("钉钉用户登录状态刷新完成")
            logger.info(
                "主页刷新完成，HTTP=%s，当前 Cookie=%s",
                response.status_code,
                ",".join(sorted(cookie.name for cookie in self.session.cookies)),
            )
            return True
        except Exception as exc:
            logger.exception("主页刷新失败：%s", exc)
            return False

    def send_message(
        self,
        content: str,
    ) -> dict:
        """向聊天平台发送一条消息。"""

        url = (
            config.CHAT_BASE_URL
            + self.SEND_MESSAGE_PATH
        )

        payload = {
            "messageContent": {
                "guardianId": config.GUARDIAN_ID,
                "studentId": config.STUDENT_ID,
                "studentGuid": config.STUDENT_GUID,
                "unitGuid": config.UNIT_GUID,
                "loginGuid": config.LOGIN_GUID,
                "leavingMessageType": 0,
                "messageContent": content,
            }
        }

        return self._send_request(url, payload)

    def _send_request(self, url: str, payload: dict) -> dict:
        response = self.session.post(
            url,
            params={"unitGuid": config.UNIT_GUID},
            json=payload,
            timeout=15,
        )
        response.raise_for_status()
        result = response.json()
        if result.get("messageCode") == 103:
            logger.warning("发送接口返回 103，先刷新智校生活主页再重试")
            self.refresh_homepage()
            response = self.session.post(
                url,
                params={"unitGuid": config.UNIT_GUID},
                json=payload,
                timeout=15,
            )
            response.raise_for_status()
            result = response.json()
        return result
