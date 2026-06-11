"""
异常检测与主动通知服务
满足作业8 L2要求：异常检测与主动通知
"""
import json
import os
from datetime import datetime, timedelta
from services.data_storage import load_weather_history, load_alert_history, save_alert

# 异常检测规则定义
ALERT_RULES = {
    # 高温预警规则
    "high_temp": {
        "name": "高温预警",
        "threshold": 38,  # 温度阈值（摄氏度）
        "condition": lambda d: d.get("temperature", 0) >= 38,
        "severity": "warning",
        "message_template": "{city}当前气温高达{temp}°C，已达到高温预警标准！\n建议：\n• 避免在中午12点至下午3点进行户外活动\n• 多补充水分，每小时至少饮用200ml水\n• 穿着轻薄透气的衣物\n• 携带遮阳伞或遮阳帽\n• 如有不适请立即前往阴凉处"
    },
    
    # 暴雨预警规则
    "heavy_rain": {
        "name": "暴雨预警",
        "condition": lambda d: d.get("precipitation", 0) > 10 or "暴雨" in d.get("condition", "") or "大雨" in d.get("condition", ""),
        "severity": "danger",
        "message_template": "{city}当前天气为{d_condition}，降水量达{precip}mm！\n建议：\n• 推迟或取消户外行程\n• 避免前往山区、河边等危险区域\n• 携带雨具和防水装备\n• 注意防范城市内涝\n• 如已在室外，请寻找安全的室内场所躲避"
    },
    
    # 空气质量差预警规则
    "poor_air_quality": {
        "name": "空气质量差预警",
        "threshold": 150,  # PM2.5阈值
        "condition": lambda d: d.get("aqi", 0) >= 150,
        "severity": "warning",
        "message_template": "{city}当前空气质量较差，PM2.5浓度为{aqi}μg/m³！\n建议：\n• 佩戴N95或KN95口罩\n• 减少户外活动时间\n• 关闭门窗，开启空气净化器\n• 避免在交通繁忙路段行走\n• 敏感人群（老人、儿童、呼吸道疾病患者）尽量留在室内"
    },
    
    # 强风预警规则
    "strong_wind": {
        "name": "强风预警",
        "threshold": 50,  # 风速阈值（km/h）
        "condition": lambda d: d.get("wind_speed", 0) >= 50,
        "severity": "warning",
        "message_template": "{city}当前风速高达{wind}km/h，请注意防范！\n建议：\n• 远离广告牌、临时搭建物\n• 检查门窗是否牢固\n• 暂停高空作业\n• 驾驶时注意横风影响\n• 如在室外，请寻找安全的室内场所"
    },
    
    # 极端低温预警规则
    "extreme_cold": {
        "name": "极端低温预警",
        "threshold": -10,  # 温度阈值
        "condition": lambda d: d.get("temperature", 0) <= -10,
        "severity": "danger",
        "message_template": "{city}当前气温低至{temp}°C，请做好防寒措施！\n建议：\n• 穿戴羽绒服、保暖内衣、帽子、手套、围巾\n• 多喝热饮，注意保暖\n• 路面结冰需小心滑倒\n• 避免长时间在户外\n• 提前检查供暖设备"
    },
    
    # 连续高温预警规则
    "consecutive_high_temp": {
        "name": "连续高温预警",
        "threshold": 3,  # 连续天数
        "severity": "warning",
        "message_template": "{city}已连续{count}天出现高温天气！\n建议：\n• 继续采取防暑措施\n• 注意防范热射病\n• 关注易感人群状态\n• 合理安排户外工作时间\n• 适时使用空调降温"
    },
    
    # 紫外线强预警规则
    "high_uv": {
        "name": "紫外线强预警",
        "threshold": 8,  # UV指数
        "condition": lambda d: d.get("uv", 0) >= 8,
        "severity": "warning",
        "message_template": "{city}当前紫外线指数高达{uv}，强度极强！\n建议：\n• 涂抹SPF30+防晒霜\n• 佩戴防紫外线的太阳镜\n• 使用遮阳伞或遮阳帽\n• 尽量避免在上午10点至下午4点外出\n• 晒伤后及时使用晒后修复产品"
    },
    
    # 低能见度预警规则
    "low_visibility": {
        "name": "低能见度预警",
        "threshold": 2,  # 能见度（km）
        "condition": lambda d: d.get("visibility", 10) <= 2,
        "severity": "warning",
        "message_template": "{city}当前能见度仅{vis}km，请注意出行安全！\n建议：\n• 驾驶时打开雾灯，保持安全车距\n• 减速慢行，注意行人\n• 公共交通出行更安全\n• 如非必要，减少外出\n• 关注交通管制信息"
    }
}

def check_weather_anomalies(city, weather_data):
    """
    检查天气数据是否触发异常规则
    
    参数:
        city: 城市名称
        weather_data: 天气数据字典
    
    返回:
        list: 触发的告警列表
    """
    triggered_alerts = []
    current_time = datetime.now()
    
    for rule_id, rule in ALERT_RULES.items():
        # 跳过需要历史数据的规则
        if rule_id == "consecutive_high_temp":
            continue
        
        try:
            if rule["condition"](weather_data):
                alert = {
                    "rule_id": rule_id,
                    "alert_type": rule["name"],
                    "city": city,
                    "severity": rule["severity"],
                    "message": rule["message_template"].format(
                        city=city,
                        temp=weather_data.get("temperature", "未知"),
                        aqi=weather_data.get("aqi", "未知"),
                        wind=weather_data.get("wind_speed", "未知"),
                        precip=weather_data.get("precipitation", "未知"),
                        d_condition=weather_data.get("condition", "未知"),
                        uv=weather_data.get("uv", "未知"),
                        vis=weather_data.get("visibility", "未知")
                    ),
                    "timestamp": current_time.isoformat(),
                    "data": weather_data
                }
                triggered_alerts.append(alert)
        except Exception as e:
            print(f"检查规则 {rule_id} 时出错: {e}")
    
    # 检查连续高温
    try:
        consecutive = check_consecutive_high_temp(city, weather_data.get("temperature", 0))
        if consecutive >= 3:
            rule = ALERT_RULES["consecutive_high_temp"]
            alert = {
                "rule_id": "consecutive_high_temp",
                "alert_type": rule["name"],
                "city": city,
                "severity": rule["severity"],
                "message": rule["message_template"].format(
                    city=city,
                    count=consecutive
                ),
                "timestamp": current_time.isoformat(),
                "data": weather_data
            }
            triggered_alerts.append(alert)
    except Exception as e:
        print(f"检查连续高温时出错: {e}")
    
    # 保存告警记录
    for alert in triggered_alerts:
        try:
            save_alert(alert)
        except Exception as e:
            print(f"保存告警失败: {e}")
    
    return triggered_alerts

def check_consecutive_high_temp(city, current_temp):
    """
    检查是否连续高温
    """
    try:
        history = load_weather_history()
        if city not in history:
            return 0
        
        # 获取最近7天的数据
        recent_data = []
        cutoff_time = datetime.now() - timedelta(days=7)
        
        for record in reversed(history[city]):
            record_time = datetime.fromisoformat(record["timestamp"])
            if record_time >= cutoff_time:
                recent_data.append(record)
            else:
                break
        
        # 检查是否连续高温
        consecutive_count = 0
        for record in recent_data:
            temp = record["data"].get("temperature", 0)
            if temp >= 35:
                consecutive_count += 1
            else:
                break
        
        return consecutive_count
    
    except Exception as e:
        print(f"检查连续高温失败: {e}")
        return 0

def get_active_alerts():
    """
    获取当前有效的告警
    """
    try:
        alerts = load_alert_history()
        # 返回最近24小时内的未解决告警
        cutoff_time = datetime.now() - timedelta(hours=24)
        active = []
        
        for alert in reversed(alerts):
            alert_time = datetime.fromisoformat(alert["timestamp"])
            if alert_time >= cutoff_time and not alert.get("resolved", False):
                active.append(alert)
        
        return active
    except Exception as e:
        print(f"获取活跃告警失败: {e}")
        return []

def get_alert_summary():
    """
    获取告警统计摘要
    """
    try:
        alerts = load_alert_history()
        
        # 统计各类型告警数量
        type_counts = {}
        city_counts = {}
        severity_counts = {"warning": 0, "danger": 0, "info": 0}
        
        for alert in alerts:
            alert_type = alert.get("alert_type", "未知")
            city = alert.get("city", "未知")
            severity = alert.get("severity", "warning")
            
            type_counts[alert_type] = type_counts.get(alert_type, 0) + 1
            city_counts[city] = city_counts.get(city, 0) + 1
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        return {
            "total": len(alerts),
            "type_counts": type_counts,
            "city_counts": city_counts,
            "severity_counts": severity_counts,
            "recent_24h": len(get_active_alerts())
        }
    except Exception as e:
        print(f"获取告警摘要失败: {e}")
        return {
            "total": 0,
            "type_counts": {},
            "city_counts": {},
            "severity_counts": {},
            "recent_24h": 0
        }

def generate_alert_notification(alerts):
    """
    生成告警通知文本
    """
    if not alerts:
        return "当前无活跃告警，天气状况良好。"
    
    notification = "⚠️ 天气告警提醒\n\n"
    
    # 按严重程度排序
    danger_alerts = [a for a in alerts if a["severity"] == "danger"]
    warning_alerts = [a for a in alerts if a["severity"] == "warning"]
    
    if danger_alerts:
        notification += "🚨 紧急告警：\n"
        for alert in danger_alerts:
            notification += f"• {alert['alert_type']} - {alert['city']}\n"
        notification += "\n"
    
    if warning_alerts:
        notification += "⚡ 一般警告：\n"
        for alert in warning_alerts[:3]:  # 最多显示3条
            notification += f"• {alert['alert_type']} - {alert['city']}\n"
        if len(warning_alerts) > 3:
            notification += f"• 还有 {len(warning_alerts) - 3} 条其他告警\n"
    
    notification += "\n请根据实际情况采取相应措施。"
    
    return notification