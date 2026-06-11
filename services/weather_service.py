import requests
import json
from config import WEATHER_API_KEY
from services.data_storage import save_weather_data

# WeatherAPI.com 配置
WEATHER_API_BASE = "https://api.weatherapi.com/v1"


def get_weather(city):
    """
    获取城市天气信息（支持多指标数据）
    WeatherAPI.com 免费额度：100万次/月
    """
    try:
        # 构建API URL
        url = f"{WEATHER_API_BASE}/current.json"
        params = {
            "key": WEATHER_API_KEY,
            "q": city,
            "lang": "zh"
        }
        
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        if response.status_code != 200 or "error" in data:
            error_msg = data.get("error", {}).get("message", "未知错误")
            return f"无法获取{city}的天气信息：{error_msg}"
        
        # 解析天气数据
        location = data["location"]
        current = data["current"]
        
        city_name = location["name"]
        country = location["country"]
        region = location["region"]
        
        # 基础天气信息
        temp_c = current["temp_c"]
        feelslike_c = current["feelslike_c"]
        humidity = current["humidity"]
        wind_kph = current["wind_kph"]
        wind_dir = current["wind_dir"]
        pressure_mb = current["pressure_mb"]
        precip_mm = current["precip_mm"]
        visibility_km = current["vis_km"]
        uv = current["uv"]
        condition_text = current["condition"]["text"]
        condition_icon = current["condition"]["icon"]
        
        # 构建详细天气数据（用于存储和分析）
        weather_data = {
            "temperature": temp_c,
            "feels_like": feelslike_c,
            "humidity": humidity,
            "wind_speed": wind_kph,
            "wind_direction": wind_dir,
            "pressure": pressure_mb,
            "precipitation": precip_mm,
            "visibility": visibility_km,
            "uv": uv,
            "condition": condition_text,
            "condition_code": current["condition"]["code"]
        }
        
        # 保存天气数据用于历史分析
        try:
            save_weather_data(city_name, weather_data)
        except Exception as e:
            print(f"保存天气数据失败: {e}")
        
        # 生成返回文本
        return f"""
{city_name}当前天气详情：

🌤️ 天气状况：{condition_text}
🌡️ 温度：{temp_c}°C（体感 {feelslike_c}°C）
💧 湿度：{humidity}%
🌬️ 风速：{wind_kph} km/h（{wind_dir}）
📊 气压：{pressure_mb} mb
🌧️ 降水量：{precip_mm} mm
👁️ 能见度：{visibility_km} km
☀️ 紫外线指数：{uv}

📍 位置：{region}, {country}
"""

    except requests.exceptions.Timeout:
        return "天气查询超时，请稍后重试"
    except requests.exceptions.RequestException as e:
        print(f"网络请求失败: {e}")
        return "天气查询失败，请检查网络连接"
    except Exception as e:
        print(f"天气查询失败: {e}")
        return "天气查询失败，请稍后重试"


def get_weather_forecast(city, days=3):
    """
    获取天气预报
    days: 预报天数 (1-10)
    """
    try:
        url = f"{WEATHER_API_BASE}/forecast.json"
        params = {
            "key": WEATHER_API_KEY,
            "q": city,
            "days": days,
            "lang": "zh"
        }
        
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        if response.status_code != 200 or "error" in data:
            return None
        
        city_name = data["location"]["name"]
        forecast_days = data["forecast"]["forecastday"]
        
        result = f"{city_name}天气预报：\n\n"
        
        for day in forecast_days:
            date = day["date"]
            day_info = day["day"]
            astro = day["astro"]
            
            result += f"📅 {date}\n"
            result += f"   天气：{day_info['condition']['text']}\n"
            result += f"   最高/最低温度：{day_info['maxtemp_c']}°C / {day_info['mintemp_c']}°C\n"
            result += f"   平均温度：{day_info['avgtemp_c']}°C\n"
            result += f"   降水概率：{day_info['daily_chance_of_rain']}%\n"
            result += f"   紫外线指数：{day_info['uv']}\n"
            result += f"   日出/日落：{astro['sunrise']} / {astro['sunset']}\n"
            result += "\n"
        
        return result.strip()
        
    except Exception as e:
        print(f"天气预报查询失败: {e}")
        return None


def get_air_quality(city):
    """
    获取空气质量数据
    """
    try:
        url = f"{WEATHER_API_BASE}/air_quality.json"
        params = {
            "key": WEATHER_API_KEY,
            "q": city
        }
        
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        if response.status_code != 200 or "error" in data:
            return None
        
        aq = data["current"]["air_quality"]
        
        result = f"{data['location']['name']}空气质量：\n\n"
        result += f"🌫️ AQI指数：{aq['us-epa-index']}（美国标准）\n"
        result += f"   PM2.5：{aq['pm2_5']} μg/m³\n"
        result += f"   PM10：{aq['pm10']} μg/m³\n"
        result += f"   SO₂：{aq['so2']} μg/m³\n"
        result += f"   NO₂：{aq['no2']} μg/m³\n"
        result += f"   O₃：{aq['o3']} μg/m³\n"
        result += f"   CO：{aq['co']} mg/m³\n"
        
        # AQI等级说明
        aqi_index = aq['us-epa-index']
        aqi_desc = {
            1: "优",
            2: "良",
            3: "中等",
            4: "对敏感人群不健康",
            5: "不健康",
            6: "非常不健康",
            7: "危险"
        }
        result += f"\n空气质量等级：{aqi_index} - {aqi_desc.get(aqi_index, '未知')}"
        
        return result
        
    except Exception as e:
        print(f"空气质量查询失败: {e}")
        return None


def get_weather_alerts(city):
    """
    获取天气预警信息（高级功能，需要付费订阅）
    这里返回模拟数据用于演示
    """
    try:
        url = f"{WEATHER_API_BASE}/forecast.json"
        params = {
            "key": WEATHER_API_KEY,
            "q": city,
            "days": 3,
            "alerts": "yes"
        }
        
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        if response.status_code != 200 or "error" in data:
            return None
        
        alerts_data = data.get("alerts", {}).get("alert", [])
        
        if not alerts_data:
            return None
        
        result = f"{city}天气预警：\n\n"
        for alert in alerts_data:
            result += f"⚠️ {alert.get('headline', '天气预警')}\n"
            result += f"   严重程度：{alert.get('severity', '未知')}\n"
            result += f"   类别：{alert.get('categories', '未知')}\n"
            result += f"   有效期：{alert.get('effective', '未知')}\n"
            result += f"   描述：{alert.get('desc', '暂无')}\n\n"
        
        return result
        
    except Exception as e:
        print(f"预警查询失败: {e}")
        return None


# 天气指数和建议
WEATHER_TIPS = {
    "uv_high": {
        "condition": lambda d: d.get("uv", 0) >= 6,
        "tip": "紫外线强度较高，建议涂抹防晒霜，佩戴太阳镜和遮阳帽"
    },
    "temp_high": {
        "condition": lambda d: d.get("temperature", 0) >= 35,
        "tip": "高温天气，请注意防暑降温，多补充水分，避免长时间户外活动"
    },
    "temp_low": {
        "condition": lambda d: d.get("temperature", 0) <= 0,
        "tip": "气温较低，请注意保暖，携带保暖衣物"
    },
    "rain": {
        "condition": lambda d: d.get("precipitation", 0) > 0 or "雨" in d.get("condition", ""),
        "tip": "有降雨天气，请携带雨具，注意道路湿滑"
    },
    "wind_high": {
        "condition": lambda d: d.get("wind_speed", 0) >= 40,
        "tip": "风力较大，请注意高空坠物，远离广告牌等临时建筑"
    },
    "aqi_poor": {
        "condition": lambda d: d.get("aqi", 0) >= 4,
        "tip": "空气质量较差，建议佩戴口罩，减少户外活动时间"
    }
}

def get_weather_advice(city):
    """
    根据天气数据生成旅行建议
    """
    try:
        url = f"{WEATHER_API_BASE}/current.json"
        params = {
            "key": WEATHER_API_KEY,
            "q": city,
            "lang": "zh"
        }
        
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        if response.status_code != 200 or "error" in data:
            return None
        
        current = data["current"]
        weather_data = {
            "temperature": current["temp_c"],
            "humidity": current["humidity"],
            "wind_speed": current["wind_kph"],
            "precipitation": current["precip_mm"],
            "uv": current["uv"],
            "condition": current["condition"]["text"]
        }
        
        city_name = data["location"]["name"]
        result = f"{city_name}旅行建议：\n\n"
        
        # 检查各项条件并生成建议
        advice_list = []
        
        for tip_key, tip_info in WEATHER_TIPS.items():
            if tip_info["condition"](weather_data):
                advice_list.append(f"• {tip_info['tip']}")
        
        # 根据天气状况推荐活动
        condition = weather_data["condition"]
        temp = weather_data["temperature"]
        
        if any(x in condition for x in ["晴", "多云"]):
            if 15 <= temp <= 25:
                advice_list.append("• 天气宜人，非常适合户外游览和拍照")
            elif temp > 25:
                advice_list.append("• 天气较热，建议携带遮阳伞，安排室内活动或水上项目")
        
        if not advice_list:
            advice_list.append("• 天气条件良好，适合各类旅行活动")
        
        result += "\n".join(advice_list)
        
        return result
        
    except Exception as e:
        print(f"建议生成失败: {e}")
        return None