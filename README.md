# 🏖️ 旅行计划生成助手 (Travel Assistant)

一个基于 Flask 的智能旅行助手 Web 应用，提供天气查询、行程规划、个性化推荐、预算估算等功能。

## ✨ 主要功能

- 🌤️ **天气查询与趋势分析** — 接入 WeatherAPI.com 实时数据
- 🗺️ **智能行程规划** — 自动生成多日旅行计划
- 🎯 **个性化推荐** — 基于用户画像的旅行建议
- 💰 **预算估算** — 根据城市/天数/风格估算费用
- 🛡️ **行程守护者** — 行前预判 + 行中实时监控 + 行后总结
- 👤 **旅行人格画像引擎** — 7维用户模型，三层偏好学习
- 📊 **数据看板** — 可视化天气数据与告警统计
- 📝 **周报/日报自动生成**

## 🚀 快速开始

### 前提条件

- Python 3.8 或更高版本
- 免费注册以下 API Key：
  - [DeepSeek API](https://platform.deepseek.com/) — LLM 大模型
  - [WeatherAPI.com](https://www.weatherapi.com/) — 天气数据（免费100万次/月）

### 一键启动（Windows）

双击运行 `run.bat`，脚本会自动完成环境配置并启动服务。

### 手动安装

```bash
# 1. 克隆或下载项目
cd travel-assistant

# 2. 创建虚拟环境
python -m venv .venv

# 3. 激活虚拟环境
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# 4. 安装依赖
pip install -r requirements.txt

# 5. 配置 API Key
copy .env.example .env
# 编辑 .env 文件，填入你的 API Key

# 6. 启动服务
python app.py
```

### 访问

打开浏览器访问：**http://localhost:5000**

## 📁 项目结构

```
travel-assistant/
├── app.py              # Flask 主应用
├── config.py           # 配置文件（从环境变量读取）
├── run.bat             # 一键启动脚本（Windows）
├── .env.example        # 环境变量模板
├── requirements.txt    # Python 依赖
├── services/           # 业务服务模块
│   ├── weather_service.py
│   ├── itinerary_service.py
│   ├── recommendation_service.py
│   ├── budget_service.py
│   ├── persona_service.py
│   ├── trip_guardian_service.py
│   └── ...
├── templates/          # HTML 模板
├── static/             # CSS/JS 静态文件
├── data/               # JSON 数据文件
└── knowledge/          # 知识库文本
```

## 🔧 配置说明

所有配置通过 `.env` 文件管理（基于 `.env.example` 创建）：

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `OPENAI_API_KEY` | DeepSeek API Key | - |
| `OPENAI_BASE_URL` | API 地址 | `https://api.deepseek.com` |
| `WEATHER_API_KEY` | WeatherAPI Key | - |
| `FLASK_HOST` | 监听地址 | `0.0.0.0` |
| `FLASK_PORT` | 端口号 | `5000` |
| `FLASK_DEBUG` | 调试模式 | `true` |

## 🌍 跨机器运行

本项目已修复所有可移植性问题：

- ✅ **API Key 通过环境变量管理** — 不硬编码在代码中
- ✅ **文件路径使用绝对路径** — 从任何目录启动都能正确找到数据文件
- ✅ **一键启动脚本** — 自动创建虚拟环境、安装依赖、启动服务
- ✅ **`.env.example` 模板** — 新用户只需复制并填入自己的 Key
- ✅ **`.gitignore` 保护** — 防止 API Key 泄露
