"""
个性化旅行推荐系统
基于用户长期记忆和偏好，智能推荐旅游目的地和活动
"""
from datetime import datetime, timedelta
from services.memory_service import load_memory
from services.weather_service import get_weather
from services.city_service import get_all_cities

def get_personalized_recommendations(user_id=None, context=None):
    """
    获取个性化旅行推荐
    
    Args:
        user_id: 用户ID
        context: 当前上下文（可选）
    
    Returns:
        推荐结果字典
    """
    # 加载用户记忆
    memory = {}
    if user_id:
        memory = load_memory(user_id)
    
    # 提取用户偏好
    preferences = extract_preferences_from_memory(memory)
    
    # 获取当前季节
    season = get_current_season()
    
    # 根据偏好和季节生成推荐
    recommendations = generate_recommendations(preferences, season, memory)
    
    return recommendations

def extract_preferences_from_memory(memory):
    """从用户记忆中提取偏好"""
    preferences = {
        'interests': [],
        'budget': 'medium',
        'travel_style': '',
        'avoid_places': [],
        'favorite_cities': [],
        'travel_history': []
    }
    
    if memory:
        # 从记忆中提取兴趣爱好
        if 'interests' in memory:
            preferences['interests'] = memory['interests']
        
        # 提取预算信息
        if 'budget' in memory:
            preferences['budget'] = memory['budget']
        
        # 提取旅行风格
        if 'travel_style' in memory:
            preferences['travel_style'] = memory['travel_style']
        
        # 提取避免的地点
        if 'avoid_places' in memory:
            preferences['avoid_places'] = memory['avoid_places']
        
        # 提取喜欢的城市
        if 'favorite_cities' in memory:
            preferences['favorite_cities'] = memory['favorite_cities']
        
        # 提取旅行历史
        if 'travel_history' in memory:
            preferences['travel_history'] = memory['travel_history']
    
    return preferences

def get_current_season():
    """获取当前季节"""
    month = datetime.now().month
    if 3 <= month <= 5:
        return 'spring'
    elif 6 <= month <= 8:
        return 'summer'
    elif 9 <= month <= 11:
        return 'autumn'
    else:
        return 'winter'

def generate_recommendations(preferences, season, memory):
    """生成推荐"""
    recommendations = {
        'season': season,
        'season_name': get_season_name(season),
        'top_destinations': [],
        'activity_recommendations': [],
        'food_recommendations': [],
        'travel_tips': []
    }
    
    # 获取季节推荐城市
    season_cities = get_season_recommendations(season)
    
    # 根据用户偏好过滤
    filtered_cities = filter_cities_by_preferences(season_cities, preferences)
    
    # 获取天气信息并排序
    cities_with_weather = []
    for city in filtered_cities:
        try:
            weather = get_weather(city)
            temp = weather.get('temperature', 20)
            condition = weather.get('condition', '')
        except Exception:
            temp = 20
            condition = 'unknown'
        
        cities_with_weather.append({
            'city': city,
            'temperature': temp,
            'condition': condition,
            'score': calculate_city_score(city, preferences, season)
        })
    
    # 按评分排序
    cities_with_weather.sort(key=lambda x: x['score'], reverse=True)
    
    # 选择前5个推荐
    recommendations['top_destinations'] = cities_with_weather[:5]
    
    # 活动推荐
    recommendations['activity_recommendations'] = get_activity_recommendations(preferences, season)
    
    # 美食推荐
    recommendations['food_recommendations'] = get_food_recommendations(preferences)
    
    # 旅行小贴士
    recommendations['travel_tips'] = generate_travel_tips(preferences, season)
    
    return recommendations

def get_season_name(season):
    """获取季节中文名"""
    season_map = {
        'spring': '春季',
        'summer': '夏季',
        'autumn': '秋季',
        'winter': '冬季'
    }
    return season_map.get(season, '未知')

def get_season_recommendations(season):
    """获取季节推荐城市"""
    season_recommendations = {
        'spring': ['杭州', '苏州', '武汉', '昆明', '成都', '南京', '扬州', '无锡'],
        'summer': ['青岛', '大连', '威海', '厦门', '丽江', '贵阳', '承德', '西宁'],
        'autumn': ['北京', '西安', '成都', '南京', '长沙', '重庆', '洛阳', '开封'],
        'winter': ['三亚', '海口', '广州', '深圳', '厦门', '昆明', '珠海', '西双版纳']
    }
    return season_recommendations.get(season, [])

def filter_cities_by_preferences(cities, preferences):
    """根据用户偏好过滤城市"""
    filtered = []
    
    for city in cities:
        # 排除用户明确避免的地点
        if city in preferences['avoid_places']:
            continue
        
        # 如果有旅行历史，优先推荐未去过的城市
        if preferences['travel_history'] and city in preferences['travel_history']:
            continue
        
        filtered.append(city)
    
    return filtered

def calculate_city_score(city, preferences, season):
    """计算城市推荐分数"""
    score = 50  # 基础分
    
    # 季节匹配加分
    season_bonus = {
        'spring': {'杭州': 20, '苏州': 18, '武汉': 15, '昆明': 12},
        'summer': {'青岛': 20, '大连': 18, '威海': 15, '丽江': 12},
        'autumn': {'北京': 20, '西安': 18, '成都': 15, '南京': 12},
        'winter': {'三亚': 20, '海口': 18, '广州': 15, '昆明': 12}
    }
    
    if city in season_bonus.get(season, {}):
        score += season_bonus[season][city]
    
    # 用户兴趣匹配加分
    interests = preferences.get('interests', [])
    city_features = get_city_features(city)
    
    for interest in interests:
        if interest in city_features:
            score += 10
    
    # 预算匹配加分
    budget = preferences.get('budget', 'medium')
    city_cost = get_city_cost_level(city)
    if city_cost == budget:
        score += 10
    elif (budget == 'low' and city_cost == 'medium') or (budget == 'medium' and city_cost == 'high'):
        score += 5
    
    # 喜欢的城市额外加分
    if city in preferences.get('favorite_cities', []):
        score += 15
    
    return score

def get_city_features(city):
    """获取城市特色"""
    features = {
        '北京': ['history', 'culture', 'sightseeing', 'shopping'],
        '上海': ['modern', 'shopping', 'sightseeing', 'food'],
        '广州': ['food', 'shopping', 'culture', 'nature'],
        '深圳': ['modern', 'theme_park', 'nature', 'shopping'],
        '杭州': ['nature', 'sightseeing', 'food', 'culture'],
        '成都': ['food', 'culture', 'nature', 'relax'],
        '重庆': ['nature', 'food', 'sightseeing', 'culture'],
        '西安': ['history', 'culture', 'sightseeing', 'food'],
        '南京': ['history', 'culture', 'nature', 'food'],
        '武汉': ['culture', 'food', 'nature', 'sightseeing'],
        '苏州': ['culture', 'nature', 'sightseeing', 'food'],
        '青岛': ['nature', 'food', 'beach', 'relax'],
        '厦门': ['beach', 'nature', 'food', 'relax'],
        '昆明': ['nature', 'relax', 'sightseeing', 'culture'],
        '丽江': ['nature', 'culture', 'relax', 'sightseeing'],
        '三亚': ['beach', 'nature', 'relax', 'food'],
        '大连': ['beach', 'nature', 'sightseeing', 'food'],
        '威海': ['beach', 'nature', 'relax', 'food'],
        '贵阳': ['nature', 'relax', 'sightseeing', 'food'],
        '承德': ['nature', 'history', 'relax', 'sightseeing'],
        '西宁': ['nature', 'culture', 'relax', 'sightseeing'],
        '长沙': ['food', 'culture', 'sightseeing', 'shopping'],
        '洛阳': ['history', 'culture', 'sightseeing', 'nature'],
        '开封': ['history', 'culture', 'food', 'sightseeing'],
        '海口': ['beach', 'nature', 'relax', 'food'],
        '珠海': ['beach', 'nature', 'relax', 'sightseeing'],
        '西双版纳': ['nature', 'culture', 'relax', 'food'],
        '扬州': ['culture', 'nature', 'food', 'sightseeing'],
        '无锡': ['nature', 'culture', 'sightseeing', 'food']
    }
    return features.get(city, [])

def get_city_cost_level(city):
    """获取城市消费等级"""
    cost_levels = {
        'high': ['北京', '上海', '深圳'],
        'medium': ['广州', '杭州', '成都', '重庆', '西安', '南京', '武汉', '苏州', '青岛', '厦门', '三亚', '大连'],
        'low': ['昆明', '丽江', '贵阳', '承德', '西宁', '长沙', '洛阳', '开封', '海口', '珠海', '西双版纳', '扬州', '无锡']
    }
    
    for level, cities in cost_levels.items():
        if city in cities:
            return level
    
    return 'medium'

def get_activity_recommendations(preferences, season):
    """获取活动推荐"""
    interests = preferences.get('interests', [])
    activities = []
    
    if 'nature' in interests:
        activities.append({
            'activity': '自然风光',
            'description': '推荐游览当地著名自然景观',
            'season_tip': get_nature_season_tip(season)
        })
    
    if 'culture' in interests or 'history' in interests:
        activities.append({
            'activity': '文化体验',
            'description': '探访历史古迹，感受文化底蕴',
            'season_tip': '历史景点四季皆宜，建议避开节假日高峰'
        })
    
    if 'food' in interests:
        activities.append({
            'activity': '美食探索',
            'description': '品尝当地特色美食',
            'season_tip': '夏季推荐清凉小吃，冬季推荐暖心美食'
        })
    
    if 'shopping' in interests:
        activities.append({
            'activity': '购物逛街',
            'description': '逛当地特色商业街',
            'season_tip': '冬季商场有折扣活动，夏季有夜市'
        })
    
    if 'relax' in interests:
        activities.append({
            'activity': '休闲放松',
            'description': '慢节奏享受假期',
            'season_tip': '春季和秋季是放松度假的最佳时节'
        })
    
    # 如果没有明确兴趣，提供通用推荐
    if not activities:
        activities = [
            {
                'activity': '经典观光',
                'description': '游览城市标志性景点',
                'season_tip': get_general_season_tip(season)
            }
        ]
    
    return activities

def get_nature_season_tip(season):
    """获取自然风光季节提示"""
    tips = {
        'spring': '春季万物复苏，赏花踏青好时节',
        'summer': '夏季绿意盎然，避暑纳凉正当时',
        'autumn': '秋季层林尽染，红叶美景不胜收',
        'winter': '冬季银装素裹，雪山冰景别有风味'
    }
    return tips.get(season, '')

def get_general_season_tip(season):
    """获取通用季节提示"""
    tips = {
        'spring': '春季气候宜人，适合各类户外活动',
        'summer': '夏季注意防暑降温，早晚出行更舒适',
        'autumn': '秋季天高气爽，是旅行的黄金季节',
        'winter': '冬季注意保暖，温泉滑雪是不错选择'
    }
    return tips.get(season, '')

def get_food_recommendations(preferences):
    """获取美食推荐"""
    interests = preferences.get('interests', [])
    budget = preferences.get('budget', 'medium')
    
    recommendations = []
    
    if 'food' in interests:
        recommendations.append({
            'type': 'local_specialty',
            'description': '品尝当地特色美食',
            'budget_tip': get_food_budget_tip(budget)
        })
    else:
        recommendations.append({
            'type': 'recommended',
            'description': '推荐当地人气餐厅',
            'budget_tip': get_food_budget_tip(budget)
        })
    
    return recommendations

def get_food_budget_tip(budget):
    """获取美食预算提示"""
    tips = {
        'low': '推荐小吃摊和本地小馆，经济实惠',
        'medium': '可以尝试连锁餐厅和特色餐馆',
        'high': '推荐高端餐厅和特色私房菜'
    }
    return tips.get(budget, '')

def generate_travel_tips(preferences, season):
    """生成旅行小贴士"""
    tips = []
    
    # 预算提示
    budget = preferences.get('budget', 'medium')
    if budget == 'low':
        tips.append('预算有限的话，建议选择公共交通和经济型住宿')
    elif budget == 'high':
        tips.append('高端出行可以考虑专车服务和精品酒店')
    
    # 季节提示
    season_tips = {
        'spring': '春季天气多变，记得带雨具',
        'summer': '夏季炎热，注意防晒和补水',
        'autumn': '秋季温差大，建议多带一件外套',
        'winter': '冬季寒冷，注意保暖措施'
    }
    tips.append(season_tips.get(season, ''))
    
    # 兴趣相关提示
    interests = preferences.get('interests', [])
    if 'nature' in interests:
        tips.append('喜欢自然风光的话，建议早起避开人流高峰')
    if 'history' in interests or 'culture' in interests:
        tips.append('参观历史景点建议提前预约，部分景点限流')
    
    return tips
