"""
数据驱动的智能响应服务
满足作业8 L3要求：数据驱动的建议调整
"""
from services.weather_service import get_weather, get_weather_forecast
from services.city_service import get_city_by_id
from services.data_storage import load_weather_history

# 联动规则定义
LINKAGE_RULES = {
    # 规则1：高温天气 → 推荐室内景点
    "high_temp_indoor": {
        "name": "高温避暑推荐",
        "trigger": {
            "condition": lambda d: d.get("temperature", 0) >= 32,
            "description": "当温度 >= 32°C"
        },
        "action": "recommend_indoor_spots",
        "recommendation_template": "🔥 {city}当前气温较高（{temp}°C），推荐您前往室内景点避暑：\n{spots}\n\n室内活动优势：\n• 温度舒适，不受高温影响\n• 可以细细品味文化内涵\n• 避免中暑风险"
    },
    
    # 规则2：雨天 → 调整行程为室内
    "rain_outdoor_cancel": {
        "name": "雨天行程调整",
        "trigger": {
            "condition": lambda d: d.get("precipitation", 0) > 0 or "雨" in d.get("condition", ""),
            "description": "当有降水或预报有雨"
        },
        "action": "suggest_indoor_alternative",
        "recommendation_template": "🌧️ {city}今天有{condition}，建议调整行程：\n\n【取消/改期】\n• 户外景区游览\n• 露天活动\n• 漂流、蹦极等高风险项目\n\n【推荐替代】\n• 博物馆、美术馆\n• 商场、美食街\n• 电影院、剧院\n• 温泉、SPA"
    },
    
    # 规则3：空气质量差 → 推荐口罩+室内
    "poor_aqi_indoor": {
        "name": "空气质量应对",
        "trigger": {
            "condition": lambda d: d.get("aqi", 0) >= 100,
            "description": "当AQI >= 100"
        },
        "action": "aqi_recommendation",
        "recommendation_template": "🌫️ {city}当前空气质量不佳（AQI: {aqi}），建议：\n\n【出行建议】\n• 佩戴KN95/N95口罩\n• 避免长时间户外活动\n• 选择室内景点游览\n\n【健康提示】\n• 敏感人群（老人、儿童、呼吸道疾病患者）减少外出\n• 开启车内内循环\n• 回住所后及时更换衣物、洗手洗脸"
    },
    
    # 规则4：适宜天气 → 户外深度游
    "good_weather_outdoor": {
        "name": "适宜天气推荐",
        "trigger": {
            "condition": lambda d: 15 <= d.get("temperature", 0) <= 28 and 
                                   d.get("precipitation", 0) == 0 and 
                                   d.get("uv", 0) < 8 and 
                                   "雨" not in d.get("condition", ""),
            "description": "当温度15-28°C、无雨、UV<8"
        },
        "action": "outdoor_recommendation",
        "recommendation_template": "🌈 {city}今日天气绝佳，非常适合户外游览！\n\n【完美条件】\n• 温度：{temp}°C（舒适宜人）\n• 天气：{condition}\n• 紫外线：{uv}（强度适中）\n\n【推荐活动】\n• 徒步登山\n• 城市漫步\n• 景区打卡\n• 户外摄影"
    },
    
    # 规则5：极端天气 → 取消/推迟行程
    "extreme_weather_postpone": {
        "name": "极端天气应对",
        "trigger": {
            "condition": lambda d: d.get("temperature", 0) >= 40 or 
                                   d.get("temperature", 0) <= -5 or 
                                   d.get("wind_speed", 0) >= 60 or
                                   "暴雨" in d.get("condition", "") or
                                   "台风" in d.get("condition", ""),
            "description": "当出现极端天气条件"
        },
        "action": "extreme_weather_action",
        "recommendation_template": "⚠️ {city}当前天气条件极端，建议立即采取行动：\n\n【当前状况】\n• 温度：{temp}°C\n• 天气：{condition}\n• 风速：{wind}km/h\n\n【行动建议】\n• 立即停止户外活动，寻找安全室内场所\n• 推迟或取消今日行程\n• 关注官方天气预警和交通信息\n• 保持手机电量充足，随时联系"
    },
    
    # 规则6：早春/晚秋温差大 → 洋葱式穿衣
    "large_temp_swing": {
        "name": "温差穿衣建议",
        "trigger": {
            "condition": lambda d: d.get("feels_like", 0) - d.get("temperature", 0) >= 5 or
                                   d.get("feels_like", 0) - d.get("temperature", 0) <= -5,
            "description": "体感温度与实际温度差异大"
        },
        "action": "dressing_advice",
        "recommendation_template": "👔 {city}今日温差较大，请注意穿衣：\n\n【温度详情】\n• 实际温度：{temp}°C\n• 体感温度：{feels_like}°C\n\n【穿衣建议】\n• 采用\"洋葱式\"穿衣法\n• 建议携带外套或轻薄羽绒服\n• 早晚及时增减衣物\n• 选择易穿脱的层叠搭配"
    }
}

# 室内景点推荐数据
INDOOR_SPOTS = {
    "北京": ["中国国家博物馆", "故宫博物院", "国家大剧院", "798艺术区", "北京海洋馆"],
    "上海": ["上海博物馆", "上海科技馆", "东方明珠", "环球金融中心", "杜莎夫人蜡像馆"],
    "广州": ["广东省博物馆", "广州图书馆", "正佳极地海洋世界", "广州塔观光大厅", "时尚天河"],
    "深圳": ["深圳博物馆", "华强北商业街", "海上世界", "欢乐谷玛雅水公园", "深圳当代艺术馆"],
    "杭州": ["浙江省博物馆", "西湖博物馆", "宋城", "灵隐寺（室内部分）", "杭州博物馆"],
    "成都": ["成都博物馆", "四川科技馆", "宽窄巷子（室内店铺）", "锦里古街", "大熊猫基地（室内馆）"],
    "西安": ["陕西历史博物馆", "秦始皇兵马俑博物馆", "西安城墙（部分室内）", "大唐不夜城", "永兴坊"],
    "重庆": ["重庆中国三峡博物馆", "磁器口古镇", "洪崖洞", "长江索道（车厢内）", "解放碑商圈"],
    "南京": ["南京博物院", "侵华日军南京大屠杀遇难同胞纪念馆", "明孝陵（室内展厅）", "总统府", "夫子庙"],
    "武汉": ["湖北省博物馆", "武汉博物馆", "黄鹤楼（室内展陈）", "户部巷", "光谷步行街"]
}

def apply_linkage_rules(city, weather_data):
    """
    应用联动规则，根据天气数据调整旅行建议
    
    参数:
        city: 城市名称
        weather_data: 天气数据字典
    
    返回:
        dict: 触发的规则和建议
    """
    triggered_rules = []
    
    for rule_id, rule in LINKAGE_RULES.items():
        try:
            if rule["trigger"]["condition"](weather_data):
                recommendation = generate_recommendation(city, weather_data, rule)
                triggered_rules.append({
                    "rule_id": rule_id,
                    "rule_name": rule["name"],
                    "trigger_desc": rule["trigger"]["description"],
                    "action": rule["action"],
                    "recommendation": recommendation
                })
        except Exception as e:
            print(f"应用规则 {rule_id} 时出错: {e}")
    
    return triggered_rules

def generate_recommendation(city, weather_data, rule):
    """生成具体建议"""
    try:
        template = rule["recommendation_template"]
        
        # 填充模板数据
        spots = get_indoor_spots_recommendation(city)
        
        return template.format(
            city=city,
            temp=weather_data.get("temperature", "未知"),
            condition=weather_data.get("condition", "未知"),
            aqi=weather_data.get("aqi", "未知"),
            wind=weather_data.get("wind_speed", "未知"),
            uv=weather_data.get("uv", "未知"),
            feels_like=weather_data.get("feels_like", "未知"),
            spots=spots
        )
    except Exception as e:
        print(f"生成建议失败: {e}")
        return "无法生成建议，请稍后重试。"

def get_indoor_spots_recommendation(city):
    """获取室内景点推荐"""
    spots = INDOOR_SPOTS.get(city, [])
    
    if not spots:
        return "• 博物馆、美术馆\n• 商场、美食街\n• 电影院、剧院\n• 温泉、SPA"
    
    return "\n".join([f"• {spot}" for spot in spots[:5]])

def get_comprehensive_travel_advice(city):
    """
    获取综合旅行建议（整合天气和建议调整）
    """
    try:
        # 获取当前天气
        from services.weather_service import get_weather
        
        # 这里我们不直接调用get_weather避免循环依赖
        # 而是解析已保存的天气数据
        history = load_weather_history()
        
        if city not in history or not history[city]:
            return None
        
        latest_data = history[city][-1]["data"]
        
        # 应用联动规则
        rules = apply_linkage_rules(city, latest_data)
        
        if not rules:
            return {
                "city": city,
                "weather": latest_data,
                "rules_triggered": 0,
                "advice": "当前天气条件良好，适合各类旅行活动。"
            }
        
        # 整合所有建议
        full_advice = f"📋 {city}旅行建议\n\n"
        full_advice += f"当前天气：{latest_data.get('condition', '未知')}，{latest_data.get('temperature', '?')}°C\n\n"
        
        for rule in rules:
            full_advice += f"【{rule['rule_name']}】\n{rule['recommendation']}\n\n"
        
        return {
            "city": city,
            "weather": latest_data,
            "rules_triggered": len(rules),
            "rules": rules,
            "advice": full_advice,
            "primary_action": rules[0]["action"] if rules else None
        }
        
    except Exception as e:
        print(f"获取综合建议失败: {e}")
        return None

def verify_adjustment_effect(action, weather_data):
    """
    验证调整效果
    """
    # 根据采取的行动和后续天气数据验证效果
    # 这里简化处理，实际应用中需要跟踪用户行为和天气变化
    
    effect_indicators = {
        "recommend_indoor_spots": {
            "action_taken": "已推荐室内景点",
            "expected_outcome": "用户满意度提升，行程完成率提高",
            "verification": "用户反馈评分"
        },
        "suggest_indoor_alternative": {
            "action_taken": "已建议室内替代方案",
            "expected_outcome": "减少因天气造成的行程取消",
            "verification": "行程完成率对比"
        },
        "outdoor_recommendation": {
            "action_taken": "已推荐户外活动",
            "expected_outcome": "用户充分利用好天气",
            "verification": "景点访问量"
        },
        "extreme_weather_action": {
            "action_taken": "已发出极端天气警告",
            "expected_outcome": "减少安全事故发生",
            "verification": "事故报告数量"
        }
    }
    
    return effect_indicators.get(action, {
        "action_taken": "未知操作",
        "expected_outcome": "待评估",
        "verification": "需要更多数据"
    })

def get_travel_recommendation_summary():
    """
    获取旅行建议汇总（用于看板展示）
    """
    summary = {
        "cities_with_recommendations": [],
        "rule_statistics": {}
    }
    
    # 统计各规则的触发次数
    try:
        history = load_weather_history()
        
        for city, records in history.items():
            if not records:
                continue
            
            latest = records[-1]["data"]
            rules = apply_linkage_rules(city, latest)
            
            if rules:
                summary["cities_with_recommendations"].append({
                    "city": city,
                    "rule_count": len(rules),
                    "primary_rule": rules[0]["rule_name"],
                    "weather": latest.get("condition", "未知"),
                    "temperature": latest.get("temperature", "未知")
                })
            
            # 统计规则触发
            for rule in rules:
                rule_name = rule["rule_name"]
                summary["rule_statistics"][rule_name] = summary["rule_statistics"].get(rule_name, 0) + 1
        
    except Exception as e:
        print(f"获取建议汇总失败: {e}")
    
    return summary