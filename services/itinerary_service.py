"""
智能行程规划引擎 - 核心功能
根据用户输入的目的地、时间、预算和偏好，自动生成完整的旅行行程计划
"""
from datetime import datetime, timedelta
from services.weather_service import get_weather_forecast
from services.city_service import get_all_cities, search_cities

def generate_itinerary(city, days=3, preferences=None, budget='medium'):
    """
    生成旅行行程计划
    
    Args:
        city: 目的地城市
        days: 旅行天数
        preferences: 用户偏好列表 ['sightseeing', 'food', 'shopping', 'nature', 'culture']
        budget: 预算等级 'low', 'medium', 'high'
    
    Returns:
        行程计划字典
    """
    if preferences is None:
        preferences = ['sightseeing', 'food']
    
    itinerary = {
        'city': city,
        'days': days,
        'budget': budget,
        'preferences': preferences,
        'created_at': datetime.now().isoformat(),
        'days_plan': []
    }
    
    # 获取天气预报
    try:
        forecast = get_weather_forecast(city)
        daily_weather = forecast.get('forecast', [])[:days]
    except Exception:
        daily_weather = []
    
    # 景点推荐
    attractions = get_city_attractions(city, preferences)
    
    # 美食推荐
    foods = get_city_foods(city)
    
    # 按天规划行程
    day_plan = {}
    attraction_index = 0
    
    for day in range(1, days + 1):
        weather = daily_weather[day-1] if day-1 < len(daily_weather) else None
        day_info = {
            'day': day,
            'date': (datetime.now() + timedelta(days=day-1)).strftime('%Y-%m-%d'),
            'weather': weather,
            'morning': None,
            'afternoon': None,
            'evening': None
        }
        
        # 根据天气安排活动
        if weather and 'rain' in weather.get('condition', '').lower():
            # 雨天：室内活动
            day_info['morning'] = {
                'activity': '室内景点',
                'place': get_indoor_attraction(city, attractions, attraction_index),
                'duration': '2-3小时',
                'budget': get_budget_estimate(budget)
            }
            attraction_index += 1
            
            day_info['afternoon'] = {
                'activity': '特色美食',
                'place': foods[min(day, len(foods)-1)] if foods else '当地特色餐厅',
                'duration': '2小时',
                'budget': get_budget_estimate(budget, 'food')
            }
            
            day_info['evening'] = {
                'activity': '购物/夜景',
                'place': get_shopping_area(city),
                'duration': '2-3小时',
                'budget': get_budget_estimate(budget, 'shopping')
            }
        else:
            # 晴天：户外活动
            if attraction_index < len(attractions):
                day_info['morning'] = {
                    'activity': '景点游览',
                    'place': attractions[attraction_index],
                    'duration': '3-4小时',
                    'budget': get_budget_estimate(budget)
                }
                attraction_index += 1
            
            if attraction_index < len(attractions):
                day_info['afternoon'] = {
                    'activity': '景点游览',
                    'place': attractions[attraction_index],
                    'duration': '3-4小时',
                    'budget': get_budget_estimate(budget)
                }
                attraction_index += 1
            
            day_info['evening'] = {
                'activity': '美食体验',
                'place': foods[min(day, len(foods)-1)] if foods else '当地特色餐厅',
                'duration': '2小时',
                'budget': get_budget_estimate(budget, 'food')
            }
        
        itinerary['days_plan'].append(day_info)
    
    # 添加行程建议
    itinerary['tips'] = generate_travel_tips(city, budget)
    
    return itinerary

def get_city_attractions(city, preferences):
    """获取城市景点推荐"""
    attractions_db = {
        '北京': ['故宫博物院', '天安门广场', '八达岭长城', '颐和园', '天坛公园', '鸟巢', '南锣鼓巷'],
        '上海': ['外滩', '东方明珠', '豫园', '南京路', '迪士尼乐园', '田子坊', '上海博物馆'],
        '广州': ['广州塔', '长隆欢乐世界', '陈家祠', '沙面岛', '白云山', '北京路步行街'],
        '深圳': ['世界之窗', '欢乐谷', '东部华侨城', '莲花山公园', '大鹏古城', '深圳湾公园'],
        '杭州': ['西湖', '灵隐寺', '千岛湖', '西溪湿地', '雷峰塔', '宋城'],
        '成都': ['宽窄巷子', '锦里', '武侯祠', '大熊猫基地', '都江堰', '青城山'],
        '重庆': ['洪崖洞', '解放碑', '长江索道', '磁器口古镇', '武隆天生三桥'],
        '西安': ['兵马俑', '大雁塔', '城墙', '回民街', '华山', '陕西历史博物馆'],
        '南京': ['中山陵', '夫子庙', '明孝陵', '总统府', '玄武湖', '老门东'],
        '武汉': ['黄鹤楼', '东湖', '长江大桥', '户部巷', '湖北省博物馆', '昙华林'],
        '苏州': ['拙政园', '留园', '虎丘', '平江路', '周庄', '寒山寺'],
        '青岛': ['栈桥', '八大关', '崂山', '五四广场', '啤酒博物馆', '石老人浴场'],
        '厦门': ['鼓浪屿', '环岛路', '厦门大学', '南普陀寺', '曾厝垵', '沙坡尾'],
        '昆明': ['滇池', '翠湖公园', '石林', '云南民族村', '西山龙门'],
        '丽江': ['丽江古城', '玉龙雪山', '束河古镇', '泸沽湖', '虎跳峡']
    }
    
    # 根据偏好筛选
    result = attractions_db.get(city, [])
    return result[:6]

def get_city_foods(city):
    """获取城市美食推荐"""
    foods_db = {
        '北京': ['全聚德烤鸭', '东来顺涮肉', '北京炸酱面', '庆丰包子', '护国寺小吃'],
        '上海': ['南翔小笼', '生煎包', '本帮菜', '蟹粉豆腐', '上海冷面'],
        '广州': ['早茶点心', '烧腊', '肠粉', '白切鸡', '艇仔粥'],
        '深圳': ['粤菜', '潮汕牛肉火锅', '客家菜', '海鲜', '椰子鸡'],
        '杭州': ['西湖醋鱼', '龙井虾仁', '叫化鸡', '片儿川', '葱包桧'],
        '成都': ['火锅', '串串香', '麻婆豆腐', '夫妻肺片', '担担面'],
        '重庆': ['火锅', '小面', '酸辣粉', '毛血旺', '烤鱼'],
        '西安': ['肉夹馍', '羊肉泡馍', '凉皮', 'biangbiang面', '甑糕'],
        '南京': ['盐水鸭', '鸭血粉丝汤', '牛肉锅贴', '皮肚面', '桂花糖芋苗'],
        '武汉': ['热干面', '周黑鸭', '武昌鱼', '豆皮', '面窝'],
        '苏州': ['松鼠桂鱼', '响油鳝糊', '生煎', '藏书羊肉', '奥灶面'],
        '青岛': ['海鲜', '啤酒', '辣炒蛤蜊', '海菜凉粉', '烤鱿鱼'],
        '厦门': ['沙茶面', '土笋冻', '海蛎煎', '花生汤', '鱼丸'],
        '昆明': ['过桥米线', '汽锅鸡', '宣威火腿', '饵块', '酸角汁'],
        '丽江': ['腊排骨火锅', '三文鱼', '鸡豆凉粉', '纳西烤肉', '粑粑']
    }
    return foods_db.get(city, [])

def get_indoor_attraction(city, attractions, index):
    """获取室内景点"""
    indoor_attractions = {
        '北京': ['故宫博物院', '国家博物馆', '北京天文馆'],
        '上海': ['上海博物馆', '科技馆', '美术馆'],
        '广州': ['广东省博物馆', '广州图书馆', '陈家祠'],
        '成都': ['四川博物院', '武侯祠', '杜甫草堂'],
        '西安': ['陕西历史博物馆', '兵马俑博物馆', '碑林博物馆']
    }
    return indoor_attractions.get(city, attractions)[min(index, len(attractions)-1)] if attractions else '当地博物馆'

def get_shopping_area(city):
    """获取购物区域"""
    shopping_areas = {
        '北京': '王府井/西单',
        '上海': '南京路/淮海路',
        '广州': '天河城/北京路',
        '深圳': '东门/华强北',
        '杭州': '湖滨银泰/武林广场',
        '成都': '春熙路/太古里',
        '重庆': '解放碑/观音桥',
        '西安': '回民街/赛格',
        '南京': '新街口',
        '武汉': '楚河汉街/江汉路',
        '苏州': '观前街/平江路',
        '青岛': '中山路/万象城',
        '厦门': '中山路/SM城市广场',
        '昆明': '南屏街/正义路',
        '丽江': '丽江古城商业街'
    }
    return shopping_areas.get(city, '市中心商业街')

def get_budget_estimate(budget_type, category='activity'):
    """获取预算估算"""
    budget_map = {
        'low': {'activity': '¥50-100', 'food': '¥30-60', 'shopping': '¥100-300'},
        'medium': {'activity': '¥100-200', 'food': '¥60-150', 'shopping': '¥300-800'},
        'high': {'activity': '¥200-500', 'food': '¥150-300', 'shopping': '¥800+'}
    }
    return budget_map.get(budget_type, budget_map['medium']).get(category, '¥100-200')

def generate_travel_tips(city, budget):
    """生成旅行小贴士"""
    tips = []
    
    # 交通提示
    tips.append(f"{city}公共交通便利，建议办理交通卡或使用打车软件")
    
    # 预算提示
    if budget == 'low':
        tips.append("经济型出行建议：选择地铁公交，品尝街头小吃")
    elif budget == 'high':
        tips.append("高端出行建议：预约特色餐厅，安排专车服务")
    
    # 天气提示
    tips.append("出行前请关注天气预报，备好合适衣物")
    
    # 特色提示
    city_tips = {
        '北京': '故宫建议提前网上预约门票',
        '上海': '外滩夜景非常值得一看',
        '广州': '早茶建议早点去，热门餐厅需要排队',
        '成都': '火锅建议微辣起步，量力而行',
        '西安': '兵马俑建议请讲解员，了解历史背景',
        '杭州': '西湖周边景点众多，可以租自行车游览',
        '重庆': '注意地形，穿舒适的鞋子',
        '丽江': '古城内石板路较多，行李箱建议用轮子大的'
    }
    
    if city in city_tips:
        tips.append(city_tips[city])
    
    return tips
