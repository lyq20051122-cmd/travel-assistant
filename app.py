from flask import Flask, render_template, request, jsonify, send_file, Response
from datetime import datetime, timedelta
import json
import os
import random
import requests

from services.llm_service import ask_llm
from services.weather_service import get_weather, get_weather_forecast, get_weather_advice
from services.memory_service import save_memory, load_memory
from services.conversation_service import save_conversation, get_conversation_history, clear_conversation, get_recent_conversations, get_conversation_by_date
from services.city_service import get_all_cities, get_city_by_id, search_cities
from services.data_storage import load_weather_history, load_alert_history, save_weather_data, save_alert
from services.anomaly_detection import check_weather_anomalies, get_active_alerts, get_alert_summary
from services.linkage_service import apply_linkage_rules, get_travel_recommendation_summary
from services.report_service import generate_weekly_report, generate_daily_brief, save_report_to_file
from services.itinerary_service import generate_itinerary
from services.recommendation_service import get_personalized_recommendations
from services.budget_service import estimate_budget
from services.alert_service import alert_service, schedule_daily_weather_brief, generate_travel_reminder, check_trip_conflicts

from intents.intent_recognizer import recognize_intent
from intents.safety_check import safety_check

from services.preference_extractor import extract_preferences
from services.simple_response import get_greeting_response, get_thanks_response

# 导入配置
from config import WEATHER_API_KEY, FLASK_HOST, FLASK_PORT, FLASK_DEBUG

# 🆕 旅行回顾卡片服务
from services.review_card_service import (
    generate_review_card, list_cards_for_user, get_card,
    export_card_markdown, delete_card, get_available_trips
)

# 新增：旅行人格画像引擎 & 主动式行程守护者（作业9特色功能）
from services.persona_service import persona_service, TravelPersona
from services.trip_guardian_service import trip_guardian_service, classify_activity, calculate_conflict_index

# 城市ID映射
CITY_IDS = {
    '北京': 'beijing',
    '上海': 'shanghai',
    '广州': 'guangzhou',
    '深圳': 'shenzhen',
    '杭州': 'hangzhou',
    '成都': 'chengdu',
    '重庆': 'chongqing',
    '西安': 'xian',
    '南京': 'nanjing',
    '武汉': 'wuhan',
    '苏州': 'suzhou',
    '青岛': 'qingdao',
    '厦门': 'xiamen',
    '福州': 'fuzhou',
    '昆明': 'kunming',
    '丽江': 'lijiang'
}

app = Flask(__name__)

# 季节推荐城市映射
SEASON_CITIES = {
    'spring': ['hangzhou', 'wuhan', 'suzhou', 'kunming'],  # 春季：杭州赏花、武汉樱花、苏州园林、昆明春城
    'summer': ['qingdao', 'xiamen', 'chongqing', 'lijiang'],  # 夏季：青岛海滨、厦门海岛、重庆避暑、丽江清凉
    'autumn': ['xian', 'beijing', 'chengdu', 'nanjing'],  # 秋季：西安秋景、北京红叶、成都桂香、南京梧桐
    'winter': ['shenzhen', 'guangzhou', 'xiamen', 'kunming']  # 冬季：深圳温暖、广州繁花、厦门海岛、昆明如春
}

def extract_city_from_message(message):
    common_cities = ["北京", "上海", "广州", "深圳", "杭州", "成都", "重庆", "西安", "南京", "武汉", "苏州", "天津", "郑州", "长沙", "青岛", "大连", "厦门", "昆明", "三亚", "桂林", "拉萨", "乌鲁木齐", "哈尔滨", "沈阳", "长春", "济南", "福州", "合肥", "南昌", "石家庄", "太原", "呼和浩特", "兰州", "西宁", "银川", "南宁", "贵阳", "海口", "东京", "大阪", "京都", "名古屋", "横滨", "首尔", "釜山", "曼谷", "新加坡", "吉隆坡", "雅加达", "马尼拉", "河内", "胡志明", "金边", "仰光", "加德满都", "新德里", "孟买", "班加罗尔", "伊斯兰堡", "卡拉奇", "德黑兰", "巴格达", "利雅得", "迪拜", "多哈", "科威特城", "安曼", "贝鲁特", "耶路撒冷", "开罗", "亚历山大", "拉各斯", "约翰内斯堡", "开普敦", "内罗毕", "阿克拉", "达喀尔", "突尼斯", "阿尔及尔", "拉巴特", "卡萨布兰卡", "的黎波里", "伊斯坦布尔", "安卡拉", "雅典", "罗马", "米兰", "威尼斯", "佛罗伦萨", "那不勒斯", "都灵", "博洛尼亚", "马德里", "巴塞罗那", "塞维利亚", "瓦伦西亚", "里斯本", "波尔图", "巴黎", "里昂", "马赛", "尼斯", "里尔", "柏林", "慕尼黑", "汉堡", "法兰克福", "科隆", "杜塞尔多夫", "斯图加特", "维也纳", "苏黎世", "日内瓦", "阿姆斯特丹", "鹿特丹", "布鲁塞尔", "安特卫普", "伦敦", "曼彻斯特", "伯明翰", "爱丁堡", "格拉斯哥", "都柏林", "哥本哈根", "斯德哥尔摩", "奥斯陆", "赫尔辛基", "雷克雅未克", "莫斯科", "圣彼得堡", "华沙", "布拉格", "布达佩斯", "布加勒斯特", "索非亚", "贝尔格莱德", "萨格勒布", "卢布尔雅那", "布拉迪斯拉发", "维尔纽斯", "里加", "塔林", "基辅", "明斯克", "基希讷乌", "第比利斯", "埃里温", "巴库", "阿斯塔纳", "阿拉木图", "塔什干", "比什凯克", "杜尚别", "阿什哈巴德", "纽约", "洛杉矶", "芝加哥", "休斯顿", "旧金山", "西雅图", "波士顿", "迈阿密", "拉斯维加斯", "华盛顿", "费城", "达拉斯", "亚特兰大", "多伦多", "温哥华", "蒙特利尔", "墨西哥城", "布宜诺斯艾利斯", "圣保罗", "里约热内卢", "利马", "圣地亚哥", "波哥大", "加拉加斯", "蒙得维的亚", "亚松森", "拉巴斯", "基多", "悉尼", "墨尔本", "布里斯班", "珀斯", "阿德莱德", "奥克兰", "惠灵顿", "檀香山"]
    
    for city in common_cities:
        if city in message:
            return city
    
    return None

def get_current_season():
    month = datetime.now().month
    if month >= 3 and month <= 5:
        return 'spring'
    elif month >= 6 and month <= 8:
        return 'summer'
    elif month >= 9 and month <= 11:
        return 'autumn'
    else:
        return 'winter'

# 首页
@app.route("/")
def home():
    season_map = {
        'spring': '🌱 春季',
        'summer': '☀️ 夏季',
        'autumn': '🍂 秋季',
        'winter': '❄️ 冬季'
    }
    current_season = get_current_season()
    return render_template("index.html", current_season=season_map[current_season])

# 简洁版聊天页面（独立HTML）
@app.route("/simple-chat")
def simple_chat():
    html_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "travel_assistant.html")
    return send_file(html_path)

# 新增：旅游物品清单页面
@app.route("/checklist")
def checklist():
    return render_template("checklist.html")

# 新增：城市介绍页面
@app.route("/cities")
def cities():
    return render_template("cities.html")

# 新增：城市详情页面
@app.route("/city/<city_id>")
def city_detail(city_id):
    return render_template("city_detail.html", city_id=city_id)

# 新增：城市统计页面
@app.route("/city-stats")
def city_stats():
    return render_template("city_stats.html")

# 新增：天气趋势页面
@app.route("/weather-trend")
def weather_trend():
    return render_template("weather_trend.html")

# API：获取所有城市列表
@app.route("/api/cities", methods=["GET"])
def api_get_cities():
    try:
        cities = get_all_cities()
        return jsonify({
            "success": True,
            "cities": cities
        })
    except Exception as e:
        print("获取城市列表失败：", e)
        return jsonify({
            "success": False,
            "cities": []
        }), 500

# API：获取城市详情
@app.route("/api/city/<city_id>", methods=["GET"])
def api_get_city_detail(city_id):
    try:
        city = get_city_by_id(city_id)
        if city:
            return jsonify({
                "success": True,
                "city": city
            })
        else:
            return jsonify({
                "success": False,
                "message": "城市不存在"
            }), 404
    except Exception as e:
        print("获取城市详情失败：", e)
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

# API：搜索城市
@app.route("/api/search-cities", methods=["GET"])
def api_search_cities():
    try:
        keyword = request.args.get("keyword", "")
        if not keyword:
            return jsonify({
                "success": False,
                "message": "请输入搜索关键词"
            }), 400
        
        cities = search_cities(keyword)
        return jsonify({
            "success": True,
            "cities": cities
        })
    except Exception as e:
        print("搜索城市失败：", e)
        return jsonify({
            "success": False,
            "cities": []
        }), 500

# API：季节推荐城市
@app.route("/api/season-cities", methods=["GET"])
def api_season_cities():
    try:
        season = request.args.get("season", "")
        if season not in SEASON_CITIES:
            return jsonify({
                "success": False,
                "message": "无效的季节参数"
            }), 400
        
        city_ids = SEASON_CITIES[season]
        cities = []
        for city_id in city_ids:
            city = get_city_by_id(city_id)
            if city:
                cities.append(city)
        
        return jsonify({
            "success": True,
            "cities": cities
        })
    except Exception as e:
        print("获取季节推荐城市失败：", e)
        return jsonify({
            "success": False,
            "cities": []
        }), 500

# API：获取天气趋势数据
@app.route("/api/weather-trend", methods=["GET"])
def api_weather_trend():
    try:
        city = request.args.get("city", "北京")
        
        # 尝试使用WeatherAPI.com获取真实数据
        if WEATHER_API_KEY != "demo":
            try:
                # 调用WeatherAPI.com 7天预报API
                url = f"http://api.weatherapi.com/v1/forecast.json?key={WEATHER_API_KEY}&q={city}&days=7&aqi=no&alerts=no"
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                weather_data = response.json()
                
                if "forecast" in weather_data and "forecastday" in weather_data["forecast"]:
                    days = []
                    temperatures = []
                    humidities = []
                    conditions = []
                    
                    weekdays = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
                    
                    for day_data in weather_data["forecast"]["forecastday"]:
                        date_str = day_data["date"]
                        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                        days.append(weekdays[date_obj.weekday()])
                        temperatures.append(day_data["day"]["maxtemp_c"])
                        humidities.append(day_data["day"]["avghumidity"])
                        conditions.append(day_data["day"]["condition"]["text"])
                    
                    data = {
                        "success": True,
                        "city": city,
                        "days": days,
                        "temperatures": temperatures,
                        "humidities": humidities,
                        "conditions": conditions,
                        "avg_temp": round(sum(temperatures) / len(temperatures), 1),
                        "max_temp": max(temperatures),
                        "min_temp": min(temperatures)
                    }
                    return jsonify(data)
            except Exception as e:
                print("WeatherAPI.com调用失败，使用模拟数据：", e)
        
        # 如果API调用失败或没有配置API key，使用模拟数据
        days = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
        temperatures = []
        humidities = []
        conditions = []
        
        base_temp = {
            '北京': 20, '上海': 25, '广州': 28, '深圳': 28,
            '杭州': 23, '成都': 22, '重庆': 24, '西安': 21,
            '南京': 23, '武汉': 24, '苏州': 23, '青岛': 20,
            '厦门': 26, '福州': 27, '昆明': 18, '丽江': 16
        }
        
        base = base_temp.get(city, 22)
        
        for i in range(7):
            temp = base + random.randint(-3, 4)
            temperatures.append(temp)
            humidities.append(random.randint(40, 85))
            condition_list = ['晴', '多云', '阴', '小雨', '阵雨']
            conditions.append(random.choice(condition_list))
        
        data = {
            "success": True,
            "city": city,
            "days": days,
            "temperatures": temperatures,
            "humidities": humidities,
            "conditions": conditions,
            "avg_temp": round(sum(temperatures) / 7, 1),
            "max_temp": max(temperatures),
            "min_temp": min(temperatures)
        }
        
        return jsonify(data)
    
    except Exception as e:
        print("获取天气趋势失败：", e)
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

# 新增：天气数据看板页面
@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

# API：获取看板统计数据
@app.route("/api/dashboard/stats", methods=["GET"])
def api_dashboard_stats():
    try:
        history = load_weather_history()
        alerts = get_active_alerts()
        alert_summary = get_alert_summary()
        
        # 统计触发的规则
        active_rules = 0
        rule_details = {}
        for city, records in history.items():
            if records:
                latest_data = records[-1]["data"]
                rules = apply_linkage_rules(city, latest_data)
                active_rules += len(rules)
                for rule in rules:
                    rule_name = rule["rule_name"]
                    rule_details[rule_name] = rule_details.get(rule_name, 0) + 1
        
        # 统计总数据记录数
        total_records = sum(len(records) for records in history.values())
        
        # 计算记录详细数据
        today = datetime.now().strftime("%Y-%m-%d")
        week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        month_ago = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        
        today_records = 0
        week_records = 0
        month_records = 0
        
        for city, records in history.items():
            for record in records:
                timestamp = record["timestamp"]
                if timestamp.startswith(today):
                    today_records += 1
                if timestamp >= week_ago:
                    week_records += 1
                if timestamp >= month_ago:
                    month_records += 1
        
        # 计算平均每日记录
        active_days = len(set(record["timestamp"].split("T")[0] for city, records in history.items() for record in records))
        daily_avg = round(total_records / active_days) if active_days > 0 else 0
        
        record_details = {
            "today": today_records,
            "week": week_records,
            "month": month_records,
            "total": total_records,
            "activeCities": len(history),
            "dailyAvg": daily_avg
        }
        
        return jsonify({
            "success": True,
            "monitoredCities": len(history),
            "activeAlerts": len(alerts),
            "activeRules": active_rules,
            "dataRecords": total_records,
            "ruleDetails": rule_details,
            "recordDetails": record_details
        })
    except Exception as e:
        print("获取看板统计失败：", e)
        return jsonify({"success": False}), 500

# API：获取温度趋势
@app.route("/api/dashboard/temperature-trend", methods=["GET"])
def api_temperature_trend():
    try:
        history = load_weather_history()
        
        labels = []
        temperatures = []
        
        # 获取最近7天的温度趋势
        for i in range(7):
            date = (datetime.now() - timedelta(days=6-i)).strftime("%m-%d")
            labels.append(date)
            
            # 计算当天所有城市的平均温度
            day_temps = []
            for city, records in history.items():
                for record in records:
                    if record["timestamp"].startswith((datetime.now() - timedelta(days=6-i)).strftime("%Y-%m-%d")):
                        temp = record["data"].get("temperature")
                        if temp:
                            day_temps.append(temp)
            
            if day_temps:
                temperatures.append(round(sum(day_temps) / len(day_temps), 1))
            else:
                temperatures.append(None)
        
        return jsonify({
            "success": True,
            "labels": labels,
            "temperatures": temperatures
        })
    except Exception as e:
        print("获取温度趋势失败：", e)
        return jsonify({"success": False}), 500

# API：获取告警统计
@app.route("/api/dashboard/alert-summary", methods=["GET"])
def api_alert_summary():
    try:
        summary = get_alert_summary()
        
        type_counts = summary.get("type_counts", {})
        
        return jsonify({
            "success": True,
            "highTemp": type_counts.get("高温预警", 0),
            "heavyRain": type_counts.get("暴雨预警", 0),
            "poorAqi": type_counts.get("空气质量差预警", 0),
            "strongWind": type_counts.get("强风预警", 0),
            "other": summary.get("total", 0) - type_counts.get("高温预警", 0) - type_counts.get("暴雨预警", 0) - type_counts.get("空气质量差预警", 0) - type_counts.get("强风预警", 0)
        })
    except Exception as e:
        print("获取告警统计失败：", e)
        return jsonify({"success": False}), 500

# API：获取城市天气列表
@app.route("/api/dashboard/weather-list", methods=["GET"])
def api_weather_list():
    try:
        history = load_weather_history()
        
        cities = []
        for city, records in history.items():
            if records:
                latest = records[-1]["data"]
                cities.append({
                    "city": city,
                    "temperature": latest.get("temperature", "-"),
                    "condition": latest.get("condition", "未知"),
                    "humidity": latest.get("humidity", "-"),
                    "wind": latest.get("wind_speed", "-")
                })
        
        return jsonify({
            "success": True,
            "cities": cities
        })
    except Exception as e:
        print("获取城市天气列表失败：", e)
        return jsonify({"success": False}), 500

# API：获取活跃告警
@app.route("/api/dashboard/alerts", methods=["GET"])
def api_dashboard_alerts():
    try:
        alerts = get_active_alerts()
        return jsonify({
            "success": True,
            "alerts": alerts
        })
    except Exception as e:
        print("获取告警失败：", e)
        return jsonify({"success": False}), 500

# API：获取智能建议
@app.route("/api/dashboard/recommendations", methods=["GET"])
def api_recommendations():
    try:
        history = load_weather_history()
        
        recommendations = []
        for city, records in history.items():
            if records:
                latest_data = records[-1]["data"]
                rules = apply_linkage_rules(city, latest_data)
                
                for rule in rules:
                    recommendations.append({
                        "city": city,
                        "rule_name": rule["rule_name"],
                        "recommendation": rule["recommendation"]
                    })
        
        return jsonify({
            "success": True,
            "recommendations": recommendations[:10]  # 最多返回10条
        })
    except Exception as e:
        print("获取建议失败：", e)
        return jsonify({"success": False}), 500

# API：获取规则统计
@app.route("/api/dashboard/rule-statistics", methods=["GET"])
def api_rule_statistics():
    try:
        history = load_weather_history()
        
        rule_counts = {}
        for city, records in history.items():
            for record in records:
                latest_data = record["data"]
                rules = apply_linkage_rules(city, latest_data)
                for rule in rules:
                    rule_name = rule["rule_name"]
                    rule_counts[rule_name] = rule_counts.get(rule_name, 0) + 1
        
        return jsonify(rule_counts)
    except Exception as e:
        print("获取规则统计失败：", e)
        return jsonify({}), 500

# API：生成周报
@app.route("/api/report/weekly", methods=["GET"])
def api_weekly_report():
    try:
        report = generate_weekly_report()
        return jsonify({
            "success": True,
            "report": report
        })
    except Exception as e:
        print("生成周报失败：", e)
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

# API：生成日报
@app.route("/api/report/daily", methods=["GET"])
def api_daily_brief():
    try:
        brief = generate_daily_brief()
        return jsonify({
            "success": True,
            "brief": brief
        })
    except Exception as e:
        print("生成日报失败：", e)
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

# API：生成并保存周报
@app.route("/api/report/save-weekly", methods=["POST"])
def api_save_weekly_report():
    try:
        report = generate_weekly_report()
        filename = save_report_to_file(report)
        return jsonify({
            "success": True,
            "filename": filename,
            "report": report
        })
    except Exception as e:
        print("保存周报失败：", e)
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

# ============================================================
# 🆕 每周天气简报 API
# ============================================================

# 热门城市列表（用于简报）
POPULAR_CITIES = [
    {"name": "北京", "id": "beijing", "region": "华北"},
    {"name": "上海", "id": "shanghai", "region": "华东"},
    {"name": "广州", "id": "guangzhou", "region": "华南"},
    {"name": "深圳", "id": "shenzhen", "region": "华南"},
    {"name": "杭州", "id": "hangzhou", "region": "华东"},
    {"name": "成都", "id": "chengdu", "region": "西南"},
    {"name": "重庆", "id": "chongqing", "region": "西南"},
    {"name": "西安", "id": "xian", "region": "西北"},
    {"name": "南京", "id": "nanjing", "region": "华东"},
    {"name": "武汉", "id": "wuhan", "region": "华中"},
    {"name": "苏州", "id": "suzhou", "region": "华东"},
    {"name": "青岛", "id": "qingdao", "region": "华东"},
    {"name": "厦门", "id": "xiamen", "region": "华南"},
    {"name": "昆明", "id": "kunming", "region": "西南"},
    {"name": "丽江", "id": "lijiang", "region": "西南"},
]

def get_travel_score(temp, condition, humidity, wind_speed):
    """根据天气计算旅行适宜度分数 (0-100)"""
    score = 80  # 基础分

    # 温度评分
    if 18 <= temp <= 28:
        score += 10
    elif 10 <= temp <= 35:
        score += 5
    elif temp < 0 or temp > 40:
        score -= 30
    else:
        score -= 10

    # 天气状况评分
    condition_lower = condition.lower() if condition else ""
    if any(w in condition_lower for w in ["晴", "sunny", "clear"]):
        score += 10
    elif any(w in condition_lower for w in ["多云", "cloudy", "partly"]):
        score += 5
    elif any(w in condition_lower for w in ["阴", "overcast"]):
        score -= 5
    elif any(w in condition_lower for w in ["雨", "rain", "drizzle", "shower"]):
        score -= 15
    elif any(w in condition_lower for w in ["雪", "snow", "sleet"]):
        score -= 20
    elif any(w in condition_lower for w in ["雾", "fog", "mist", "霾", "haze"]):
        score -= 10
    elif any(w in condition_lower for w in ["雷", "thunder", "storm"]):
        score -= 25

    # 湿度评分
    if 30 <= humidity <= 60:
        score += 5
    elif humidity > 85:
        score -= 10

    # 风速评分
    if wind_speed > 40:
        score -= 15
    elif wind_speed > 25:
        score -= 5

    return max(0, min(100, score))

def generate_travel_advice(city_name, temp, condition, humidity, wind_speed, uv):
    """根据天气生成出行建议"""
    advice = []
    condition_lower = (condition or "").lower()

    # 温度建议
    if temp >= 35:
        advice.append("🔥 高温预警！避免中午户外活动，多补充水分")
    elif temp >= 30:
        advice.append("🌡️ 天气炎热，建议穿着轻薄透气的衣物")
    elif 18 <= temp <= 28:
        advice.append("🌤️ 气温宜人，非常适合户外游览")
    elif 10 <= temp < 18:
        advice.append("🍂 天气凉爽，建议携带薄外套")
    elif 0 <= temp < 10:
        advice.append("❄️ 天气寒冷，请穿厚外套注意保暖")
    elif temp < 0:
        advice.append("🥶 严寒天气，不建议长时间户外活动")

    # 天气状况建议
    if any(w in condition_lower for w in ["雨", "rain", "drizzle", "shower"]):
        advice.append("🌧️ 有降雨，请务必携带雨具")
        advice.append("📸 雨天适合安排博物馆、美术馆等室内景点")
    elif any(w in condition_lower for w in ["雪", "snow"]):
        advice.append("🌨️ 有降雪，路面湿滑请注意安全")
    elif any(w in condition_lower for w in ["晴", "sunny", "clear"]):
        advice.append("☀️ 天气晴好，适合拍照和户外活动")

    # 紫外线建议
    if uv >= 6:
        advice.append("🧴 紫外线强，请涂抹防晒霜并佩戴太阳镜")
    elif uv >= 3:
        advice.append("😎 中等紫外线，建议适当防晒")

    # 湿度建议
    if humidity > 80:
        advice.append("💧 湿度较大，体感闷热，注意防暑")
    elif humidity < 30:
        advice.append("🏜️ 空气干燥，注意补水和保湿")

    # 风速建议
    if wind_speed > 30:
        advice.append("💨 风力较大，远离广告牌和临时建筑")

    # 综合推荐
    score = get_travel_score(temp, condition, humidity, wind_speed)
    if score >= 80:
        advice.append("✅ 综合来看，今日非常适合旅行出游！")
    elif score >= 60:
        advice.append("👍 天气条件尚可，出行前请做好相应准备")
    elif score >= 40:
        advice.append("⚠️ 天气条件一般，建议根据个人情况决定是否出行")
    else:
        advice.append("🚫 天气条件较差，建议调整出行计划")

    return advice

@app.route("/api/weekly-briefing/data", methods=["GET"])
def api_weekly_briefing_data():
    """获取每周天气简报数据 - 实时抓取热门城市天气"""
    try:
        briefing_data = {
            "success": True,
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "period_start": datetime.now().strftime("%Y-%m-%d"),
            "period_end": (datetime.now() + timedelta(days=6)).strftime("%Y-%m-%d"),
            "cities": [],
            "summary": {}
        }

        rainy_cities = []
        best_cities = []
        all_temps = []
        all_scores = []

        for city_info in POPULAR_CITIES:
            city_name = city_info["name"]
            try:
                # 调用 WeatherAPI 获取实时天气
                from config import WEATHER_API_KEY
                url = "https://api.weatherapi.com/v1/current.json"
                params = {
                    "key": WEATHER_API_KEY,
                    "q": city_name,
                    "lang": "zh"
                }
                resp = requests.get(url, params=params, timeout=8)
                data = resp.json()

                if resp.status_code == 200 and "current" in data:
                    current = data["current"]
                    temp = current["temp_c"]
                    feels_like = current["feelslike_c"]
                    condition = current["condition"]["text"]
                    humidity = current["humidity"]
                    wind_speed = current["wind_kph"]
                    uv = current["uv"]
                    wind_dir = current["wind_dir"]
                    pressure = current["pressure_mb"]
                    visibility = current["vis_km"]

                    score = get_travel_score(temp, condition, humidity, wind_speed)
                    advice = generate_travel_advice(city_name, temp, condition, humidity, wind_speed, uv)

                    city_data = {
                        "name": city_name,
                        "id": city_info["id"],
                        "region": city_info["region"],
                        "temperature": temp,
                        "feels_like": feels_like,
                        "condition": condition,
                        "humidity": humidity,
                        "wind_speed": wind_speed,
                        "wind_dir": wind_dir,
                        "pressure": pressure,
                        "visibility": visibility,
                        "uv": uv,
                        "travel_score": score,
                        "advice": advice,
                        "icon": current["condition"]["icon"]
                    }
                else:
                    # API 调用失败，使用备用模拟数据
                    city_data = _generate_fallback_city_data(city_name, city_info)

            except Exception as e:
                print(f"获取 {city_name} 天气失败: {e}")
                city_data = _generate_fallback_city_data(city_name, city_info)

            briefing_data["cities"].append(city_data)
            all_temps.append(city_data["temperature"])
            all_scores.append(city_data["travel_score"])

            # 分类统计
            cond = (city_data["condition"] or "").lower()
            if any(w in cond for w in ["雨", "rain", "drizzle", "shower"]):
                rainy_cities.append(city_name)
            if city_data["travel_score"] >= 75:
                best_cities.append({
                    "name": city_name,
                    "score": city_data["travel_score"],
                    "condition": city_data["condition"],
                    "temp": city_data["temperature"]
                })

        # 按旅行评分排序
        briefing_data["cities"].sort(key=lambda c: c["travel_score"], reverse=True)
        best_cities.sort(key=lambda c: c["score"], reverse=True)

        # 生成摘要
        hottest_idx = all_temps.index(max(all_temps))
        coolest_idx = all_temps.index(min(all_temps))

        briefing_data["summary"] = {
            "total_cities": len(POPULAR_CITIES),
            "hottest_city": {
                "name": briefing_data["cities"][hottest_idx]["name"],
                "temp": max(all_temps)
            },
            "coolest_city": {
                "name": briefing_data["cities"][coolest_idx]["name"],
                "temp": min(all_temps)
            },
            "avg_temperature": round(sum(all_temps) / len(all_temps), 1),
            "rainy_cities": rainy_cities,
            "rainy_count": len(rainy_cities),
            "best_travel_cities": best_cities[:5],
            "overall_score": round(sum(all_scores) / len(all_scores))
        }

        # 保存简报数据用于导出
        briefing_data["_export_content"] = _build_export_content(briefing_data)

        return jsonify(briefing_data)

    except Exception as e:
        print("生成每周简报失败：", e)
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

def _generate_fallback_city_data(city_name, city_info):
    """当API调用失败时，使用备用模拟数据"""
    import random as _random
    base_temps = {
        "北京": 22, "上海": 26, "广州": 30, "深圳": 30, "杭州": 25,
        "成都": 24, "重庆": 26, "西安": 23, "南京": 25, "武汉": 26,
        "苏州": 25, "青岛": 21, "厦门": 28, "昆明": 20, "丽江": 18
    }
    base_conditions = ["晴", "多云", "阴", "小雨", "阵雨", "晴间多云"]

    temp = base_temps.get(city_name, 23) + _random.randint(-3, 3)
    condition = _random.choice(base_conditions)
    humidity = _random.randint(35, 80)
    wind_speed = _random.randint(5, 25)
    uv = _random.randint(1, 8)

    score = get_travel_score(temp, condition, humidity, wind_speed)
    advice = generate_travel_advice(city_name, temp, condition, humidity, wind_speed, uv)

    return {
        "name": city_name,
        "id": city_info["id"],
        "region": city_info["region"],
        "temperature": temp,
        "feels_like": temp + _random.randint(-2, 2),
        "condition": condition,
        "humidity": humidity,
        "wind_speed": wind_speed,
        "wind_dir": "东北风",
        "pressure": 1013 + _random.randint(-10, 10),
        "visibility": 8 + _random.randint(0, 8),
        "uv": uv,
        "travel_score": score,
        "advice": advice,
        "icon": "",
        "_fallback": True
    }

def _build_export_content(briefing_data):
    """构建各格式导出内容"""
    today_str = briefing_data["generated_at"]
    period = f"{briefing_data['period_start']} ~ {briefing_data['period_end']}"
    summary = briefing_data["summary"]
    cities = briefing_data["cities"]

    # 旅行评分等级图标
    def score_label(s):
        if s >= 80:
            return "🟢 优秀"
        elif s >= 60:
            return "🟡 良好"
        elif s >= 40:
            return "🟠 一般"
        else:
            return "🔴 较差"

    markdown = f"""# 🌤️ 每周天气旅行简报

> **生成时间**：{today_str}
> **简报周期**：{period}
> **监测城市**：{summary['total_cities']} 个热门旅游城市

---

## 📊 一周天气概览

| 指标 | 数据 |
|------|------|
| 📡 监测城市 | {summary['total_cities']} 个 |
| 🌡️ 平均气温 | {summary['avg_temperature']}°C |
| 🔥 最热城市 | {summary['hottest_city']['name']}（{summary['hottest_city']['temp']}°C） |
| ❄️ 最凉爽 | {summary['coolest_city']['name']}（{summary['coolest_city']['temp']}°C） |
| 🌧️ 降雨城市 | {summary['rainy_count']} 个 |
| ⭐ 综合旅行评分 | {summary['overall_score']}/100 |

---

## 🏙️ 各城市天气详情

| # | 城市 | 区域 | 温度 | 天气 | 湿度 | 风速 | UV | 旅行评分 |
|---|------|------|------|------|------|------|----|---------|
"""

    for i, city in enumerate(cities, 1):
        markdown += f"| {i} | {city['name']} | {city['region']} | {city['temperature']}°C | {city['condition']} | {city['humidity']}% | {city['wind_speed']}km/h | {city['uv']} | {score_label(city['travel_score'])} {city['travel_score']} |\n"

    markdown += f"""
---

## ⭐ 最佳旅行城市 TOP 5

"""

    for i, city in enumerate(summary['best_travel_cities'], 1):
        markdown += f"{i}. **{city['name']}** — {city['condition']}，{city['temp']}°C，旅行评分 {city['score']}/100\n"

    markdown += """
---

## 💡 出行建议

"""

    # 收集所有建议
    all_advice = {}
    for city in cities:
        for adv in city['advice']:
            all_advice[adv] = all_advice.get(adv, 0) + 1

    # 去重并排序（出现次数多的在前）
    sorted_advice = sorted(all_advice.items(), key=lambda x: x[1], reverse=True)
    for adv, count in sorted_advice[:10]:
        markdown += f"- {adv}\n"

    markdown += f"""

---

## 🌧️ 降雨城市提醒

"""

    if summary['rainy_cities']:
        markdown += "以下城市有降雨天气，出行请携带雨具：\n\n"
        for city_name in summary['rainy_cities']:
            city_data = next((c for c in cities if c['name'] == city_name), None)
            if city_data:
                markdown += f"- {city_name}：{city_data['condition']}，{city_data['temperature']}°C\n"
    else:
        markdown += "本周各城市无明显降雨，天气状况良好！✅\n"

    markdown += f"""

---

## 📋 各城市详细建议

"""

    for city in cities:
        markdown += f"""
### {city['name']}（{city['region']}）

🌡️ {city['temperature']}°C（体感 {city['feels_like']}°C）| 🌤️ {city['condition']} | 💧 湿度 {city['humidity']}% | 🌬️ {city['wind_speed']}km/h

**旅行建议**：
"""
        for adv in city['advice']:
            markdown += f"- {adv}\n"

    markdown += f"""

---

*本报告由 Travel Assistant 自动生成 | {today_str}*
"""

    # TXT 纯文本版本（去除 Markdown 标记）
    txt = markdown.replace("# ", "").replace("## ", "").replace("### ", "")
    txt = txt.replace("**", "").replace("*", "").replace("`", "")
    txt = txt.replace("|", " ").replace("---", "-" * 40)

    # JSON 结构化版本
    json_content = {
        "generated_at": today_str,
        "period": period,
        "summary": {k: v for k, v in summary.items() if k != "best_travel_cities"},
        "best_travel_cities": summary["best_travel_cities"],
        "cities": [{
            "name": c["name"],
            "region": c["region"],
            "temperature": c["temperature"],
            "feels_like": c["feels_like"],
            "condition": c["condition"],
            "humidity": c["humidity"],
            "wind_speed": c["wind_speed"],
            "wind_dir": c["wind_dir"],
            "uv": c["uv"],
            "travel_score": c["travel_score"],
            "advice": c["advice"]
        } for c in cities]
    }

    return {
        "markdown": markdown,
        "txt": txt,
        "json": json.dumps(json_content, ensure_ascii=False, indent=2)
    }

@app.route("/api/weekly-briefing/export", methods=["GET"])
def api_weekly_briefing_export():
    """导出每周天气简报（支持 md / txt / json 格式）"""
    try:
        export_format = request.args.get("format", "md").lower()

        if export_format not in ["md", "txt", "json"]:
            return jsonify({
                "success": False,
                "message": "不支持的导出格式，请使用 md / txt / json"
            }), 400

        # 重新生成简报数据
        # 先调用数据接口获取最新数据
        briefing_data = None
        try:
            # 直接内联生成
            all_cities = []
            rainy_cities = []
            best_cities = []
            all_temps = []
            all_scores = []

            for city_info in POPULAR_CITIES:
                city_name = city_info["name"]
                try:
                    from config import WEATHER_API_KEY
                    url = "https://api.weatherapi.com/v1/current.json"
                    params = {"key": WEATHER_API_KEY, "q": city_name, "lang": "zh"}
                    resp = requests.get(url, params=params, timeout=8)
                    data = resp.json()
                    if resp.status_code == 200 and "current" in data:
                        cur = data["current"]
                        temp = cur["temp_c"]
                        cond = cur["condition"]["text"]
                        hum = cur["humidity"]
                        ws = cur["wind_kph"]
                        uv = cur["uv"]
                        score = get_travel_score(temp, cond, hum, ws)
                        adv = generate_travel_advice(city_name, temp, cond, hum, ws, uv)
                        city_data = {
                            "name": city_name, "id": city_info["id"], "region": city_info["region"],
                            "temperature": temp, "feels_like": cur["feelslike_c"],
                            "condition": cond, "humidity": hum, "wind_speed": ws,
                            "wind_dir": cur["wind_dir"], "pressure": cur["pressure_mb"],
                            "visibility": cur["vis_km"], "uv": uv, "travel_score": score, "advice": adv
                        }
                    else:
                        city_data = _generate_fallback_city_data(city_name, city_info)
                except:
                    city_data = _generate_fallback_city_data(city_name, city_info)

                all_cities.append(city_data)
                all_temps.append(city_data["temperature"])
                all_scores.append(city_data["travel_score"])

                cond_lower = (city_data["condition"] or "").lower()
                if any(w in cond_lower for w in ["雨", "rain", "drizzle", "shower"]):
                    rainy_cities.append(city_name)
                if city_data["travel_score"] >= 75:
                    best_cities.append({
                        "name": city_name, "score": city_data["travel_score"],
                        "condition": city_data["condition"], "temp": city_data["temperature"]
                    })

            all_cities.sort(key=lambda c: c["travel_score"], reverse=True)
            best_cities.sort(key=lambda c: c["score"], reverse=True)
            hottest_idx = all_temps.index(max(all_temps))
            coolest_idx = all_temps.index(min(all_temps))

            briefing_data = {
                "success": True,
                "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "period_start": datetime.now().strftime("%Y-%m-%d"),
                "period_end": (datetime.now() + timedelta(days=6)).strftime("%Y-%m-%d"),
                "cities": all_cities,
                "summary": {
                    "total_cities": len(POPULAR_CITIES),
                    "hottest_city": {"name": all_cities[hottest_idx]["name"], "temp": max(all_temps)},
                    "coolest_city": {"name": all_cities[coolest_idx]["name"], "temp": min(all_temps)},
                    "avg_temperature": round(sum(all_temps) / len(all_temps), 1),
                    "rainy_cities": rainy_cities,
                    "rainy_count": len(rainy_cities),
                    "best_travel_cities": best_cities[:5],
                    "overall_score": round(sum(all_scores) / len(all_scores))
                }
            }
            briefing_data["_export_content"] = _build_export_content(briefing_data)
        except Exception as e:
            print(f"生成导出数据失败: {e}")
            return jsonify({"success": False, "message": str(e)}), 500

        export_content = briefing_data["_export_content"]

        if export_format == "md":
            content = export_content["markdown"]
            mimetype = "text/markdown; charset=utf-8"
            filename = f"weekly_weather_briefing_{datetime.now().strftime('%Y%m%d')}.md"
        elif export_format == "txt":
            content = export_content["txt"]
            mimetype = "text/plain; charset=utf-8"
            filename = f"weekly_weather_briefing_{datetime.now().strftime('%Y%m%d')}.txt"
        elif export_format == "json":
            content = export_content["json"]
            mimetype = "application/json; charset=utf-8"
            filename = f"weekly_weather_briefing_{datetime.now().strftime('%Y%m%d')}.json"

        return Response(
            content,
            mimetype=mimetype,
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )

    except Exception as e:
        print("导出简报失败：", e)
        return jsonify({"success": False, "message": str(e)}), 500

# 每周天气简报页面
@app.route("/weekly-briefing")
def weekly_briefing_page():
    return render_template("weekly_briefing.html")

# 🆕 旅行回顾卡片页面
@app.route("/travel-review-cards")
def travel_review_cards_page():
    return render_template("review_cards.html")

# API：智能行程规划
@app.route("/api/itinerary/generate", methods=["POST"])
def api_generate_itinerary():
    try:
        data = request.get_json()
        city = data.get('city', '北京')
        days = data.get('days', 3)
        preferences = data.get('preferences', ['sightseeing', 'food'])
        budget = data.get('budget', 'medium')
        
        itinerary = generate_itinerary(city, days, preferences, budget)
        
        return jsonify({
            "success": True,
            "itinerary": itinerary
        })
    except Exception as e:
        print("生成行程失败：", e)
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

# API：个性化推荐
@app.route("/api/recommendations", methods=["GET"])
def api_get_recommendations():
    try:
        user_id = request.args.get('user_id', None)
        recommendations = get_personalized_recommendations(user_id)
        
        return jsonify({
            "success": True,
            "recommendations": recommendations
        })
    except Exception as e:
        print("获取推荐失败：", e)
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

# API：预算估算
@app.route("/api/budget/estimate", methods=["POST"])
def api_estimate_budget():
    try:
        data = request.get_json()
        city = data.get('city', '北京')
        days = data.get('days', 3)
        budget_level = data.get('budget_level', 'medium')
        travel_style = data.get('travel_style', 'leisure')
        
        budget = estimate_budget(city, days, budget_level, travel_style)
        
        return jsonify({
            "success": True,
            "budget": budget
        })
    except Exception as e:
        print("预算估算失败：", e)
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

# API：获取每日天气简报
@app.route("/api/alert/daily-brief", methods=["GET"])
def api_alert_daily_brief():
    try:
        user_id = request.args.get('user_id', None)
        brief = schedule_daily_weather_brief(user_id)
        
        return jsonify({
            "success": True,
            "brief": brief
        })
    except Exception as e:
        print("生成每日简报失败：", e)
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

# API：生成旅行提醒
@app.route("/api/alert/travel-reminder", methods=["POST"])
def api_travel_reminder():
    try:
        data = request.get_json()
        destination = data.get('destination', '')
        date = data.get('date', '')
        preferences = data.get('preferences', None)
        
        if not destination or not date:
            return jsonify({
                "success": False,
                "message": "目的地和日期不能为空"
            }), 400
        
        reminder = generate_travel_reminder(destination, date, preferences)
        
        return jsonify({
            "success": True,
            "reminder": reminder
        })
    except Exception as e:
        print("生成旅行提醒失败：", e)
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

# API：检查旅行冲突
@app.route("/api/alert/check-conflicts", methods=["GET"])
def api_check_conflicts():
    try:
        trip_date = request.args.get('date', '')
        user_id = request.args.get('user_id', None)
        
        conflicts = check_trip_conflicts(trip_date, user_id)
        
        return jsonify({
            "success": True,
            "conflicts": conflicts
        })
    except Exception as e:
        print("检查旅行冲突失败：", e)
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

# API：获取待处理提醒
@app.route("/api/alert/pending", methods=["GET"])
def api_pending_alerts():
    try:
        alerts = alert_service.get_pending_alerts()
        
        return jsonify({
            "success": True,
            "alerts": alerts
        })
    except Exception as e:
        print("获取待处理提醒失败：", e)
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

# API：确认提醒
@app.route("/api/alert/acknowledge", methods=["POST"])
def api_acknowledge_alert():
    try:
        data = request.get_json()
        alert_id = data.get('alert_id', '')
        
        if alert_id:
            alert_service.acknowledge_alert(alert_id)
        else:
            alert_service.acknowledge_all()
        
        return jsonify({
            "success": True
        })
    except Exception as e:
        print("确认提醒失败：", e)
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

# 聊天接口
@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                "reply": "没有接收到JSON数据"
            }), 400

        user_message = data.get("message", "")
        user_id = data.get("user_id", "default_user")  # 支持多用户画像

        if not user_message:
            return jsonify({
                "reply": "消息不能为空"
            }), 400

        # 安全检查
        safety = safety_check(user_message)
        if safety == "BLOCK":
            return jsonify({
                "reply": "该内容存在风险"
            })

        # 意图识别
        intent = recognize_intent(user_message)

        # 读取长期记忆
        memory = load_memory()

        # 读取对话历史
        conversation_history = get_conversation_history()

        # 问候语
        if intent == "greeting":
            reply = get_greeting_response(user_message)

        # 感谢
        elif intent == "thanks":
            reply = get_thanks_response()

        # 天气查询
        elif intent == "weather":
            city = extract_city_from_message(user_message)
            if not city:
                reply = "请告诉我您想查询哪个城市的天气"
            else:
                reply = get_weather(city)

        # 普通聊天
        else:
            # 构建包含对话历史的prompt
            history_str = "\n".join([f"{item['role']}: {item['content']}" for item in conversation_history[-10:]])

            # 🆕 特色功能：注入用户画像上下文
            persona_context = persona_service.generate_persona_context_for_prompt(user_id)

            prompt = f"""
你是旅游计划生成助手。

用户长期记忆：
{memory}

{persona_context}

对话历史：
{history_str}

用户问题：
{user_message}
"""
            reply = ask_llm(prompt)

        # 保存对话历史
        save_conversation(user_message, reply)

        # 提取用户偏好
        preferences = extract_preferences(user_message)

        # 🆕 特色功能：三层偏好提取 - 显式偏好
        persona_service.extract_explicit_preferences(user_id, user_message)

        # 🆕 特色功能：三层偏好提取 - 隐式偏好
        if intent == "weather" or intent == "travel":
            city = extract_city_from_message(user_message)
            persona_service.extract_implicit_preferences(user_id, {
                'action': 'query_city' if intent == 'weather' else 'plan_travel',
                'city': city or '未知',
                'intent': intent
            })

        # 保存偏好
        if preferences:
            save_memory(preferences)

        return jsonify({
            "reply": reply
        })

    except Exception as e:
        print("后端错误：", e)
        return jsonify({
            "reply": f"服务器错误：{str(e)}"
        }), 500

# 获取对话历史接口
@app.route("/conversation-history", methods=["GET"])
def conversation_history():
    try:
        history = get_conversation_history()
        return jsonify({
            "history": history
        })
    except Exception as e:
        print("获取对话历史失败：", e)
        return jsonify({
            "history": []
        }), 500

# 清空对话历史接口
@app.route("/clear-conversation", methods=["POST"])
def clear_conversation_endpoint():
    try:
        clear_conversation()
        return jsonify({
            "success": True
        })
    except Exception as e:
        print("清空对话历史失败：", e)
        return jsonify({
            "success": False
        }), 500

# 获取最近会话列表接口
@app.route("/recent-conversations", methods=["GET"])
def recent_conversations():
    try:
        conversations = get_recent_conversations(limit=10)
        return jsonify({
            "conversations": conversations
        })
    except Exception as e:
        print("获取最近会话失败：", e)
        return jsonify({
            "conversations": []
        }), 500

# 按日期获取会话接口
@app.route("/conversation-by-date", methods=["GET"])
def conversation_by_date():
    try:
        date_str = request.args.get("date")
        if not date_str:
            return jsonify({"history": []}), 400
        
        history = get_conversation_by_date(date_str)
        return jsonify({
            "history": history
        })
    except Exception as e:
        print("获取指定日期会话失败：", e)
        return jsonify({
            "history": []
        }), 500

# ============================================================
# 🆕 作业9特色功能API：旅行人格画像引擎
# ============================================================

# API：获取用户画像
@app.route("/api/persona/<user_id>", methods=["GET"])
def api_get_persona(user_id):
    """获取用户旅行人格画像"""
    try:
        persona = persona_service.get_or_create_persona(user_id)
        persona.apply_decay()
        return jsonify({
            "success": True,
            "persona": persona.to_dict(),
            "summary": persona.get_persona_summary(),
            "top_interests": persona.get_top_interests(5)
        })
    except Exception as e:
        print("获取画像失败：", e)
        return jsonify({"success": False, "message": str(e)}), 500

# API：更新用户画像偏好（显式声明）
@app.route("/api/persona/<user_id>/preferences", methods=["POST"])
def api_update_persona_preferences(user_id):
    """用户显式声明偏好"""
    try:
        data = request.get_json()
        message = data.get('message', '')

        if not message:
            return jsonify({"success": False, "message": "偏好描述不能为空"}), 400

        extracted = persona_service.extract_explicit_preferences(user_id, message)
        persona = persona_service.get_persona(user_id)

        return jsonify({
            "success": True,
            "extracted_preferences": extracted,
            "persona_summary": persona.get_persona_summary() if persona else ""
        })
    except Exception as e:
        print("更新偏好失败：", e)
        return jsonify({"success": False, "message": str(e)}), 500

# API：提交推荐反馈
@app.route("/api/persona/<user_id>/feedback", methods=["POST"])
def api_submit_feedback(user_id):
    """用户对推荐的反馈"""
    try:
        data = request.get_json()
        recommendation_type = data.get('type', 'general')
        recommendation_content = data.get('content', '')
        accepted = data.get('accepted', True)

        result = persona_service.apply_feedback(
            user_id, recommendation_type, recommendation_content, accepted
        )

        return jsonify({
            "success": True,
            "feedback_result": result
        })
    except Exception as e:
        print("提交反馈失败：", e)
        return jsonify({"success": False, "message": str(e)}), 500

# API：基于画像的个性化城市推荐
@app.route("/api/persona/<user_id>/city-recommendations", methods=["GET"])
def api_persona_city_recommendations(user_id):
    """基于用户画像的个性化城市推荐"""
    try:
        # 获取所有候选城市
        all_cities = get_all_cities()
        if not all_cities:
            return jsonify({"success": False, "message": "无法获取城市列表"}), 500

        # 为每个城市添加特征标签
        city_features_map = {
            '北京': ['history', 'culture', 'architecture', 'food'],
            '上海': ['shopping', 'nightlife', 'architecture', 'food'],
            '广州': ['food', 'shopping', 'culture', 'nightlife'],
            '深圳': ['theme_park', 'shopping', 'adventure', 'modern'],
            '杭州': ['nature', 'photography', 'culture', 'relax'],
            '成都': ['food', 'relax', 'culture', 'nature'],
            '重庆': ['food', 'mountain', 'nightlife', 'culture'],
            '西安': ['history', 'culture', 'food', 'architecture'],
            '南京': ['history', 'culture', 'nature', 'food'],
            '武汉': ['culture', 'food', 'nature', 'sightseeing'],
            '苏州': ['culture', 'architecture', 'nature', 'relax'],
            '青岛': ['beach', 'food', 'relax', 'nature'],
            '厦门': ['beach', 'relax', 'food', 'photography'],
            '昆明': ['nature', 'relax', 'photography', 'culture'],
            '丽江': ['nature', 'relax', 'culture', 'adventure']
        }

        cities_with_features = []
        for city in all_cities:
            city_name = city.get('name', city.get('city', ''))
            features = city_features_map.get(city_name, ['sightseeing'])
            cities_with_features.append({
                'city': city_name,
                'name': city_name,
                'features': features,
                'cost_level': 'medium',
                'risk_level': 'low'
            })

        # 画像驱动排序
        ranked_cities = persona_service.filter_and_rank_cities(user_id, cities_with_features)

        # 添加用户画像摘要
        persona = persona_service.get_persona(user_id)

        return jsonify({
            "success": True,
            "recommendations": ranked_cities[:8],
            "persona_summary": persona.get_persona_summary() if persona else ""
        })
    except Exception as e:
        print("画像推荐失败：", e)
        return jsonify({"success": False, "message": str(e)}), 500

# ============================================================
# 🆕 作业9特色功能API：主动式行程守护者
# ============================================================

# API：注册行程并启动守护
@app.route("/api/guardian/register-trip", methods=["POST"])
def api_register_trip():
    """注册一个新的旅行行程"""
    try:
        data = request.get_json()
        user_id = data.get('user_id', 'default_user')
        destination = data.get('destination', '')
        start_date = data.get('start_date', '')
        end_date = data.get('end_date', '')
        days = data.get('days', 3)
        preferences = data.get('preferences', ['sightseeing', 'food'])
        budget = data.get('budget', 'medium')

        if not destination or not start_date or not end_date:
            return jsonify({
                "success": False,
                "message": "目的地、开始日期和结束日期不能为空"
            }), 400

        # 生成行程计划
        itinerary = generate_itinerary(destination, days, preferences, budget)
        days_plan = itinerary.get('days_plan', [])

        # 注册到守护者
        trip_id = trip_guardian_service.register_trip(
            user_id, destination, start_date, end_date, days_plan
        )

        # 执行行前检查
        pre_trip_result = trip_guardian_service.phase1_pre_trip_check(trip_id)

        return jsonify({
            "success": True,
            "trip_id": trip_id,
            "pre_trip_check": pre_trip_result,
            "itinerary": itinerary
        })
    except Exception as e:
        print("注册行程失败：", e)
        return jsonify({"success": False, "message": str(e)}), 500

# API：行前检查
@app.route("/api/guardian/pre-trip/<trip_id>", methods=["GET"])
def api_pre_trip_check(trip_id):
    """执行行前智能预判"""
    try:
        result = trip_guardian_service.phase1_pre_trip_check(trip_id)
        return jsonify(result)
    except Exception as e:
        print("行前检查失败：", e)
        return jsonify({"success": False, "message": str(e)}), 500

# API：行中实时监控
@app.route("/api/guardian/realtime/<trip_id>", methods=["GET"])
def api_realtime_monitoring(trip_id):
    """执行行中实时动态守护"""
    try:
        result = trip_guardian_service.phase2_realtime_monitoring(trip_id)
        return jsonify(result)
    except Exception as e:
        print("实时监控失败：", e)
        return jsonify({"success": False, "message": str(e)}), 500

# API：行后总结
@app.route("/api/guardian/post-trip/<trip_id>", methods=["POST"])
def api_post_trip_summary(trip_id):
    """生成行后经验沉淀"""
    try:
        result = trip_guardian_service.phase3_post_trip_summary(trip_id)
        return jsonify(result)
    except Exception as e:
        print("生成行后总结失败：", e)
        return jsonify({"success": False, "message": str(e)}), 500

# API：获取守护者状态
@app.route("/api/guardian/status", methods=["GET"])
def api_guardian_status():
    """获取守护者运行状态"""
    try:
        status = trip_guardian_service.get_guardian_status()
        log = trip_guardian_service.get_guardian_log(20)
        return jsonify({
            "success": True,
            "status": status,
            "recent_log": log
        })
    except Exception as e:
        print("获取守护者状态失败：", e)
        return jsonify({"success": False, "message": str(e)}), 500

# API：获取用户活跃行程
@app.route("/api/guardian/active-trip/<user_id>", methods=["GET"])
def api_active_trip(user_id):
    """获取用户的活跃行程"""
    try:
        trip = trip_guardian_service.get_user_active_trip(user_id)
        if trip:
            return jsonify({
                "success": True,
                "trip": trip.to_dict()
            })
        else:
            return jsonify({
                "success": True,
                "trip": None,
                "message": "当前无活跃行程"
            })
    except Exception as e:
        print("获取活跃行程失败：", e)
        return jsonify({"success": False, "message": str(e)}), 500

# API：检查所有活跃行程（后台监控用）
@app.route("/api/guardian/check-all", methods=["POST"])
def api_check_all_trips():
    """手动触发所有活跃行程检查"""
    try:
        results = trip_guardian_service.check_all_active_trips()
        return jsonify({
            "success": True,
            "checked_trips": len(results),
            "interventions": results
        })
    except Exception as e:
        print("检查所有行程失败：", e)
        return jsonify({"success": False, "message": str(e)}), 500

# API：启动后台守护
@app.route("/api/guardian/start", methods=["POST"])
def api_start_guardian():
    """启动行程守护者后台监控"""
    try:
        trip_guardian_service.start_background_monitoring()
        return jsonify({
            "success": True,
            "message": "行程守护者后台监控已启动"
        })
    except Exception as e:
        print("启动守护者失败：", e)
        return jsonify({"success": False, "message": str(e)}), 500

# API：停止后台守护
@app.route("/api/guardian/stop", methods=["POST"])
def api_stop_guardian():
    """停止行程守护者后台监控"""
    try:
        trip_guardian_service.stop_background_monitoring()
        return jsonify({
            "success": True,
            "message": "行程守护者后台监控已停止"
        })
    except Exception as e:
        print("停止守护者失败：", e)
        return jsonify({"success": False, "message": str(e)}), 500

# API：获取守护者日志
@app.route("/api/guardian/log", methods=["GET"])
def api_guardian_log():
    """获取守护者操作日志"""
    try:
        limit = request.args.get('limit', 50, type=int)
        log = trip_guardian_service.get_guardian_log(limit)
        return jsonify({
            "success": True,
            "log": log
        })
    except Exception as e:
        print("获取日志失败：", e)
        return jsonify({"success": False, "message": str(e)}), 500

# ============================================================
# 🆕 综合测试API：特色功能端到端测试
# ============================================================

@app.route("/api/test/special-features", methods=["GET"])
def api_test_special_features():
    """测试所有特色功能"""
    test_user = request.args.get('user_id', 'test_user_001')
    results = {
        'persona_test': {},
        'guardian_test': {},
        'overall': ''
    }

    # 1. 测试画像引擎
    try:
        persona = persona_service.get_or_create_persona(test_user)

        # 模拟显式偏好提取
        messages = [
            "我喜欢历史文化类的旅行，特别喜欢逛博物馆和古迹",
            "我不喜欢太赶的行程，喜欢慢慢感受当地文化",
            "预算中等就行，但吃方面我愿意多花点钱",
            "我一般和朋友一起出行，三四个人的小团体"
        ]
        for msg in messages:
            persona_service.extract_explicit_preferences(test_user, msg)

        # 模拟隐式偏好提取
        persona_service.extract_implicit_preferences(test_user, {
            'action': 'query_city', 'city': '西安',
            'preferences': ['history', 'culture', 'food']
        })
        persona_service.extract_implicit_preferences(test_user, {
            'action': 'generate_itinerary', 'days': 4,
            'preferences': ['history', 'culture', 'food', 'photography'],
            'attraction_count': 12
        })

        # 模拟反馈
        persona_service.apply_feedback(test_user, 'city', '西安旅游推荐', True)
        persona_service.apply_feedback(test_user, 'activity', '滑雪推荐', False)

        updated_persona = persona_service.get_persona(test_user)
        updated_persona.apply_decay()

        results['persona_test'] = {
            'status': 'success',
            'persona_summary': updated_persona.get_persona_summary(),
            'top_interests': updated_persona.get_top_interests(5),
            'interaction_count': updated_persona.interaction_count,
            'accept_rate': round(
                updated_persona.recommendation_accept_count /
                max(updated_persona.interaction_count, 1), 3
            )
        }
    except Exception as e:
        results['persona_test'] = {'status': 'error', 'message': str(e)}

    # 2. 测试行程守护者
    try:
        # 注册一个测试行程
        test_days_plan = [
            {
                'day': 1,
                'date': (datetime.now()).strftime('%Y-%m-%d'),
                'morning': {'activity': '景点游览', 'place': '兵马俑', 'duration': '3小时'},
                'afternoon': {'activity': '景点游览', 'place': '大雁塔', 'duration': '2小时'},
                'evening': {'activity': '美食体验', 'place': '回民街', 'duration': '2小时'}
            },
            {
                'day': 2,
                'date': (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d'),
                'morning': {'activity': '户外摄影', 'place': '城墙', 'duration': '2小时'},
                'afternoon': {'activity': '博物馆', 'place': '陕西历史博物馆', 'duration': '3小时'},
                'evening': {'activity': '夜景观光', 'place': '大唐不夜城', 'duration': '2小时'}
            }
        ]

        trip_id = trip_guardian_service.register_trip(
            test_user, '西安',
            (datetime.now()).strftime('%Y-%m-%d'),
            (datetime.now() + timedelta(days=2)).strftime('%Y-%m-%d'),
            test_days_plan
        )

        # 执行行前检查
        pre_trip = trip_guardian_service.phase1_pre_trip_check(trip_id)

        # 执行实时监控
        realtime = trip_guardian_service.phase2_realtime_monitoring(trip_id)

        # 执行行后总结
        post_trip = trip_guardian_service.phase3_post_trip_summary(trip_id)

        results['guardian_test'] = {
            'status': 'success',
            'trip_id': trip_id,
            'pre_trip_alerts_count': len(pre_trip.get('alerts', [])),
            'pre_trip_recommendations_count': len(pre_trip.get('recommendations', [])),
            'realtime_interventions_count': len(realtime.get('interventions', [])),
            'post_trip_summary': post_trip.get('trip_summary', {}),
            'guardian_log_count': len(trip_guardian_service.get_guardian_log(100))
        }
    except Exception as e:
        results['guardian_test'] = {'status': 'error', 'message': str(e)}

    # 3. 总体评估
    all_success = (
        results['persona_test'].get('status') == 'success' and
        results['guardian_test'].get('status') == 'success'
    )
    results['overall'] = 'ALL_PASSED' if all_success else 'SOME_FAILED'

    return jsonify({
        "success": all_success,
        "results": results,
        "timestamp": datetime.now().isoformat()
    })

# ============================================================
# 🆕 旅行回顾卡片 API
# ============================================================

@app.route("/api/review-cards/available-trips", methods=["GET"])
def api_available_trips():
    """获取可生成回顾卡片的已完成行程 + 已生成的卡片列表"""
    try:
        user_id = request.args.get("user_id", "default_user")
        result = get_available_trips(user_id)
        return jsonify({"success": True, **result})
    except Exception as e:
        print("获取可用行程失败：", e)
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/api/review-cards/generate", methods=["POST"])
def api_generate_review_card():
    """生成旅行回顾卡片"""
    try:
        data = request.get_json()
        trip_id = data.get("trip_id", "")
        user_id = data.get("user_id", "default_user")

        if not trip_id:
            return jsonify({"success": False, "message": "缺少 trip_id"}), 400

        result = generate_review_card(trip_id, user_id)
        return jsonify(result)
    except Exception as e:
        print("生成回顾卡片失败：", e)
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/api/review-cards/list", methods=["GET"])
def api_review_cards_list():
    """列出用户的所有回顾卡片"""
    try:
        user_id = request.args.get("user_id", "default_user")
        cards = list_cards_for_user(user_id)
        return jsonify({"success": True, "cards": cards})
    except Exception as e:
        print("获取回顾卡片列表失败：", e)
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/api/review-cards/<card_id>", methods=["GET"])
def api_review_card_detail(card_id):
    """获取单张回顾卡片详情"""
    try:
        card = get_card(card_id)
        if card:
            return jsonify({"success": True, "card": card})
        return jsonify({"success": False, "message": "卡片不存在"}), 404
    except Exception as e:
        print("获取回顾卡片详情失败：", e)
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/api/review-cards/<card_id>/export", methods=["GET"])
def api_review_card_export(card_id):
    """导出回顾卡片为 Markdown"""
    try:
        card = get_card(card_id)
        if not card:
            return jsonify({"success": False, "message": "卡片不存在"}), 404

        fmt = request.args.get("format", "json")
        if fmt == "markdown":
            md_content = export_card_markdown(card_id)
            if md_content:
                return jsonify({"success": True, "markdown": md_content})
            return jsonify({"success": False, "message": "导出失败"}), 500
        else:
            return jsonify({"success": True, "card": card})
    except Exception as e:
        print("导出回顾卡片失败：", e)
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/api/review-cards/<card_id>", methods=["DELETE"])
def api_review_card_delete(card_id):
    """删除回顾卡片"""
    try:
        deleted = delete_card(card_id)
        if deleted:
            return jsonify({"success": True, "message": "卡片已删除"})
        return jsonify({"success": False, "message": "卡片不存在"}), 404
    except Exception as e:
        print("删除回顾卡片失败：", e)
        return jsonify({"success": False, "message": str(e)}), 500


if __name__ == "__main__":
    # 设置控制台输出编码为 UTF-8（Windows 兼容）
    import sys
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except Exception:
            pass

    print("=" * 50)
    print("  Travel Assistant - 旅游计划生成助手")
    print("=" * 50)
    print(f"  访问地址: http://{FLASK_HOST}:{FLASK_PORT}")
    print(f"  调试模式: {'开启' if FLASK_DEBUG else '关闭'}")
    print("=" * 50)
    app.run(host=FLASK_HOST, port=FLASK_PORT, debug=FLASK_DEBUG)