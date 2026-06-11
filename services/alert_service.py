"""
智能安全提醒服务（主动服务特性）
基于天气预警和安全信息，主动向用户推送提醒
"""
from datetime import datetime, timedelta
from services.data_storage import load_alert_history, save_alert, load_weather_history
from services.anomaly_detection import check_weather_anomalies, get_active_alerts
import threading
import time

class AlertService:
    """主动提醒服务"""
    
    def __init__(self):
        self.alert_queue = []
        self.subscribers = []
        self.running = False
        self.thread = None
        self.check_interval = 3600  # 检查间隔（秒）
    
    def start(self):
        """启动提醒服务"""
        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
    
    def stop(self):
        """停止提醒服务"""
        self.running = False
        if self.thread:
            self.thread.join()
    
    def _run(self):
        """后台运行逻辑"""
        while self.running:
            self.check_and_send_alerts()
            time.sleep(self.check_interval)
    
    def check_and_send_alerts(self):
        """检查并发送提醒"""
        # 检查天气异常
        active_alerts = get_active_alerts()
        
        for alert in active_alerts:
            if not alert.get('notified', False):
                self.send_alert(alert)
                # 标记为已通知
                alert['notified'] = True
                save_alert(alert)
    
    def send_alert(self, alert):
        """发送提醒"""
        alert_message = format_alert_message(alert)
        
        # 添加到提醒队列
        self.alert_queue.append({
            'id': alert.get('id', str(time.time())),
            'type': alert.get('alert_type', 'info'),
            'message': alert_message,
            'city': alert.get('city', ''),
            'timestamp': datetime.now().isoformat(),
            'urgency': alert.get('severity', 'low')
        })
        
        # 通知所有订阅者
        for subscriber in self.subscribers:
            try:
                subscriber(alert_message)
            except Exception as e:
                print(f"通知订阅者失败: {e}")
    
    def subscribe(self, callback):
        """订阅提醒"""
        if callback not in self.subscribers:
            self.subscribers.append(callback)
    
    def unsubscribe(self, callback):
        """取消订阅"""
        if callback in self.subscribers:
            self.subscribers.remove(callback)
    
    def get_pending_alerts(self):
        """获取待处理的提醒"""
        return list(self.alert_queue)
    
    def acknowledge_alert(self, alert_id):
        """确认提醒"""
        self.alert_queue = [a for a in self.alert_queue if a['id'] != alert_id]
    
    def acknowledge_all(self):
        """确认所有提醒"""
        self.alert_queue.clear()

def format_alert_message(alert):
    """格式化提醒消息"""
    alert_type = alert.get('alert_type', '未知')
    city = alert.get('city', '未知城市')
    message = alert.get('message', '')
    severity = alert.get('severity', 'low')
    
    severity_icon = {
        'low': 'ℹ️',
        'warning': '⚠️',
        'high': '🚨',
        'critical': '🔴'
    }
    
    type_descriptions = {
        '高温预警': '高温预警',
        '暴雨预警': '暴雨预警',
        '空气质量预警': '空气质量预警',
        '强风预警': '强风预警',
        '低温预警': '低温预警',
        '紫外线预警': '紫外线预警',
        '能见度预警': '能见度预警',
        '连续高温预警': '连续高温预警'
    }
    
    icon = severity_icon.get(severity, 'ℹ️')
    type_desc = type_descriptions.get(alert_type, alert_type)
    
    return f"{icon}【{type_desc}】{city}: {message}"

def schedule_daily_weather_brief(user_id=None):
    """
    定时发送每日天气简报
    
    Returns:
        每日简报内容
    """
    today = datetime.now()
    date_str = today.strftime('%Y年%m月%d日')
    
    # 获取今日天气数据
    weather_history = load_weather_history()
    
    brief = f"📅 {date_str} 每日天气简报\n\n"
    brief += "="*40 + "\n\n"
    
    # 获取今日活跃告警
    alerts = get_active_alerts()
    active_count = len(alerts)
    
    brief += f"🌤️ 今日天气概览\n"
    brief += f"• 监测城市：{len(weather_history)}个\n"
    brief += f"• 活跃告警：{active_count}条\n\n"
    
    # 显示部分城市天气
    if weather_history:
        brief += "主要城市天气：\n"
        cities_shown = 0
        for city, records in list(weather_history.items())[:5]:
            if records:
                latest = records[-1]
                temp = latest['data'].get('temperature', '?')
                condition = latest['data'].get('condition', '未知')
                brief += f"• {city}：{condition} {temp}°C\n"
                cities_shown += 1
                if cities_shown >= 5:
                    break
    
    # 显示活跃告警
    if alerts:
        brief += "\n⚠️ 今日告警：\n"
        for alert in alerts[:3]:
            brief += f"• {alert['city']}：{alert['alert_type']}\n"
    
    # 添加出行建议
    brief += "\n💡 今日建议："
    if active_count > 0:
        brief += "今日有告警信息，请关注天气变化，注意出行安全。"
    else:
        brief += "今日天气良好，适合出行！"
    
    brief += "\n\n" + "="*40 + "\n"
    brief += "祝您旅途愉快！✈️"
    
    return brief

def generate_travel_reminder(destination, date, user_preferences=None):
    """
    生成旅行前提醒
    
    Args:
        destination: 目的地
        date: 出发日期
        user_preferences: 用户偏好（可选）
    
    Returns:
        提醒消息
    """
    reminder = f"📢 旅行提醒\n\n"
    reminder += f"您即将前往 {destination}！\n"
    reminder += f"出发日期：{date}\n\n"
    
    # 添加准备清单
    reminder += "📋 出行准备清单：\n"
    reminder += "• 身份证/护照\n"
    reminder += "• 机票/火车票\n"
    reminder += "• 酒店预订确认\n"
    reminder += "• 换洗衣物\n"
    reminder += "• 手机充电器\n"
    reminder += "• 常用药品\n"
    
    # 根据偏好添加建议
    if user_preferences:
        if 'nature' in user_preferences.get('interests', []):
            reminder += "• 舒适的步行鞋\n"
        if user_preferences.get('budget') == 'low':
            reminder += "• 交通卡/零钱\n"
    
    reminder += "\n🌡️ 建议关注目的地天气预报"
    reminder += "\n\n祝您旅途顺利！🌍"
    
    return reminder

def check_trip_conflicts(trip_date, user_id=None):
    """
    检查旅行日期是否有冲突（如恶劣天气）
    
    Args:
        trip_date: 旅行日期
        user_id: 用户ID（可选）
    
    Returns:
        冲突信息列表
    """
    conflicts = []
    
    # 检查是否有即将到来的天气预警
    alerts = get_active_alerts()
    
    for alert in alerts:
        # 简化检查：如果当前有高等级告警，提示用户注意
        if alert.get('severity') in ['high', 'critical']:
            conflicts.append({
                'type': 'weather_alert',
                'city': alert['city'],
                'message': f"{alert['alert_type']}：{alert['message']}",
                'severity': alert['severity']
            })
    
    return conflicts

# 全局提醒服务实例
alert_service = AlertService()
