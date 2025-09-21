"""核心逻辑：根据天气信息生成穿搭建议。"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Tuple


@dataclass(frozen=True)
class _RecommendationTemplate:
    """模板，用于描述某种天气下的基础穿衣建议。"""

    outfit: str
    accessories: Tuple[str, ...] = ()
    tips: Tuple[str, ...] = ()


@dataclass
class OutfitRecommendation:
    """具体的穿衣推荐结果。"""

    outfit: str
    accessories: List[str] = field(default_factory=list)
    tips: List[str] = field(default_factory=list)

    def format(self) -> str:
        """格式化穿衣建议，方便展示。"""

        lines: List[str] = [f"推荐穿搭：{self.outfit}"]
        if self.accessories:
            lines.append("建议搭配：" + "、".join(self.accessories))
        if self.tips:
            lines.append("贴心提示：" + "；".join(self.tips))
        return "\n".join(lines)

    def to_dict(self) -> Dict[str, List[str] | str]:
        """转换为便于序列化的结构。"""

        data = asdict(self)
        return data


class WeatherAssistant:
    """智能天气助手，可以根据不同天气给出穿搭建议。"""

    #: 常见天气的别名，用于提升识别率。
    _ALIASES: Dict[str, str] = {
        "晴": "sunny",
        "晴天": "sunny",
        "晴朗": "sunny",
        "多云": "cloudy",
        "阴": "cloudy",
        "阴天": "cloudy",
        "雨": "rainy",
        "下雨": "rainy",
        "小雨": "rainy",
        "大雨": "rainy",
        "雷阵雨": "storm",
        "暴雨": "storm",
        "雪": "snowy",
        "下雪": "snowy",
        "大雪": "snowy",
        "小雪": "snowy",
        "雾": "foggy",
        "雾霾": "foggy",
        "风": "windy",
        "大风": "windy",
        "沙尘": "windy",
        "沙尘暴": "windy",
    }

    def __init__(self) -> None:
        self._templates: Dict[str, _RecommendationTemplate] = {
            "sunny": _RecommendationTemplate(
                "轻薄长袖或短袖上衣，搭配舒适长裤或裙装",
                ("太阳镜", "防晒霜"),
                ("中午紫外线较强时尽量戴帽子",),
            ),
            "cloudy": _RecommendationTemplate(
                "薄外套配长裤，内搭透气上衣",
                ("轻便运动鞋",),
                ("天气多变，出门前留意是否会转雨",),
            ),
            "rainy": _RecommendationTemplate(
                "防水外套或带帽雨衣，搭配快干长裤",
                ("雨伞", "防水鞋"),
                ("尽量避免穿布鞋，回家后及时烘干衣物",),
            ),
            "storm": _RecommendationTemplate(
                "防水风衣加保暖内搭",
                ("长筒雨靴", "防水背包"),
                ("尽量减少外出，注意雷电安全",),
            ),
            "snowy": _RecommendationTemplate(
                "厚实羽绒服或呢大衣，内搭羊毛衫",
                ("防滑雪地靴", "保暖手套"),
                ("外出前在鞋底贴防滑贴，注意路面结冰",),
            ),
            "foggy": _RecommendationTemplate(
                "保暖外套配长裤",
                ("口罩", "护目镜"),
                ("雾霾天尽量减少户外运动，回家及时清洁面部",),
            ),
            "windy": _RecommendationTemplate(
                "防风外套配长裤",
                ("围巾",),
                ("骑行或长时间户外活动时注意防风保暖",),
            ),
            "default": _RecommendationTemplate(
                "舒适的分层穿搭，如 T 恤配开衫",
                ("随身携带一件薄外套以防温差",),
                ("留意实时天气预报，适时增减衣物",),
            ),
        }

    def suggest_outfit(
        self,
        weather: str,
        temperature: Optional[float] = None,
        wind_speed: Optional[float] = None,
    ) -> OutfitRecommendation:
        """根据天气、气温和风力情况生成穿衣建议。"""

        if not weather or not weather.strip():
            raise ValueError("weather 不能为空")

        normalized_weather = self._normalize_weather(weather)
        template = self._templates.get(normalized_weather, self._templates["default"])
        accessories = list(template.accessories)
        tips = list(template.tips)
        outfit = template.outfit

        if temperature is not None:
            outfit, accessories, tips = self._adjust_by_temperature(
                temperature, outfit, accessories, tips
            )

        if wind_speed is not None:
            tips = self._adjust_by_wind(wind_speed, tips, accessories)

        return OutfitRecommendation(outfit=outfit, accessories=accessories, tips=tips)

    def _normalize_weather(self, weather: str) -> str:
        key = weather.strip().lower()
        return self._ALIASES.get(key, key)

    def _adjust_by_temperature(
        self,
        temperature: float,
        outfit: str,
        accessories: List[str],
        tips: List[str],
    ) -> Tuple[str, List[str], List[str]]:
        """根据气温调整穿搭。"""

        if temperature <= 5:
            outfit = "保暖羽绒服或厚呢大衣，内搭羊毛衫与保暖裤"
            if "保暖帽" not in accessories:
                accessories.extend(["保暖帽", "围巾"])
            tips.append("室内外温差大时注意及时增减衣物")
        elif temperature <= 15:
            outfit = "针织衫或卫衣外搭中等厚度外套，下装长裤"
            if "薄围巾" not in accessories:
                accessories.append("薄围巾")
            tips.append("早晚偏凉，可准备一件轻薄内搭")
        elif temperature >= 28:
            outfit = "透气短袖或无袖上衣，搭配短裤或轻薄长裤"
            if "遮阳帽" not in accessories:
                accessories.append("遮阳帽")
            tips.append("多喝水，避免长时间暴晒")
        elif temperature >= 22:
            tips.append("气温较高，选择吸汗面料会更舒适")
        else:
            tips.append("气温适中，保持分层穿搭以便调节")

        return outfit, accessories, tips

    def _adjust_by_wind(
        self,
        wind_speed: float,
        tips: List[str],
        accessories: List[str],
    ) -> List[str]:
        """根据风力调整提示。"""

        if wind_speed >= 10:
            if "防风外套" not in accessories:
                accessories.append("防风外套")
            tips.append("风力较大，外出时注意防风并保护好头部")
        elif wind_speed >= 5:
            tips.append("有明显风感，骑行或长时间户外活动时注意防风")
        return tips


def parse_optional_float(value: str) -> Optional[float]:
    """将字符串转换为浮点数，空值返回 None。"""

    value = value.strip()
    if not value:
        return None
    try:
        return float(value)
    except ValueError as exc:  # noqa: PERF203 - 简单脚本，不考虑极致性能
        raise ValueError("请输入有效的数字") from exc
