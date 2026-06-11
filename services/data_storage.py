import json
import os
from datetime import datetime

# 使用项目根目录的绝对路径，确保在任何目录下运行都能找到数据文件
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
WEATHER_HISTORY_FILE = os.path.join(DATA_DIR, "weather_history.json")
ALERT_HISTORY_FILE = os.path.join(DATA_DIR, "alert_history.json")

def init_data_dir():
    """初始化数据目录"""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

def save_weather_data(city, weather_data):
    """保存天气数据到历史记录"""
    init_data_dir()
    
    history = load_weather_history()
    
    record = {
        "city": city,
        "data": weather_data,
        "timestamp": datetime.now().isoformat()
    }
    
    if city not in history:
        history[city] = []
    
    history[city].append(record)
    
    # 保留最近30天的数据
    if len(history[city]) > 30:
        history[city] = history[city][-30:]
    
    with open(WEATHER_HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

def load_weather_history():
    """加载天气历史数据"""
    init_data_dir()
    
    if not os.path.exists(WEATHER_HISTORY_FILE):
        return {}
    
    try:
        with open(WEATHER_HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def save_alert(alert_data):
    """保存告警记录"""
    init_data_dir()
    
    history = load_alert_history()
    
    record = {
        "alert_type": alert_data["alert_type"],
        "city": alert_data["city"],
        "message": alert_data["message"],
        "severity": alert_data["severity"],
        "timestamp": datetime.now().isoformat(),
        "resolved": False
    }
    
    history.append(record)
    
    # 保留最近100条告警
    if len(history) > 100:
        history = history[-100:]
    
    with open(ALERT_HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

def load_alert_history():
    """加载告警历史"""
    init_data_dir()
    
    if not os.path.exists(ALERT_HISTORY_FILE):
        return []
    
    try:
        with open(ALERT_HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []

def get_daily_summary(city, date_str=None):
    """获取指定日期的天气汇总"""
    history = load_weather_history()
    
    if city not in history:
        return None
    
    if date_str is None:
        date_str = datetime.now().strftime("%Y-%m-%d")
    
    day_records = []
    for record in history[city]:
        if record["timestamp"].startswith(date_str):
            day_records.append(record)
    
    if not day_records:
        return None
    
    # 计算统计值
    temps = []
    humidities = []
    aqis = []
    
    for record in day_records:
        data = record["data"]
        if "temperature" in data:
            temps.append(data["temperature"])
        if "humidity" in data:
            humidities.append(data["humidity"])
        if "aqi" in data:
            aqis.append(data["aqi"])
    
    return {
        "date": date_str,
        "record_count": len(day_records),
        "avg_temp": round(sum(temps)/len(temps), 1) if temps else None,
        "max_temp": max(temps) if temps else None,
        "min_temp": min(temps) if temps else None,
        "avg_humidity": round(sum(humidities)/len(humidities), 1) if humidities else None,
        "avg_aqi": round(sum(aqis)/len(aqis), 1) if aqis else None,
        "records": day_records
    }