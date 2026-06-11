"""
旅行人格画像引擎 (Travel Persona Engine)
==========================================
特色功能一：构建多维用户画像，实现从"关键词匹配"到"深度理解用户"的跨越

核心能力：
- 7维用户模型（兴趣向量/旅行风格/风险偏好/预算敏感度/节奏偏好/社交倾向/季节偏好）
- 三层偏好提取（显式声明/隐式推理/反馈校准）
- 指数衰减演化模型（30天未强化→衰减至50%）
- 画像驱动的个性化过滤与排序
"""
import json
import os
import math
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any

# 数据文件路径（使用绝对路径，确保在任何目录下运行都能找到）
PERSONA_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
PERSONA_FILE = os.path.join(PERSONA_DATA_DIR, 'user_personas.json')

# 兴趣标签库（30+标签）
INTEREST_TAGS = [
    # 自然类
    'nature', 'beach', 'mountain', 'lake', 'forest', 'desert', 'snow', 'island',
    # 人文类
    'history', 'culture', 'museum', 'architecture', 'religion', 'art',
    # 美食类
    'food', 'street_food', 'fine_dining', 'local_cuisine', 'tea', 'wine',
    # 活动类
    'hiking', 'photography', 'shopping', 'sightseeing', 'adventure', 'sports',
    # 休闲类
    'relax', 'spa', 'hot_spring', 'nightlife', 'entertainment',
    # 亲子类
    'family_friendly', 'theme_park', 'zoo', 'education'
]

# 旅行风格频谱
TRAVEL_STYLES = [
    'intensive',       # 特种兵式：一天8个景点
    'active',          # 活跃型：一天5-6个景点
    'balanced',        # 均衡型：一天3-4个景点
    'relaxed',         # 悠闲型：一天2-3个景点
    'slow_paced'       # 慢节奏度假：一天1-2个景点
]

# 风险偏好
RISK_PREFERENCES = ['conservative', 'moderate', 'adventurous']

# 预算等级
BUDGET_LEVELS = ['low', 'medium', 'high']

# 社交倾向
SOCIAL_TENDENCIES = ['solo', 'couple', 'small_group', 'large_group', 'family']

# 季节
SEASONS = ['spring', 'summer', 'autumn', 'winter']

# 消费类别
EXPENSE_CATEGORIES = ['dining', 'accommodation', 'transport', 'attractions', 'shopping', 'other']

# 衰减参数
DECAY_HALF_LIFE_DAYS = 30  # 30天半衰期
DECAY_LAMBDA = math.log(2) / DECAY_HALF_LIFE_DAYS


class TravelPersona:
    """单个用户的旅行人格画像"""

    def __init__(self, user_id: str):
        self.user_id = user_id
        self.created_at = datetime.now().isoformat()
        self.updated_at = datetime.now().isoformat()

        # 维度1：兴趣向量 {tag: weight, ...}，权重范围0-1
        self.interests: Dict[str, float] = {}

        # 维度2：旅行风格 (travel_styles中的值)
        self.travel_style: str = 'balanced'
        self.travel_style_confidence: float = 0.3  # 置信度0-1

        # 维度3：风险偏好
        self.risk_preference: str = 'moderate'
        self.risk_preference_confidence: float = 0.3

        # 维度4：预算敏感度 {category: elasticity_coefficient}
        # 弹性系数：>1表示对该类消费敏感（倾向省钱），<1表示不敏感（愿意花钱）
        self.budget_sensitivity: Dict[str, float] = {
            cat: 1.0 for cat in EXPENSE_CATEGORIES
        }
        self.budget_level: str = 'medium'

        # 维度5：节奏偏好 {min_attractions_per_day, max_attractions_per_day}
        self.pace_preference: Dict[str, int] = {
            'min_per_day': 2,
            'max_per_day': 4
        }

        # 维度6：社交倾向
        self.social_tendency: str = 'small_group'
        self.social_confidence: float = 0.3

        # 维度7：季节偏好 {season: count}
        self.seasonal_preference: Dict[str, float] = {
            season: 0.25 for season in SEASONS  # 初始均匀分布
        }

        # 旅行历史
        self.travel_history: List[Dict] = []

        # 避免的地点
        self.avoid_places: List[str] = []

        # 喜欢的城市
        self.favorite_cities: List[str] = []

        # 偏好更新时间戳（用于衰减计算）
        self.interest_timestamps: Dict[str, str] = {}  # {tag: iso_datetime}

        # 交互统计
        self.interaction_count: int = 0
        self.recommendation_accept_count: int = 0
        self.recommendation_reject_count: int = 0
        self.feedback_history: List[Dict] = []

    def to_dict(self) -> Dict:
        return {
            'user_id': self.user_id,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'interests': self.interests,
            'travel_style': self.travel_style,
            'travel_style_confidence': self.travel_style_confidence,
            'risk_preference': self.risk_preference,
            'risk_preference_confidence': self.risk_preference_confidence,
            'budget_sensitivity': self.budget_sensitivity,
            'budget_level': self.budget_level,
            'pace_preference': self.pace_preference,
            'social_tendency': self.social_tendency,
            'social_confidence': self.social_confidence,
            'seasonal_preference': self.seasonal_preference,
            'travel_history': self.travel_history,
            'avoid_places': self.avoid_places,
            'favorite_cities': self.favorite_cities,
            'interest_timestamps': self.interest_timestamps,
            'interaction_count': self.interaction_count,
            'recommendation_accept_count': self.recommendation_accept_count,
            'recommendation_reject_count': self.recommendation_reject_count,
            'feedback_history': self.feedback_history[-20:]  # 只保留最近20条
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'TravelPersona':
        persona = cls(data['user_id'])
        persona.created_at = data.get('created_at', persona.created_at)
        persona.updated_at = data.get('updated_at', persona.updated_at)
        persona.interests = data.get('interests', {})
        persona.travel_style = data.get('travel_style', 'balanced')
        persona.travel_style_confidence = data.get('travel_style_confidence', 0.3)
        persona.risk_preference = data.get('risk_preference', 'moderate')
        persona.risk_preference_confidence = data.get('risk_preference_confidence', 0.3)
        persona.budget_sensitivity = data.get('budget_sensitivity', {cat: 1.0 for cat in EXPENSE_CATEGORIES})
        persona.budget_level = data.get('budget_level', 'medium')
        persona.pace_preference = data.get('pace_preference', {'min_per_day': 2, 'max_per_day': 4})
        persona.social_tendency = data.get('social_tendency', 'small_group')
        persona.social_confidence = data.get('social_confidence', 0.3)
        persona.seasonal_preference = data.get('seasonal_preference', {s: 0.25 for s in SEASONS})
        persona.travel_history = data.get('travel_history', [])
        persona.avoid_places = data.get('avoid_places', [])
        persona.favorite_cities = data.get('favorite_cities', [])
        persona.interest_timestamps = data.get('interest_timestamps', {})
        persona.interaction_count = data.get('interaction_count', 0)
        persona.recommendation_accept_count = data.get('recommendation_accept_count', 0)
        persona.recommendation_reject_count = data.get('recommendation_reject_count', 0)
        persona.feedback_history = data.get('feedback_history', [])
        return persona

    def apply_decay(self):
        """应用指数衰减模型：30天未强化的兴趣权重衰减至50%"""
        now = datetime.now()
        for tag in list(self.interests.keys()):
            if tag in self.interest_timestamps:
                last_update = datetime.fromisoformat(self.interest_timestamps[tag])
                days_elapsed = (now - last_update).days
                if days_elapsed > 0:
                    # 指数衰减公式: w(t) = w0 * exp(-lambda * t)
                    decay_factor = math.exp(-DECAY_LAMBDA * days_elapsed)
                    old_weight = self.interests[tag]
                    self.interests[tag] = round(old_weight * decay_factor, 4)
                    # 如果权重过低，移除该兴趣
                    if self.interests[tag] < 0.05:
                        del self.interests[tag]
                        del self.interest_timestamps[tag]

    def get_persona_summary(self) -> str:
        """生成画像摘要文本，用于注入LLM prompt"""
        self.apply_decay()

        parts = []

        # 兴趣Top-5
        if self.interests:
            sorted_interests = sorted(self.interests.items(), key=lambda x: x[1], reverse=True)
            top5 = [f"{tag}({weight:.2f})" for tag, weight in sorted_interests[:5]]
            parts.append(f"兴趣偏好: {', '.join(top5)}")

        # 旅行风格
        style_names = {
            'intensive': '特种兵式（密集打卡）',
            'active': '活跃型（充实丰富）',
            'balanced': '均衡型（劳逸结合）',
            'relaxed': '悠闲型（轻松自在）',
            'slow_paced': '慢节奏度假（深度体验）'
        }
        parts.append(f"旅行风格: {style_names.get(self.travel_style, '均衡型')}")

        # 风险偏好
        risk_names = {
            'conservative': '谨慎保守（偏好安全、成熟路线）',
            'moderate': '适度平衡（可接受一定冒险）',
            'adventurous': '热爱冒险（喜欢小众、极限体验）'
        }
        parts.append(f"风险偏好: {risk_names.get(self.risk_preference, '适度平衡')}")

        # 预算
        budget_names = {'low': '经济实惠型', 'medium': '舒适型', 'high': '品质享受型'}
        parts.append(f"预算等级: {budget_names.get(self.budget_level, '舒适型')}")

        # 节奏
        parts.append(f"每日景点: {self.pace_preference['min_per_day']}-{self.pace_preference['max_per_day']}个")

        # 社交倾向
        social_names = {
            'solo': '独自出行',
            'couple': '双人出行',
            'small_group': '小团体（3-5人）',
            'large_group': '大团体（6人以上）',
            'family': '家庭出行（含老人/儿童）'
        }
        parts.append(f"社交倾向: {social_names.get(self.social_tendency, '小团体')}")

        return '\n'.join(parts)

    def get_top_interests(self, n: int = 5) -> List[Tuple[str, float]]:
        """获取Top-N兴趣"""
        self.apply_decay()
        sorted_interests = sorted(self.interests.items(), key=lambda x: x[1], reverse=True)
        return sorted_interests[:n]

    def get_interest_vector_for_filtering(self) -> Dict[str, float]:
        """获取用于推荐过滤的兴趣向量"""
        self.apply_decay()
        # 归一化到0-1
        if not self.interests:
            return {}
        max_weight = max(self.interests.values())
        if max_weight == 0:
            return {}
        return {k: v / max_weight for k, v in self.interests.items()}


class PersonaService:
    """旅行人格画像服务"""

    def __init__(self):
        self._personas: Dict[str, TravelPersona] = {}
        self._load()

    def _load(self):
        """从文件加载所有画像"""
        try:
            os.makedirs(PERSONA_DATA_DIR, exist_ok=True)
            if os.path.exists(PERSONA_FILE):
                with open(PERSONA_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                for user_id, persona_data in data.items():
                    self._personas[user_id] = TravelPersona.from_dict(persona_data)
        except Exception as e:
            print(f"[PersonaService] 加载画像失败: {e}")

    def _save(self):
        """保存所有画像到文件"""
        try:
            os.makedirs(PERSONA_DATA_DIR, exist_ok=True)
            data = {uid: p.to_dict() for uid, p in self._personas.items()}
            with open(PERSONA_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[PersonaService] 保存画像失败: {e}")

    def get_or_create_persona(self, user_id: str) -> TravelPersona:
        """获取或创建用户画像"""
        if user_id not in self._personas:
            self._personas[user_id] = TravelPersona(user_id)
            self._save()
        return self._personas[user_id]

    def get_persona(self, user_id: str) -> Optional[TravelPersona]:
        """获取用户画像（不创建）"""
        return self._personas.get(user_id)

    # ===== 三层偏好提取 =====

    def extract_explicit_preferences(self, user_id: str, message: str) -> Dict[str, Any]:
        """
        第一层：显式偏好提取（置信度0.9）
        用户在对话中明确表达的偏好
        """
        persona = self.get_or_create_persona(user_id)
        extracted = {}
        confidence = 0.9

        # 兴趣标签匹配
        tag_patterns = {
            'nature': ['自然', '山水', '风景', '户外', '大自然', '花草', '森林', '公园'],
            'beach': ['海边', '沙滩', '海浪', '海景', '岛屿', '海岛'],
            'mountain': ['爬山', '登山', '山景', '高山', '徒步', '山峰'],
            'history': ['历史', '古迹', '古代', '遗址', '文物', '传统'],
            'culture': ['文化', '人文', '民俗', '非遗', '艺术', '文学'],
            'museum': ['博物馆', '展览', '美术馆', '科技馆', '纪念馆'],
            'food': ['美食', '好吃', '吃货', '料理', '餐厅', '小吃', '饮食'],
            'street_food': ['街边小吃', '夜市', '大排档', '路边摊'],
            'fine_dining': ['米其林', '高级餐厅', '精致料理', '私房菜', 'Fine Dining'],
            'local_cuisine': ['当地特色', '地方菜', '本地人推荐', '家乡味'],
            'photography': ['拍照', '摄影', '出片', '打卡', '相机', '美景'],
            'shopping': ['购物', '逛街', '买', '商场', '折扣', '免税'],
            'adventure': ['冒险', '刺激', '极限', '蹦极', '跳伞', '冲浪', '潜水'],
            'relax': ['放松', '休闲', '度假', '慢', '惬意', '安静', '悠闲'],
            'spa': ['SPA', '按摩', '水疗', '温泉', '泡汤'],
            'nightlife': ['夜生活', '酒吧', '夜店', 'livehouse', '演出'],
            'family_friendly': ['亲子', '带孩子', '小朋友', '儿童', '家庭'],
            'theme_park': ['主题公园', '游乐园', '乐园', '迪士尼', '环球'],
            'sports': ['运动', '滑雪', '骑行', '跑步', '健身', '游泳'],
            'architecture': ['建筑', '设计', '特色建筑', '老建筑', '古建筑'],
            'religion': ['寺庙', '教堂', '宗教', '朝圣', '祈福'],
            'art': ['画廊', '艺术展', '戏剧', '音乐剧', '歌剧', '演出'],
        }

        for tag, keywords in tag_patterns.items():
            for kw in keywords:
                if kw in message:
                    if tag not in persona.interests:
                        persona.interests[tag] = 0.0
                    # 显式偏好：大幅提升权重
                    persona.interests[tag] = min(1.0, persona.interests[tag] + 0.3)
                    persona.interest_timestamps[tag] = datetime.now().isoformat()
                    extracted[tag] = {
                        'source': 'explicit',
                        'confidence': confidence,
                        'keyword': kw
                    }
                    break

        # 旅行风格识别
        style_keywords = {
            'intensive': ['特种兵', '一天', '打卡', '全逛完', '赶时间', '紧凑'],
            'active': ['多玩', '充实', '丰富', '多去'],
            'balanced': ['适中', '不赶', '合理安排'],
            'relaxed': ['悠闲', '轻松', '慢一点', '不赶时间', '惬意'],
            'slow_paced': ['度假', '深度', '慢游', '泡酒店', '发呆', '躺平']
        }
        for style, keywords in style_keywords.items():
            for kw in keywords:
                if kw in message:
                    persona.travel_style = style
                    persona.travel_style_confidence = min(1.0, persona.travel_style_confidence + 0.3)
                    extracted['travel_style'] = {'source': 'explicit', 'value': style}
                    break

        # 风险偏好识别
        risk_keywords = {
            'conservative': ['安全', '保险', '成熟', '不要冒险', '稳妥'],
            'moderate': ['可以试试', '适中'],
            'adventurous': ['冒险', '刺激', '极限', '挑战', '小众', '无人区', '探险']
        }
        for risk, keywords in risk_keywords.items():
            for kw in keywords:
                if kw in message:
                    persona.risk_preference = risk
                    persona.risk_preference_confidence = min(1.0, persona.risk_preference_confidence + 0.3)
                    extracted['risk_preference'] = {'source': 'explicit', 'value': risk}
                    break

        # 预算识别
        budget_keywords = {
            'low': ['省钱', '便宜', '穷游', '经济', '实惠', '性价比'],
            'medium': ['舒适', '中等', '差不多就行'],
            'high': ['豪华', '高端', '奢华', '品质', '不计较', '贵']
        }
        for budget, keywords in budget_keywords.items():
            for kw in keywords:
                if kw in message:
                    persona.budget_level = budget
                    extracted['budget'] = {'source': 'explicit', 'value': budget}
                    break

        # 社交倾向识别
        social_keywords = {
            'solo': ['独自', '一个人', '单身', '一个人去'],
            'couple': ['情侣', '两人', '蜜月', '二人世界'],
            'small_group': ['几个朋友', '三五好友', '闺蜜', '兄弟'],
            'large_group': ['一群人', '团建', '班级', '公司'],
            'family': ['家人', '带孩子', '父母', '一家', '亲子', '老小']
        }
        for social, keywords in social_keywords.items():
            for kw in keywords:
                if kw in message:
                    persona.social_tendency = social
                    persona.social_confidence = min(1.0, persona.social_confidence + 0.3)
                    extracted['social_tendency'] = {'source': 'explicit', 'value': social}
                    break

        # 城市偏好
        from services.city_service import get_all_cities
        try:
            all_cities = get_all_cities()
            city_names = [c.get('name', '') for c in all_cities] if all_cities else []
        except Exception:
            city_names = ["北京", "上海", "广州", "深圳", "杭州", "成都", "重庆", "西安",
                          "南京", "武汉", "苏州", "青岛", "厦门", "昆明", "丽江"]

        for city in city_names:
            if city in message:
                if '想去' in message or '喜欢' in message or '推荐' in message:
                    if city not in persona.favorite_cities:
                        persona.favorite_cities.append(city)
                    extracted['favorite_city'] = {'source': 'explicit', 'value': city}
                if '不去' in message or '不想' in message or '避免' in message:
                    if city not in persona.avoid_places:
                        persona.avoid_places.append(city)
                    extracted['avoid_city'] = {'source': 'explicit', 'value': city}

        if extracted:
            persona.interaction_count += 1
            persona.updated_at = datetime.now().isoformat()
            self._save()

        return extracted

    def extract_implicit_preferences(self, user_id: str, behavior_data: Dict) -> Dict[str, Any]:
        """
        第二层：隐式偏好推理（置信度0.6）
        从用户行为推断偏好
        behavior_data 包含: {'action': 'query_city'|'check_weather'|'generate_itinerary',
                            'city': str, 'preferences': list, 'duration': int, ...}
        """
        persona = self.get_or_create_persona(user_id)
        extracted = {}
        confidence = 0.6

        action = behavior_data.get('action', '')

        # 从查询行为推断兴趣
        if action in ('query_city', 'check_weather'):
            city = behavior_data.get('city', '')
            # 根据城市推断可能的兴趣
            city_features_map = {
                '北京': ['history', 'culture', 'architecture'],
                '上海': ['shopping', 'nightlife', 'architecture'],
                '广州': ['food', 'shopping', 'culture'],
                '深圳': ['theme_park', 'shopping', 'adventure'],
                '杭州': ['nature', 'photography', 'culture'],
                '成都': ['food', 'relax', 'culture'],
                '重庆': ['food', 'mountain', 'nightlife'],
                '西安': ['history', 'culture', 'food'],
                '南京': ['history', 'culture', 'nature'],
                '苏州': ['culture', 'architecture', 'nature'],
                '青岛': ['beach', 'food', 'relax'],
                '厦门': ['beach', 'relax', 'food'],
                '昆明': ['nature', 'relax', 'photography'],
                '丽江': ['nature', 'relax', 'culture'],
            }
            features = city_features_map.get(city, [])
            for tag in features:
                if tag not in persona.interests:
                    persona.interests[tag] = 0.0
                persona.interests[tag] = min(1.0, persona.interests[tag] + 0.1)
                persona.interest_timestamps[tag] = datetime.now().isoformat()
                extracted[tag] = {'source': 'implicit', 'confidence': confidence}

        # 从行程生成行为推断
        if action == 'generate_itinerary':
            prefs = behavior_data.get('preferences', [])
            for pref in prefs:
                if pref in INTEREST_TAGS:
                    if pref not in persona.interests:
                        persona.interests[pref] = 0.0
                    persona.interests[pref] = min(1.0, persona.interests[pref] + 0.15)
                    persona.interest_timestamps[pref] = datetime.now().isoformat()
                    extracted[pref] = {'source': 'implicit', 'confidence': confidence}

            # 节奏偏好推断
            days = behavior_data.get('days', 3)
            attractions = behavior_data.get('attraction_count', days * 3)
            per_day = attractions / max(days, 1)
            if per_day <= 2:
                persona.pace_preference = {'min_per_day': 1, 'max_per_day': 2}
            elif per_day <= 4:
                persona.pace_preference = {'min_per_day': 2, 'max_per_day': 4}
            else:
                persona.pace_preference = {'min_per_day': 4, 'max_per_day': 6}

            # 季节偏好更新
            month = datetime.now().month
            if 3 <= month <= 5:
                season = 'spring'
            elif 6 <= month <= 8:
                season = 'summer'
            elif 9 <= month <= 11:
                season = 'autumn'
            else:
                season = 'winter'
            total = sum(persona.seasonal_preference.values())
            persona.seasonal_preference[season] = persona.seasonal_preference.get(season, 0) + 0.1

        if extracted:
            persona.interaction_count += 1
            persona.updated_at = datetime.now().isoformat()
            self._save()

        return extracted

    def apply_feedback(self, user_id: str, recommendation_type: str,
                       recommendation_content: str, accepted: bool) -> Dict:
        """
        第三层：反馈校准
        accepted=True → +0.1 (采纳)
        accepted=False (ignored) → -0.02 (忽略)
        accepted=False (explicitly rejected) → -0.15 (拒绝)

        recommendation_type: 'city', 'itinerary', 'activity', 'food', 'alert'
        """
        persona = self.get_or_create_persona(user_id)
        feedback = {
            'type': recommendation_type,
            'content': recommendation_content,
            'accepted': accepted,
            'timestamp': datetime.now().isoformat()
        }
        persona.feedback_history.append(feedback)

        if accepted:
            persona.recommendation_accept_count += 1
            # 提升相关兴趣权重
            self._boost_interests_for_recommendation(persona, recommendation_type, recommendation_content, 0.1)
        else:
            persona.recommendation_reject_count += 1
            # 轻微降低相关兴趣权重（忽略）
            self._boost_interests_for_recommendation(persona, recommendation_type, recommendation_content, -0.02)

        persona.updated_at = datetime.now().isoformat()
        self._save()

        return {
            'accept_rate': round(
                persona.recommendation_accept_count / max(persona.interaction_count, 1), 3
            ),
            'total_interactions': persona.interaction_count
        }

    def _boost_interests_for_recommendation(self, persona: TravelPersona,
                                             rec_type: str, content: str, delta: float):
        """根据推荐内容调整兴趣权重"""
        # 从推荐内容中提取可能的兴趣标签
        for tag in INTEREST_TAGS:
            tag_patterns_map = {
                'nature': ['自然', '山水', '风景', '公园', '户外'],
                'beach': ['海边', '沙滩', '海', '岛屿'],
                'mountain': ['山', '登山', '徒步', '峰'],
                'history': ['历史', '古迹', '遗址', '古代'],
                'culture': ['文化', '人文', '民俗', '传统'],
                'museum': ['博物馆', '展览', '美术馆'],
                'food': ['美食', '小吃', '餐厅', '料理', '吃'],
                'shopping': ['购物', '逛街', '商场', '买'],
                'photography': ['拍照', '摄影', '出片', '打卡'],
                'relax': ['放松', '休闲', '度假', '慢', '安静'],
                'adventure': ['冒险', '刺激', '极限'],
                'family_friendly': ['亲子', '儿童', '家庭', '小孩'],
                'nightlife': ['夜生活', '酒吧', '夜景', '演出'],
                'architecture': ['建筑', '老房子', '设计'],
                'art': ['艺术', '画廊', '戏剧', '音乐'],
            }
            patterns = tag_patterns_map.get(tag, [tag])
            for pattern in patterns:
                if pattern in content:
                    if tag not in persona.interests:
                        persona.interests[tag] = 0.0
                    persona.interests[tag] = max(0.0, min(1.0, persona.interests[tag] + delta))
                    persona.interest_timestamps[tag] = datetime.now().isoformat()
                    break

    # ===== 画像驱动推荐方法 =====

    def filter_and_rank_cities(self, user_id: str, candidate_cities: List[Dict]) -> List[Dict]:
        """基于用户画像过滤和排序候选城市"""
        persona = self.get_or_create_persona(user_id)
        persona.apply_decay()

        for city in candidate_cities:
            city_name = city.get('city', city.get('name', ''))
            score = 50  # 基础分

            # 1. 排除用户避免的城市
            if city_name in persona.avoid_places:
                city['score'] = -1
                continue

            # 2. 兴趣匹配
            city_features = city.get('features', [])
            interest_vec = persona.get_interest_vector_for_filtering()
            for feature in city_features:
                if feature in interest_vec:
                    score += int(interest_vec[feature] * 25)

            # 3. 喜欢的城市加分
            if city_name in persona.favorite_cities:
                score += 20

            # 4. 季节匹配
            month = datetime.now().month
            if 3 <= month <= 5:
                season = 'spring'
            elif 6 <= month <= 8:
                season = 'summer'
            elif 9 <= month <= 11:
                season = 'autumn'
            else:
                season = 'winter'

            season_weights = persona.seasonal_preference
            if season in season_weights:
                score += int(season_weights[season] * 15)

            # 5. 预算匹配
            city_cost = city.get('cost_level', 'medium')
            if city_cost == persona.budget_level:
                score += 10

            # 6. 风险偏好调整
            city_risk = city.get('risk_level', 'low')
            if persona.risk_preference == 'adventurous' and city_risk == 'high':
                score += 10
            elif persona.risk_preference == 'conservative' and city_risk == 'low':
                score += 10

            city['score'] = score

        # 过滤掉score=-1的并排序
        valid_cities = [c for c in candidate_cities if c.get('score', 0) >= 0]
        valid_cities.sort(key=lambda x: x.get('score', 0), reverse=True)

        return valid_cities

    def personalize_alert_threshold(self, user_id: str, rule_id: str, default_threshold: float) -> float:
        """根据用户风险偏好调整告警阈值"""
        persona = self.get_or_create_persona(user_id)

        if persona.risk_preference == 'adventurous':
            # 冒险型用户：阈值提高20%，减少不必要的提醒
            return default_threshold * 1.2
        elif persona.risk_preference == 'conservative':
            # 保守型用户：阈值降低15%，更早提醒
            return default_threshold * 0.85
        else:
            return default_threshold

    def generate_persona_context_for_prompt(self, user_id: str) -> str:
        """生成用于注入LLM prompt的画像上下文"""
        persona = self.get_or_create_persona(user_id)
        summary = persona.get_persona_summary()

        # 添加避免的地点
        avoid_str = ''
        if persona.avoid_places:
            avoid_str = f"\n避免地点: {', '.join(persona.avoid_places)}"

        # 添加喜欢的城市
        fav_str = ''
        if persona.favorite_cities:
            fav_str = f"\n偏好城市: {', '.join(persona.favorite_cities)}"

        # 添加历史旅行
        hist_str = ''
        if persona.travel_history:
            recent = persona.travel_history[-3:]
            hist_str = '\n最近旅行: ' + ', '.join(
                [f"{h.get('city', '?')}({h.get('date', '?')})" for h in recent]
            )

        return f"""用户画像：
{summary}{avoid_str}{fav_str}{hist_str}

请根据以上用户画像提供个性化建议，推荐应匹配用户的兴趣偏好、旅行风格和预算等级。"""


# 全局单例
persona_service = PersonaService()
