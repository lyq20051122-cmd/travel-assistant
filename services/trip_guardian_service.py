"""
主动式行程守护者 (Proactive Trip Guardian)
============================================
特色功能二：从"被动问答"到"主动守护"的模式升级

核心能力：
- 三阶段守护模型（行前预判 / 行中实时守护 / 行后经验沉淀）
- 行程-天气冲突检测矩阵（室内/户外/混合 × 天气指标）
- 个性化替代方案生成管道
- 推送节流机制（防骚扰）
- 与旅行人格画像引擎联动
"""
import json
import os
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple

# 数据文件路径（使用绝对路径，确保在任何目录下运行都能找到）
GUARDIAN_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
TRIPS_FILE = os.path.join(GUARDIAN_DATA_DIR, 'active_trips.json')
GUARDIAN_LOG_FILE = os.path.join(GUARDIAN_DATA_DIR, 'guardian_log.json')

# 行程活动类型分类
ACTIVITY_CATEGORIES = {
    # 户外活动
    'outdoor': [
        '景点游览', '徒步登山', '自然风光', '户外摄影', '海滩活动',
        '漂流', '滑雪', '骑行', '露营', '野餐', '攀岩', '蹦极',
        '水上乐园', '动物园', '植物园', '主题公园户外', '城市漫步',
        '古城游览', '夜景观光', '热气球', '跳伞', '冲浪', '潜水',
        '操场运动', '高尔夫', '钓鱼', '皮划艇'
    ],
    # 室内活动
    'indoor': [
        '博物馆', '美术馆', '科技馆', '水族馆', '电影院', '剧院',
        '购物', 'SPA', '温泉', '健身房', '图书馆', '网吧',
        '桌游', '密室逃脱', 'VR体验', '烹饪课', '陶艺工坊',
        '酒店休息', '商场逛街', '美食体验', '咖啡厅', '酒吧',
        '音乐厅', '演唱会', 'livehouse', '会议', '培训'
    ],
    # 混合（可能是室内或室外）
    'mixed': [
        '自由活动', '交通换乘', '自由探索', '当地体验', '夜市',
        '古镇漫步', '美食街'
    ]
}


def classify_activity(activity_name: str) -> str:
    """判断活动类型：outdoor / indoor / mixed"""
    for category, activities in ACTIVITY_CATEGORIES.items():
        for act in activities:
            if act in activity_name or activity_name in act:
                return category
    # 默认按名称推断
    outdoor_keywords = ['山', '海', '公园', '徒步', '骑行', '户外', '滩', '湖', '河', '岛', '峰']
    indoor_keywords = ['博物馆', '馆', '厅', '影院', '商场', '店', '室内', 'SPA']
    for kw in outdoor_keywords:
        if kw in activity_name:
            return 'outdoor'
    for kw in indoor_keywords:
        if kw in activity_name:
            return 'indoor'
    return 'mixed'


def calculate_conflict_index(activity: Dict, weather: Dict) -> float:
    """
    计算行程-天气冲突指数 (0-1)
    1.0 = 严重冲突（必须调整），0 = 无冲突
    """
    conflict_score = 0.0
    activity_type = classify_activity(activity.get('place', '') + activity.get('activity', ''))

    temp = weather.get('temperature', 25)
    precip = weather.get('precipitation', 0)
    wind = weather.get('wind_speed', 10)
    condition = weather.get('condition', '')
    uv = weather.get('uv', 5)
    visibility = weather.get('visibility', 10)

    # 户外活动 + 降水 → 高冲突
    if activity_type == 'outdoor' and (precip > 1 or '雨' in condition or '雪' in condition):
        conflict_score += 0.6 if precip > 5 else 0.3

    # 户外活动 + 高温 → 中高冲突
    if activity_type == 'outdoor' and temp >= 35:
        conflict_score += 0.5
    elif activity_type == 'outdoor' and temp >= 32:
        conflict_score += 0.3

    # 户外活动 + 强风 → 中等冲突
    if activity_type == 'outdoor' and wind >= 40:
        conflict_score += 0.4
    elif activity_type == 'outdoor' and wind >= 30:
        conflict_score += 0.2

    # 户外活动 + 极端低温 → 中高冲突
    if activity_type == 'outdoor' and temp <= -5:
        conflict_score += 0.5
    elif activity_type == 'outdoor' and temp <= 0:
        conflict_score += 0.3

    # 户外活动 + 高紫外线 → 轻度冲突
    if activity_type == 'outdoor' and uv >= 8:
        conflict_score += 0.2

    # 户外活动 + 低能见度 → 中度冲突
    if activity_type == 'outdoor' and visibility <= 2:
        conflict_score += 0.4

    # 任何活动 + 极端天气 → 极高冲突
    if '暴雨' in condition or '台风' in condition or '暴雪' in condition:
        conflict_score += 0.3

    return min(1.0, conflict_score)


class ActiveTrip:
    """活跃行程"""

    def __init__(self, trip_id: str, user_id: str, destination: str,
                 start_date: str, end_date: str, days_plan: List[Dict]):
        self.trip_id = trip_id
        self.user_id = user_id
        self.destination = destination
        self.start_date = start_date
        self.end_date = end_date
        self.days_plan = days_plan  # 每天的行程安排
        self.created_at = datetime.now().isoformat()
        self.push_count: Dict[str, int] = {}  # {event_key: count} 用于节流
        self.last_push_time: Optional[str] = None
        self.guardian_phase = 'pre_trip'  # pre_trip / in_trip / post_trip
        self.intervention_log: List[Dict] = []
        self.status = 'active'

    def to_dict(self) -> Dict:
        return {
            'trip_id': self.trip_id,
            'user_id': self.user_id,
            'destination': self.destination,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'days_plan': self.days_plan,
            'created_at': self.created_at,
            'push_count': self.push_count,
            'last_push_time': self.last_push_time,
            'guardian_phase': self.guardian_phase,
            'intervention_log': self.intervention_log,
            'status': self.status
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'ActiveTrip':
        trip = cls(
            data['trip_id'], data['user_id'], data['destination'],
            data['start_date'], data['end_date'], data['days_plan']
        )
        trip.created_at = data.get('created_at', trip.created_at)
        trip.push_count = data.get('push_count', {})
        trip.last_push_time = data.get('last_push_time')
        trip.guardian_phase = data.get('guardian_phase', 'pre_trip')
        trip.intervention_log = data.get('intervention_log', [])
        trip.status = data.get('status', 'active')
        return trip


class TripGuardianService:
    """主动式行程守护者服务"""

    def __init__(self):
        self._trips: Dict[str, ActiveTrip] = {}
        self._guardian_log: List[Dict] = []
        self._running = False
        self._thread = None
        self._check_interval = 1800  # 30分钟检查间隔
        self._max_pushes_per_event = 2  # 同一事件最多推送2次
        self._push_cooldown_minutes = 60  # 推送冷静期（分钟）
        self._load()

    def _load(self):
        """加载行程和日志"""
        try:
            os.makedirs(GUARDIAN_DATA_DIR, exist_ok=True)
            if os.path.exists(TRIPS_FILE):
                with open(TRIPS_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                for trip_id, trip_data in data.items():
                    self._trips[trip_id] = ActiveTrip.from_dict(trip_data)
            if os.path.exists(GUARDIAN_LOG_FILE):
                with open(GUARDIAN_LOG_FILE, 'r', encoding='utf-8') as f:
                    self._guardian_log = json.load(f)
        except Exception as e:
            print(f"[TripGuardian] 加载失败: {e}")

    def _save(self):
        """保存行程和日志"""
        try:
            os.makedirs(GUARDIAN_DATA_DIR, exist_ok=True)
            trips_data = {tid: t.to_dict() for tid, t in self._trips.items()}
            with open(TRIPS_FILE, 'w', encoding='utf-8') as f:
                json.dump(trips_data, f, ensure_ascii=False, indent=2)
            with open(GUARDIAN_LOG_FILE, 'w', encoding='utf-8') as f:
                json.dump(self._guardian_log[-100:], f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[TripGuardian] 保存失败: {e}")

    # ===== 行程管理 =====

    def register_trip(self, user_id: str, destination: str, start_date: str,
                      end_date: str, days_plan: List[Dict]) -> str:
        """注册新行程"""
        trip_id = f"trip_{user_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"

        # 取消用户之前的活跃行程
        for tid, trip in list(self._trips.items()):
            if trip.user_id == user_id and trip.status == 'active':
                trip.status = 'completed'

        trip = ActiveTrip(trip_id, user_id, destination, start_date, end_date, days_plan)
        self._trips[trip_id] = trip
        self._save()

        self._log('trip_registered', trip_id, f"用户{user_id}注册了{destination}行程({start_date}-{end_date})")
        return trip_id

    def get_trip(self, trip_id: str) -> Optional[ActiveTrip]:
        """获取行程"""
        return self._trips.get(trip_id)

    def get_user_active_trip(self, user_id: str) -> Optional[ActiveTrip]:
        """获取用户当前活跃行程"""
        for trip in self._trips.values():
            if trip.user_id == user_id and trip.status == 'active':
                return trip
        return None

    def complete_trip(self, trip_id: str) -> bool:
        """完成行程"""
        if trip_id in self._trips:
            self._trips[trip_id].status = 'completed'
            self._trips[trip_id].guardian_phase = 'post_trip'
            self._save()
            return True
        return False

    # ===== 三阶段守护模型 =====

    def phase1_pre_trip_check(self, trip_id: str) -> Dict:
        """
        阶段一：行前智能预判（出发前3-7天）
        - 检查目的地天气预报
        - 生成差异化准备建议
        - 结合用户画像决定推送策略
        """
        trip = self.get_trip(trip_id)
        if not trip:
            return {'success': False, 'message': '行程不存在'}

        try:
            from services.weather_service import get_weather_forecast
            forecast = get_weather_forecast(trip.destination, days=7)
        except Exception as e:
            return {'success': False, 'message': f'获取天气预报失败: {e}'}

        recommendations = []
        alerts = []

        # 分析天气预报
        if forecast and 'forecast' in forecast:
            forecast_days = forecast.get('forecast', [])
        else:
            # 尝试获取当前天气
            try:
                from services.weather_service import get_weather
                current = get_weather(trip.destination)
                forecast_days = [{'date': trip.start_date, 'day': {'condition': {'text': '未知'},
                                  'maxtemp_c': 25, 'mintemp_c': 15, 'daily_chance_of_rain': 0}}]
            except Exception:
                forecast_days = []

        # 在目的地期间天气预报中检测问题
        rain_days = 0
        high_temp_days = 0
        cold_days = 0

        for day in forecast_days:
            day_info = day.get('day', {})
            condition = day_info.get('condition', {}).get('text', '')
            max_temp = day_info.get('maxtemp_c', 25)
            min_temp = day_info.get('mintemp_c', 15)
            rain_chance = day_info.get('daily_chance_of_rain', 0)

            if rain_chance > 50 or '雨' in condition:
                rain_days += 1
            if max_temp >= 35:
                high_temp_days += 1
            if min_temp <= 0:
                cold_days += 1

        # 生成建议
        if rain_days >= 2:
            alerts.append({
                'type': 'rain_warning',
                'severity': 'warning',
                'message': f'{trip.destination}在行程期间预计有{rain_days}天下雨，建议携带雨具和防水装备'
            })
            recommendations.append({
                'category': 'packing',
                'items': ['雨伞/雨衣', '防水鞋', '防水背包罩', '快干衣物'],
                'reason': f'预计{rain_days}天降雨'
            })

            # 推荐室内备选景点
            try:
                from services.linkage_service import INDOOR_SPOTS
                indoor = INDOOR_SPOTS.get(trip.destination, ['博物馆', '美术馆', '商场'])
                recommendations.append({
                    'category': 'indoor_alternatives',
                    'spots': indoor[:5],
                    'reason': '雨天室内备选方案'
                })
            except Exception:
                pass

        if high_temp_days >= 2:
            alerts.append({
                'type': 'high_temp_warning',
                'severity': 'warning',
                'message': f'{trip.destination}预计有{high_temp_days}天高温（≥35°C），请做好防暑准备'
            })
            recommendations.append({
                'category': 'heat_protection',
                'items': ['防晒霜SPF30+', '遮阳帽', '太阳镜', '便携风扇', '大容量水壶'],
                'reason': f'预计{high_temp_days}天高温'
            })

        if cold_days >= 1:
            alerts.append({
                'type': 'cold_warning',
                'severity': 'warning',
                'message': f'{trip.destination}气温较低（≤0°C），请注意保暖'
            })
            recommendations.append({
                'category': 'cold_protection',
                'items': ['羽绒服', '保暖内衣', '手套围巾', '暖宝宝'],
                'reason': f'最低温≤0°C'
            })

        # 通用建议
        recommendations.append({
            'category': 'general',
            'items': ['身份证/护照', '手机充电器', '常用药品', '现金/银行卡'],
            'reason': '出行必备'
        })

        # 结合用户画像
        persona_context = ''
        try:
            from services.persona_service import persona_service as ps
            persona = ps.get_persona(trip.user_id)
            if persona:
                persona_context = persona.get_persona_summary()
                # 根据风险偏好调整提醒频率
                if persona.risk_preference == 'conservative':
                    alerts.append({
                        'type': 'conservative_note',
                        'severity': 'info',
                        'message': '根据您的偏好，建议购买旅行保险并保存紧急联系方式'
                    })
        except Exception:
            pass

        result = {
            'success': True,
            'phase': 'pre_trip',
            'destination': trip.destination,
            'date_range': f'{trip.start_date} ~ {trip.end_date}',
            'alerts': alerts,
            'recommendations': recommendations,
            'weather_summary': {
                'rain_days': rain_days,
                'high_temp_days': high_temp_days,
                'cold_days': cold_days,
                'total_days': len(forecast_days)
            },
            'persona_context': persona_context
        }

        self._log('pre_trip_check', trip_id, f"行前检查完成：{len(alerts)}条提醒，{len(recommendations)}条建议")
        return result

    def phase2_realtime_monitoring(self, trip_id: str, current_weather: Dict = None) -> Dict:
        """
        阶段二：行中实时动态守护
        - 检查当前天气与行程活动的冲突
        - 生成个性化替代方案
        - 推送节流控制
        """
        trip = self.get_trip(trip_id)
        if not trip:
            return {'success': False, 'message': '行程不存在'}

        now = datetime.now()
        today_str = now.strftime('%Y-%m-%d')

        # 确定当前是哪一天的行程
        current_day_plan = None
        current_day_index = 0
        for i, day_plan in enumerate(trip.days_plan):
            if day_plan.get('date', '') == today_str:
                current_day_plan = day_plan
                current_day_index = i
                break

        if not current_day_plan:
            # 用日期匹配
            start = datetime.fromisoformat(trip.start_date)
            day_offset = (now - start).days
            if 0 <= day_offset < len(trip.days_plan):
                current_day_plan = trip.days_plan[day_offset]
                current_day_index = day_offset

        if not current_day_plan:
            return {'success': True, 'message': '今天没有行程安排', 'interventions': []}

        # 获取当前天气
        if current_weather is None:
            try:
                from services.weather_service import get_weather
                weather_result = get_weather(trip.destination)
                current_weather = {
                    'temperature': 25,
                    'precipitation': 0,
                    'wind_speed': 10,
                    'condition': '晴',
                    'uv': 5,
                    'visibility': 10,
                    'humidity': 50
                }
            except Exception:
                current_weather = {
                    'temperature': 25, 'precipitation': 0, 'wind_speed': 10,
                    'condition': '晴', 'uv': 5, 'visibility': 10, 'humidity': 50
                }

        interventions = []

        # 检查每一个时段的活动
        for period in ['morning', 'afternoon', 'evening']:
            activity = current_day_plan.get(period)
            if not activity:
                continue

            conflict_index = calculate_conflict_index(activity, current_weather)

            if conflict_index >= 0.5:  # 冲突指数>=0.5 → 需要干预
                event_key = f"{today_str}_{period}_{activity.get('place', '')}"

                # 推送节流检查
                if not self._can_push(trip, event_key):
                    continue

                # 生成个性化替代方案
                alternatives = self._generate_alternatives(
                    user_id=trip.user_id,
                    destination=trip.destination,
                    activity=activity,
                    period=period,
                    weather=current_weather
                )

                intervention = {
                    'period': period,
                    'activity': activity,
                    'conflict_index': round(conflict_index, 2),
                    'weather_issue': self._describe_weather_issue(current_weather, activity),
                    'alternatives': alternatives,
                    'timestamp': now.isoformat(),
                    'event_key': event_key
                }

                interventions.append(intervention)
                trip.intervention_log.append(intervention)
                trip.push_count[event_key] = trip.push_count.get(event_key, 0) + 1
                trip.last_push_time = now.isoformat()

        if interventions:
            self._save()
            self._log('realtime_intervention', trip_id,
                      f"触发{len(interventions)}项干预，天气: {current_weather.get('condition')}")

        return {
            'success': True,
            'phase': 'in_trip',
            'date': today_str,
            'weather': current_weather,
            'interventions': interventions,
            'total_interventions_today': len(interventions)
        }

    def phase3_post_trip_summary(self, trip_id: str) -> Dict:
        """
        阶段三：行后经验沉淀
        - 生成旅行回顾
        - 偏好验证/修正提示
        - 画像更新建议
        """
        trip = self.get_trip(trip_id)
        if not trip:
            return {'success': False, 'message': '行程不存在'}

        # 统计干预日志
        total_interventions = len(trip.intervention_log)
        interventions_by_type = {}
        for intervention in trip.intervention_log:
            itype = intervention.get('weather_issue', 'unknown')
            interventions_by_type[itype] = interventions_by_type.get(itype, 0) + 1

        # 生成回顾卡片
        weather_rating = '良好'
        if total_interventions >= 3:
            weather_rating = '天气多变，建议下次选择更稳定的季节'
        elif total_interventions >= 1:
            weather_rating = '偶有波折，总体顺利'
        else:
            weather_rating = '天气完美，旅途顺利'

        # 偏好验证提示
        preference_prompts = []
        try:
            from services.persona_service import persona_service as ps
            persona = ps.get_persona(trip.user_id)
            if persona:
                top_interests = persona.get_top_interests(3)
                if top_interests:
                    pref_prompts.append({
                        'type': 'interest_validation',
                        'question': f'本次{trip.destination}之行后，您对{top_interests[0][0]}的兴趣是否有所变化？',
                        'current_weight': top_interests[0][1]
                    })
        except Exception:
            pass

        summary = {
            'success': True,
            'phase': 'post_trip',
            'destination': trip.destination,
            'date_range': f'{trip.start_date} ~ {trip.end_date}',
            'trip_summary': {
                'total_days': len(trip.days_plan),
                'total_interventions': total_interventions,
                'weather_rating': weather_rating,
                'intervention_breakdown': interventions_by_type,
                'intervention_log': trip.intervention_log[-10:]  # 最近10条
            },
            'preference_prompts': preference_prompts,
            'guardian_tips': [
                f'本次行程共{trip.days_plan}天，系统为您提供了{total_interventions}次实时建议',
                weather_rating,
                '您的偏好已根据本次行程自动更新'
            ]
        }

        # 标记行程完成
        self.complete_trip(trip_id)
        self._log('post_trip_summary', trip_id, f"行程回顾生成完成，{total_interventions}次干预")

        return summary

    # ===== 辅助方法 =====

    def _can_push(self, trip: ActiveTrip, event_key: str) -> bool:
        """检查是否可以推送（节流控制）"""
        # 同一事件最多推送2次
        if trip.push_count.get(event_key, 0) >= self._max_pushes_per_event:
            return False

        # 推送冷静期
        if trip.last_push_time:
            last = datetime.fromisoformat(trip.last_push_time)
            if (datetime.now() - last).seconds < self._push_cooldown_minutes * 60:
                return False

        return True

    def _generate_alternatives(self, user_id: str, destination: str,
                               activity: Dict, period: str, weather: Dict) -> List[Dict]:
        """生成个性化替代方案"""
        alternatives = []

        # 获取用户画像
        persona_interests = []
        try:
            from services.persona_service import persona_service as ps
            persona = ps.get_persona(user_id)
            if persona:
                persona_interests = [tag for tag, _ in persona.get_top_interests(5)]
        except Exception:
            pass

        # 获取城市室内景点
        indoor_spots = []
        try:
            from services.linkage_service import INDOOR_SPOTS
            indoor_spots = INDOOR_SPOTS.get(destination, [])
        except Exception:
            indoor_spots = []

        activity_type = classify_activity(activity.get('place', '') + activity.get('activity', ''))

        if activity_type == 'outdoor' and indoor_spots:
            # 户外→室内替代
            for spot in indoor_spots[:3]:
                # 检查是否匹配用户兴趣
                match_score = 0
                for interest in persona_interests:
                    interest_keywords = {
                        'history': ['历史', '博物', '古迹', '故居'],
                        'culture': ['文化', '民俗', '博馆'],
                        'museum': ['博物馆', '美术馆', '展览'],
                        'art': ['艺术', '画廊', '创意'],
                        'food': ['美食', '小吃', '街', '坊'],
                        'shopping': ['商场', '购物', '商圈', '步行街'],
                        'architecture': ['建筑', '设计'],
                    }
                    keywords = interest_keywords.get(interest, [])
                    for kw in keywords:
                        if kw in spot:
                            match_score += 1
                            break

                alternatives.append({
                    'place': spot,
                    'type': 'indoor_alternative',
                    'match_score': match_score,
                    'reason': f'替代户外活动"{activity.get("place", "")}"，'
                             f'天气: {weather.get("condition", "")}, {weather.get("temperature", "?")}°C'
                })

            # 按匹配度排序
            alternatives.sort(key=lambda x: x['match_score'], reverse=True)

        if not alternatives:
            # 通用替代方案
            default_alternatives = [
                {'place': '当地博物馆', 'type': 'general_indoor', 'match_score': 1,
                 'reason': '室内文化活动，不受天气影响'},
                {'place': '特色美食街', 'type': 'general_indoor', 'match_score': 1,
                 'reason': '品尝当地美食，室内外均可'},
                {'place': '购物中心', 'type': 'general_indoor', 'match_score': 0,
                 'reason': '舒适购物体验，完全室内'},
            ]
            alternatives.extend(default_alternatives)

        return alternatives[:3]

    def _describe_weather_issue(self, weather: Dict, activity: Dict) -> str:
        """描述天气问题"""
        issues = []
        temp = weather.get('temperature', 25)
        precip = weather.get('precipitation', 0)
        wind = weather.get('wind_speed', 10)
        condition = weather.get('condition', '')
        uv = weather.get('uv', 5)

        activity_type = classify_activity(activity.get('place', '') + activity.get('activity', ''))

        if activity_type == 'outdoor':
            if precip > 0 or '雨' in condition:
                issues.append(f'{condition}天气不适合户外活动')
            if temp >= 35:
                issues.append(f'高温{temp}°C')
            if temp <= 0:
                issues.append(f'低温{temp}°C')
            if wind >= 30:
                issues.append(f'强风{wind}km/h')
            if uv >= 8:
                issues.append(f'强紫外线UV{uv}')

        return '；'.join(issues) if issues else '天气条件一般'

    def check_all_active_trips(self) -> List[Dict]:
        """检查所有活跃行程（供后台线程调用）"""
        results = []
        for trip_id, trip in self._trips.items():
            if trip.status != 'active':
                continue

            result = self.phase2_realtime_monitoring(trip_id)
            if result.get('interventions'):
                results.append({
                    'trip_id': trip_id,
                    'user_id': trip.user_id,
                    'destination': trip.destination,
                    'interventions': result['interventions']
                })

        return results

    # ===== 后台服务 =====

    def start_background_monitoring(self):
        """启动后台监控"""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run_monitoring, daemon=True)
        self._thread.start()
        self._log('service_started', 'system', '行程守护者后台监控已启动')

    def stop_background_monitoring(self):
        """停止后台监控"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)

    def _run_monitoring(self):
        """后台监控循环"""
        while self._running:
            try:
                results = self.check_all_active_trips()
                if results:
                    self._log('background_check', 'system',
                              f'后台检查完成：{len(results)}个行程需要干预')
            except Exception as e:
                print(f"[TripGuardian] 后台监控异常: {e}")
            time.sleep(self._check_interval)

    # ===== 日志 =====

    def _log(self, event_type: str, trip_id: str, message: str):
        """记录日志"""
        entry = {
            'event_type': event_type,
            'trip_id': trip_id,
            'message': message,
            'timestamp': datetime.now().isoformat()
        }
        self._guardian_log.append(entry)
        # 每10条日志保存一次
        if len(self._guardian_log) % 10 == 0:
            self._save()

    def get_guardian_log(self, limit: int = 50) -> List[Dict]:
        """获取守护者日志"""
        return self._guardian_log[-limit:]

    def get_guardian_status(self) -> Dict:
        """获取守护者状态"""
        return {
            'running': self._running,
            'active_trips': sum(1 for t in self._trips.values() if t.status == 'active'),
            'total_trips': len(self._trips),
            'check_interval_seconds': self._check_interval,
            'total_interventions': sum(len(t.intervention_log) for t in self._trips.values())
        }


# 全局单例
trip_guardian_service = TripGuardianService()
