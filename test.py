"""Web 版智能天气穿搭助手。"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

import requests
from flask import Flask, jsonify, render_template, request

from weather_assistant import (
    WeatherAssistant,
    describe_open_meteo_code,
    parse_optional_float,
)

app = Flask(__name__)
assistant = WeatherAssistant()


@app.route("/")
def index() -> str:
    """展示主页面。"""

    return render_template("index.html")


@app.post("/api/recommend")
def recommend() -> Tuple[Any, int]:
    """根据请求参数返回穿衣建议。"""

    payload: Dict[str, Any] = request.get_json(silent=True) or {}
    if not payload and request.form:
        payload = request.form.to_dict(flat=True)

    weather = str(payload.get("weather", ""))
    temperature_input = payload.get("temperature")
    wind_input = payload.get("windSpeed")

    errors: Dict[str, str] = {}
    temperature = None
    wind_speed = None

    if not weather.strip():
        errors["weather"] = "请输入天气描述"

    try:
        temperature = _normalize_maybe_number(temperature_input)
    except ValueError as exc:
        errors["temperature"] = str(exc)

    try:
        wind_speed = _normalize_maybe_number(wind_input)
    except ValueError as exc:
        errors["windSpeed"] = str(exc)

    if errors:
        return jsonify({"success": False, "errors": errors}), 400

    try:
        recommendation = assistant.suggest_outfit(weather, temperature, wind_speed)
    except ValueError as exc:
        return jsonify({"success": False, "errors": {"weather": str(exc)}}), 400

    return jsonify({"success": True, "data": recommendation.to_dict()}), 200


@app.post("/api/auto-forecast")
def auto_forecast() -> Tuple[Any, int]:
    """根据经纬度自动查询未来七天的天气与穿搭建议。"""

    payload: Dict[str, Any] = request.get_json(silent=True) or {}
    latitude_raw = payload.get("latitude")
    longitude_raw = payload.get("longitude")

    errors: Dict[str, str] = {}
    try:
        latitude = _normalize_coordinate(latitude_raw)
    except ValueError as exc:
        errors["latitude"] = str(exc)
        latitude = None

    try:
        longitude = _normalize_coordinate(longitude_raw)
    except ValueError as exc:
        errors["longitude"] = str(exc)
        longitude = None

    if errors:
        return jsonify({"success": False, "errors": errors}), 400

    try:
        forecast_raw = _fetch_forecast(latitude, longitude)
    except RuntimeError as exc:
        return (
            jsonify({"success": False, "errors": {"general": str(exc)}}),
            502,
        )

    try:
        days = _build_forecast_days(forecast_raw)
    except ValueError as exc:
        return (
            jsonify({"success": False, "errors": {"general": str(exc)}}),
            502,
        )

    if not days:
        return (
            jsonify(
                {
                    "success": False,
                    "errors": {"general": "暂未获取到天气数据，请稍后重试。"},
                }
            ),
            502,
        )

    response_payload = {
        "location": {
            "latitude": latitude,
            "longitude": longitude,
            "timezone": forecast_raw.get("timezone"),
        },
        "days": days,
    }

    return jsonify({"success": True, "data": response_payload}), 200


def _normalize_maybe_number(value: Any) -> float | None:
    """解析可能为字符串的数值，保持空值为 None。"""

    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    return parse_optional_float(str(value))


def _normalize_coordinate(value: Any) -> float:
    """解析地理坐标，确保为浮点数。"""

    if value in (None, ""):
        raise ValueError("未能获取定位信息")

    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("定位数据格式有误") from exc


def _fetch_forecast(latitude: float, longitude: float) -> Dict[str, Any]:
    """调用 Open-Meteo 接口获取七天预报。"""

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "daily": "weathercode,temperature_2m_max,temperature_2m_min,windspeed_10m_max",
        "timezone": "auto",
        "forecast_days": 7,
    }
    try:
        response = requests.get(
            "https://api.open-meteo.com/v1/forecast", params=params, timeout=10
        )
        response.raise_for_status()
    except requests.RequestException as exc:  # pragma: no cover - 需网络环境
        raise RuntimeError("天气服务暂时不可用，请稍后再试。") from exc

    try:
        data: Dict[str, Any] = response.json()
    except ValueError as exc:  # pragma: no cover - 第三方异常
        raise RuntimeError("天气服务返回了无效的数据。") from exc

    return data


def _build_forecast_days(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """将天气预报数据转换为前端可用的结构。"""

    daily = data.get("daily")
    if not isinstance(daily, dict):
        raise ValueError("天气服务暂未提供未来七天天气数据。")

    dates = list(daily.get("time") or [])
    weather_codes = list(daily.get("weathercode") or [])
    temps_max = list(daily.get("temperature_2m_max") or [])
    temps_min = list(daily.get("temperature_2m_min") or [])
    winds = list(daily.get("windspeed_10m_max") or [])

    days: List[Dict[str, Any]] = []
    for index, date_str in enumerate(dates[:7]):
        code_raw = weather_codes[index] if index < len(weather_codes) else None
        category, description = describe_open_meteo_code(code_raw)

        max_temp = _safe_get_float(temps_max, index)
        min_temp = _safe_get_float(temps_min, index)
        wind_speed = _safe_get_float(winds, index)

        averaged_temp = _average_temperature(max_temp, min_temp)

        recommendation = assistant.suggest_outfit(
            category, temperature=averaged_temp, wind_speed=wind_speed
        )

        try:
            weather_code = int(code_raw) if code_raw is not None else None
        except (TypeError, ValueError):  # pragma: no cover - 容错逻辑
            weather_code = None

        days.append(
            {
                "date": date_str,
                "weather_text": description,
                "weather_code": weather_code,
                "temperature_max": max_temp,
                "temperature_min": min_temp,
                "wind_speed": wind_speed,
                "recommendation": recommendation.to_dict(),
            }
        )

    return days


def _average_temperature(max_temp: float | None, min_temp: float | None) -> float | None:
    """根据最高与最低气温计算平均值。"""

    temps = [value for value in (max_temp, min_temp) if value is not None]
    if not temps:
        return None
    return sum(temps) / len(temps)


def _safe_get_float(values: List[Any], index: int) -> float | None:
    """安全地从列表中取出浮点值。"""

    try:
        value = values[index]
    except (IndexError, TypeError):
        return None

    if value in (None, ""):
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
