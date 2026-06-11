"""
旅行预算估算器
根据目的地、天数、住宿标准自动估算旅行费用
"""
from datetime import datetime, timedelta

def estimate_budget(city, days, budget_level='medium', travel_style='leisure'):
    """
    估算旅行预算
    
    Args:
        city: 目的地城市
        days: 旅行天数
        budget_level: 预算等级 'low', 'medium', 'high'
        travel_style: 旅行风格 'leisure', 'adventure', 'business', 'luxury'
    
    Returns:
        预算估算结果字典
    """
    budget = {
        'city': city,
        'days': days,
        'budget_level': budget_level,
        'travel_style': travel_style,
        'total_estimate': 0,
        'breakdown': {},
        'currency': 'CNY',
        'suggestions': []
    }
    
    # 获取城市基准价格
    city_prices = get_city_price_level(city)
    
    # 计算各项费用
    transport_cost = calculate_transport_cost(city, budget_level, travel_style)
    accommodation_cost = calculate_accommodation_cost(city, days, budget_level)
    food_cost = calculate_food_cost(city, days, budget_level)
    attraction_cost = calculate_attraction_cost(city, days, budget_level)
    shopping_cost = calculate_shopping_cost(city, days, budget_level, travel_style)
    other_cost = calculate_other_cost(days, budget_level)
    
    # 汇总费用
    total_cost = transport_cost + accommodation_cost + food_cost + attraction_cost + shopping_cost + other_cost
    
    # 添加到预算结果
    budget['breakdown'] = {
        'transport': {
            'description': '交通费用（含往返交通）',
            'cost': transport_cost,
            'unit': '元'
        },
        'accommodation': {
            'description': '住宿费用',
            'cost': accommodation_cost,
            'unit': '元'
        },
        'food': {
            'description': '餐饮费用',
            'cost': food_cost,
            'unit': '元'
        },
        'attractions': {
            'description': '景点门票',
            'cost': attraction_cost,
            'unit': '元'
        },
        'shopping': {
            'description': '购物消费',
            'cost': shopping_cost,
            'unit': '元'
        },
        'other': {
            'description': '其他费用（交通、小费等）',
            'cost': other_cost,
            'unit': '元'
        }
    }
    
    budget['total_estimate'] = total_cost
    
    # 添加预算建议
    budget['suggestions'] = generate_budget_suggestions(city, days, budget_level, total_cost)
    
    return budget

def get_city_price_level(city):
    """获取城市价格等级"""
    price_levels = {
        'high': {
            'cities': ['北京', '上海', '深圳'],
            'multiplier': 1.3
        },
        'medium': {
            'cities': ['广州', '杭州', '成都', '重庆', '西安', '南京', '武汉', '苏州', '青岛', '厦门', '三亚', '大连'],
            'multiplier': 1.0
        },
        'low': {
            'cities': ['昆明', '丽江', '贵阳', '承德', '西宁', '长沙', '洛阳', '开封', '海口', '珠海', '西双版纳', '扬州', '无锡'],
            'multiplier': 0.7
        }
    }
    
    for level, data in price_levels.items():
        if city in data['cities']:
            return {'level': level, 'multiplier': data['multiplier']}
    
    return {'level': 'medium', 'multiplier': 1.0}

def calculate_transport_cost(city, budget_level, travel_style):
    """计算交通费用"""
    # 基准价格（假设从主要城市出发）
    base_costs = {
        'low': 300,
        'medium': 600,
        'high': 1200
    }
    
    city_price = get_city_price_level(city)
    
    # 根据旅行风格调整
    style_multiplier = {
        'leisure': 1.0,
        'adventure': 0.8,
        'business': 1.2,
        'luxury': 2.0
    }
    
    base = base_costs[budget_level]
    multiplier = city_price['multiplier'] * style_multiplier[travel_style]
    
    return int(base * multiplier)

def calculate_accommodation_cost(city, days, budget_level):
    """计算住宿费用"""
    # 日均住宿价格
    daily_rates = {
        'low': {
            'high': 300,
            'medium': 200,
            'low': 120
        },
        'medium': {
            'high': 500,
            'medium': 350,
            'low': 220
        },
        'high': {
            'high': 800,
            'medium': 600,
            'low': 400
        }
    }
    
    city_price_level = get_city_price_level(city)['level']
    daily_rate = daily_rates[budget_level][city_price_level]
    
    # 住宿天数 = 旅行天数 - 1（到达当天不算全天住宿）
    nights = max(1, days - 1)
    
    return daily_rate * nights

def calculate_food_cost(city, days, budget_level):
    """计算餐饮费用"""
    # 日均餐饮费用
    daily_costs = {
        'low': {
            'high': 120,
            'medium': 80,
            'low': 50
        },
        'medium': {
            'high': 200,
            'medium': 150,
            'low': 100
        },
        'high': {
            'high': 400,
            'medium': 300,
            'low': 200
        }
    }
    
    city_price_level = get_city_price_level(city)['level']
    daily_cost = daily_costs[budget_level][city_price_level]
    
    return daily_cost * days

def calculate_attraction_cost(city, days, budget_level):
    """计算景点门票费用"""
    # 日均景点费用
    daily_costs = {
        'low': {
            'high': 80,
            'medium': 60,
            'low': 40
        },
        'medium': {
            'high': 150,
            'medium': 120,
            'low': 80
        },
        'high': {
            'high': 300,
            'medium': 200,
            'low': 150
        }
    }
    
    city_price_level = get_city_price_level(city)['level']
    daily_cost = daily_costs[budget_level][city_price_level]
    
    # 假设每天去1-2个景点
    return daily_cost * days

def calculate_shopping_cost(city, days, budget_level, travel_style):
    """计算购物费用"""
    base_amounts = {
        'low': 200,
        'medium': 500,
        'high': 1500
    }
    
    city_price = get_city_price_level(city)
    
    # 购物倾向
    shopping_multiplier = {
        'leisure': 1.0,
        'adventure': 0.5,
        'business': 0.8,
        'luxury': 2.0
    }
    
    base = base_amounts[budget_level]
    multiplier = city_price['multiplier'] * shopping_multiplier[travel_style]
    
    # 购物通常不是每天都进行
    return int(base * multiplier * min(days, 3) / 3)

def calculate_other_cost(days, budget_level):
    """计算其他费用"""
    base_amounts = {
        'low': 50,
        'medium': 100,
        'high': 200
    }
    
    return base_amounts[budget_level] * days

def generate_budget_suggestions(city, days, budget_level, total_cost):
    """生成预算建议"""
    suggestions = []
    
    # 总体预算评估
    per_day_cost = total_cost / days
    if per_day_cost < 300:
        suggestions.append('您的预算比较紧凑，建议选择经济型住宿和公共交通')
    elif per_day_cost < 600:
        suggestions.append('您的预算适中，可以享受舒适的旅行体验')
    else:
        suggestions.append('您的预算充裕，可以享受高品质的旅行服务')
    
    # 省钱建议
    if budget_level == 'low':
        suggestions.append('省钱小贴士：可以选择青年旅舍或民宿，品尝当地小吃')
    
    # 城市特定建议
    city_suggestions = {
        '北京': '北京景点门票相对较高，建议提前规划好路线',
        '上海': '上海餐饮选择丰富，从平价小吃到高端餐厅都有',
        '广州': '广州物价相对亲民，早茶是性价比很高的选择',
        '成都': '成都美食众多且价格实惠，住宿选择也很丰富',
        '杭州': '西湖周边有很多免费景点，可以节省门票费用',
        '三亚': '三亚旅游旺季价格会上涨，建议错峰出行'
    }
    
    if city in city_suggestions:
        suggestions.append(city_suggestions[city])
    
    return suggestions

def format_budget(cost):
    """格式化预算金额"""
    return f"¥{cost:,.0f}"

def get_budget_summary(budget):
    """获取预算摘要"""
    summary = {
        'total': format_budget(budget['total_estimate']),
        'per_day': format_budget(int(budget['total_estimate'] / budget['days'])),
        'breakdown': {}
    }
    
    for category, details in budget['breakdown'].items():
        summary['breakdown'][category] = format_budget(details['cost'])
    
    return summary
