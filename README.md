# 智能天气穿搭助手

一个使用 Flask 构建的交互式网页应用，根据天气、气温与风力信息提供美观简约的穿搭建议。

## 快速开始

1. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```
2. 启动网页应用：
   ```bash
   python test.py
   ```
3. 在浏览器中访问 [http://localhost:5000](http://localhost:5000)，输入天气信息即可获取智能穿搭推荐。

## 逻辑复用

如果只想在脚本或其他应用中复用穿搭算法，可导入 `weather_assistant.WeatherAssistant` 类，并调用 `suggest_outfit` 方法。

## 开发检查

提交代码前，可执行以下命令确认脚本无语法错误：
```bash
python -m compileall .
```
