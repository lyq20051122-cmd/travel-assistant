"""
配置文件 - 所有配置项从环境变量读取
其他用户在部署时只需复制 .env.example 为 .env 并填入自己的 API Key 即可运行
"""
import os
from dotenv import load_dotenv

# 加载 .env 文件（如果存在）
load_dotenv()

# LLM 配置 (DeepSeek / OpenAI 兼容接口)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "your-api-key-here")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.deepseek.com/v1")

# WeatherAPI.com 配置
# 免费额度：100万次/月，注册地址：https://www.weatherapi.com/
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY", "your-weather-api-key-here")

# Flask 配置
FLASK_HOST = os.getenv("FLASK_HOST", "0.0.0.0")
FLASK_PORT = int(os.getenv("FLASK_PORT", "5000"))
FLASK_DEBUG = os.getenv("FLASK_DEBUG", "true").lower() == "true"
