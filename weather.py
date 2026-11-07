from datetime import datetime

import requests

import config


WEATHER_CODES = {
    0: "晴",
    1: "大部晴",
    2: "多云",
    3: "阴",
    45: "雾",
    48: "冻雾",
    51: "小毛毛雨",
    53: "毛毛雨",
    55: "较强毛毛雨",
    61: "小雨",
    63: "中雨",
    65: "大雨",
    71: "小雪",
    73: "中雪",
    75: "大雪",
    80: "阵雨",
    81: "较强阵雨",
    82: "强阵雨",
    95: "雷雨",
    96: "雷雨伴冰雹",
    99: "强雷雨伴冰雹",
}


class WeatherService:
    """通过 Open-Meteo 获取指定地区的实时和未来天气。"""

    def forecast(self) -> str:
        location = self._geocode(config.WEATHER_LOCATION)
        if not location:
            return "天气查询失败：找不到地区。"

        response = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": location["latitude"],
                "longitude": location["longitude"],
                "current": "temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m",
                "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max",
                "forecast_days": 2,
                "timezone": "Asia/Shanghai",
            },
            timeout=config.WEATHER_TIMEOUT,
        )
        response.raise_for_status()
        data = response.json()
        current = data.get("current", {})
        daily = data.get("daily", {})
        dates = daily.get("time", [])
        if len(dates) < 2:
            return "天气查询失败：天气服务没有返回今天和明天的数据。"

        current_text = (
            f"当前 {current.get('temperature_2m', '?')}°C，"
            f"{WEATHER_CODES.get(current.get('weather_code'), '未知天气')}，"
            f"湿度 {current.get('relative_humidity_2m', '?')}%，"
            f"风速 {current.get('wind_speed_10m', '?')} km/h"
        )
        lines = [f"{config.WEATHER_LOCATION}天气", current_text]
        for index, label in enumerate(("今天", "明天")):
            code = daily["weather_code"][index]
            low = daily["temperature_2m_min"][index]
            high = daily["temperature_2m_max"][index]
            rain = daily["precipitation_probability_max"][index]
            lines.append(
                f"{label} {dates[index]}：{WEATHER_CODES.get(code, '未知天气')}，"
                f"{low}~{high}°C，降水概率 {rain}%"
            )
        return "\n".join(lines)

    @staticmethod
    def _geocode(query: str):
        response = requests.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={"name": query, "count": 1, "language": "zh", "format": "json"},
            timeout=config.WEATHER_TIMEOUT,
        )
        response.raise_for_status()
        results = response.json().get("results", [])
        return results[0] if results else None
