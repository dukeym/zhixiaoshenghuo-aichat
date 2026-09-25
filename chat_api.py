import requests

import config


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
            self.session.headers["Cookie"] = (
                config.CHAT_COOKIE
            )

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

        response = self.session.post(
            url,
            params={
                "unitGuid": config.UNIT_GUID,
            },
            json=payload,
            timeout=15,
        )

        response.raise_for_status()

        result = response.json()

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

        response = self.session.post(
            url,
            params={
                "unitGuid": config.UNIT_GUID,
            },
            json=payload,
            timeout=15,
        )

        response.raise_for_status()

        return response.json()
