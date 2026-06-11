# 天气API使用说明

## 推荐的天气API：WeatherAPI.com

### 为什么选择 WeatherAPI.com？

| 特点 | 说明 |
|------|------|
| 免费额度 | 100万次/月 |
| 数据完整性 | 支持实时天气、预报、空气质量、天气预警 |
| 稳定性 | 全球多个服务器节点，99.9%可用性 |
| 响应速度 | 平均响应时间 < 200ms |
| 中文支持 | 支持中文语言 |

### 注册步骤

1. 访问 [WeatherAPI.com](https://www.weatherapi.com/)
2. 点击右上角 "Sign Up" 注册账号
3. 注册成功后登录，进入 Dashboard
4. 在左侧菜单找到 "API Key" 或 "My Keys"
5. 复制您的免费 API Key

### 配置步骤

1. 打开 `config.py` 文件
2. 将 `YOUR_WEATHER_API_KEY` 替换为您的实际API Key

```python
# config.py
WEATHER_API_KEY = "您的实际API Key"
```

### API功能一览

WeatherAPI.com 提供以下免费功能：

| 功能 | API端点 | 说明 |
|------|---------|------|
| 实时天气 | `/current.json` | 温度、湿度、风速、紫外线等 |
| 天气预报 | `/forecast.json` | 未来1-10天预报 |
| 空气质量 | `/air_quality.json` | AQI、PM2.5等指标 |
| 历史天气 | `/history.json` | 过去7天历史数据 |
| 搜索 | `/search.json` | 城市搜索 |

### 测试天气API

运行以下命令测试API是否正常工作：

```bash
cd e:\pythonproject\travel-assistant
python test_weather.py
```

### 常见问题

**Q: API Key无效？**
A: 请确保您复制的是完整的API Key，没有多余的空格或引号。

**Q: 超出免费额度？**
A: 免费版每月100万次调用，个人使用完全足够。如果超出，可以等待次月重置或升级付费版。

**Q: 城市搜索不到？**
A: WeatherAPI使用英文城市名，请使用拼音，如 "guangzhou" 而不是 "广州"。

### 代码示例

```python
import requests

API_KEY = "YOUR_API_KEY"
CITY = "beijing"

url = f"https://api.weatherapi.com/v1/current.json?key={API_KEY}&q={CITY}&lang=zh"
response = requests.get(url)
data = response.json()

print(f"城市: {data['location']['name']}")
print(f"天气: {data['current']['condition']['text']}")
print(f"温度: {data['current']['temp_c']}°C")
```

### 备用API

如果 WeatherAPI.com 不可用，可以考虑：

1. **OpenWeatherMap** - https://openweathermap.org/api
   - 免费额度：60次/分钟
   
2. **和风天气** - https://dev.qweather.com/
   - 国内访问稳定

### 注意事项

- 请妥善保管您的API Key，不要泄露给他人
- 不要在公开场合（如GitHub）提交包含API Key的代码
- 建议在生产环境中使用环境变量存储敏感信息