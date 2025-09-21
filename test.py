"""Web 版智能天气穿搭助手。"""

from __future__ import annotations

from typing import Any, Dict, Tuple

from flask import Flask, jsonify, render_template, request

from weather_assistant import WeatherAssistant, parse_optional_float

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


def _normalize_maybe_number(value: Any) -> float | None:
    """解析可能为字符串的数值，保持空值为 None。"""

    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    return parse_optional_float(str(value))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
