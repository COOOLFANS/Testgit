# 智能天气穿搭助手

一个使用 Flask 构建的交互式网页应用，根据天气、气温与风力信息提供美观简约的穿搭建议，并支持自动定位你当前位置的未来 7 天天气以生成穿搭日历。

## 快速开始

1. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```
2. 启动网页应用：
   ```bash
   python test.py
   ```
3. 在浏览器中访问 [http://localhost:5000](http://localhost:5000)，允许浏览器定位后即可自动获取未来 7 天的天气与穿搭建议；你也可以手动输入天气信息获取即时推荐。

> 提示：自动天气功能基于 [Open-Meteo](https://open-meteo.com/) 公共接口，需要外网访问权限以及浏览器定位许可。

## 逻辑复用

如果只想在脚本或其他应用中复用穿搭算法，可导入 `weather_assistant.WeatherAssistant` 类，并调用 `suggest_outfit` 方法。

## 开发检查

提交代码前，可执行以下命令确认脚本无语法错误：
```bash
python -m compileall .
```
