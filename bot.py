import time
from datetime import datetime

import config
from ai_service import AIService
from message_processor import MessageProcessor
from app_logging import get_logger


logger = get_logger("bot")


def split_message(content: str, max_length: int = 150) -> list[str]:
    """将消息按固定长度拆分。"""

    return [
        content[i:i + max_length]
        for i in range(0, len(content), max_length)
    ]


def get_poll_interval() -> float:
    """高频时间段每 3 秒轮询，其余时间使用默认间隔。"""
    now = datetime.now().time()
    current_minutes = now.hour * 60 + now.minute

    for window in config.FAST_POLL_WINDOWS.split(","):
        start_text, end_text = window.strip().split("-", 1)
        start_hour, start_minute = map(int, start_text.split(":", 1))
        end_hour, end_minute = map(int, end_text.split(":", 1))
        start = start_hour * 60 + start_minute
        end = end_hour * 60 + end_minute

        if start <= current_minutes < end:
            return config.FAST_POLL_INTERVAL

    return config.POLL_INTERVAL


def send_daily_weather(processor, ai):
    """每天 21:00 后发送一次今天和明天天气。"""
    now = datetime.now()
    if now.hour < 21:
        return
    today = now.date().isoformat()
    if processor.db.get_setting("weather_last_sent") == today:
        return
    try:
        parts = split_message(ai.weather.forecast(), 150)
        for index, part in enumerate(parts, start=1):
            processor.api.send_message(part)
            if index < len(parts):
                time.sleep(1)
        processor.db.save_setting("weather_last_sent", today)
        logger.info("每日天气已发送：%s", today)
    except Exception as exc:
        logger.exception("每日天气发送失败：%s", exc)


def main():
    processor = MessageProcessor()
    ai = AIService()

    logger.info("AI Chat Bot 已启动")
    logger.info("轮询间隔: %s 秒", config.POLL_INTERVAL)
    logger.info("AI_SEND_ENABLED: %s", config.AI_SEND_ENABLED)

    while True:
        try:
            if config.AI_SEND_ENABLED:
                send_daily_weather(processor, ai)
                for reminder in ai.pet.due_reminders():
                    processor.api.send_message(reminder)
            messages = processor.poll()

            for message in messages:
                logger.info("收到新消息 时间=%s 内容=%s ID=%s",
                            message["insertTime"],
                            message["messageContent"],
                            message["messageGuid"])

                try:
                    reply = ai.reply_to(message)

                    logger.info("AI 回复: %s", reply)

                    if config.AI_SEND_ENABLED:
                        parts = split_message(reply, 150)

                        for index, part in enumerate(parts, start=1):
                            logger.info("发送第 %s/%s 条，共 %s 字",
                                        index, len(parts), len(part))

                            processor.api.send_message(part)

                            if index < len(parts):
                                time.sleep(1)

                        processor.db.mark_processed(
                            message["messageGuid"]
                        )
                        processor.db.mark_replied(
                            message["messageGuid"]
                        )

                        logger.info("AI 回复已发送")
                    else:
                        logger.info("AI_SEND_ENABLED=false，本次不会实际发送")

                except Exception as exc:
                    logger.exception("处理消息失败: %s", exc)

            time.sleep(get_poll_interval())

        except KeyboardInterrupt:
            logger.info("AI Chat Bot 已停止")
            break

        except Exception as exc:
            logger.exception("轮询发生错误: %s；稍后继续尝试", exc)
            time.sleep(get_poll_interval())


if __name__ == "__main__":
    main()
