#!/usr/bin/env python3
"""直接测试新功能服务"""

import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, '.')

def test_itinerary_service():
    print("测试智能行程规划服务...")
    from services.itinerary_service import generate_itinerary
    
    try:
        itinerary = generate_itinerary("杭州", 3, ["sightseeing", "food"], "medium")
        print("✅ 智能行程规划服务正常")
        print(f"   目的地：{itinerary['city']}")
        print(f"   天数：{itinerary['days']}天")
        for day_plan in itinerary['days_plan']:
            print(f"   Day{day_plan['day']}: {day_plan['date']}")
            if day_plan['morning']:
                print(f"      上午: {day_plan['morning']['activity']} - {day_plan['morning']['place']}")
            if day_plan['afternoon']:
                print(f"      下午: {day_plan['afternoon']['activity']} - {day_plan['afternoon']['place']}")
    except Exception as e:
        print(f"❌ 智能行程规划服务异常: {e}")

def test_recommendation_service():
    print("\n测试个性化推荐服务...")
    from services.recommendation_service import get_personalized_recommendations
    
    try:
        recommendations = get_personalized_recommendations(None)
        print("✅ 个性化推荐服务正常")
        print(f"   季节：{recommendations['season_name']}")
        print(f"   推荐城市数：{len(recommendations['top_destinations'])}")
        for city in recommendations['top_destinations'][:3]:
            print(f"   - {city['city']} (评分: {city['score']})")
    except Exception as e:
        print(f"❌ 个性化推荐服务异常: {e}")

def test_budget_service():
    print("\n测试预算估算服务...")
    from services.budget_service import estimate_budget
    
    try:
        budget = estimate_budget("成都", 5, "medium", "leisure")
        print("✅ 预算估算服务正常")
        print(f"   目的地：{budget['city']}")
        print(f"   总预算：¥{budget['total_estimate']:,}")
        print("   费用明细：")
        for category, details in budget['breakdown'].items():
            print(f"      {details['description']}: ¥{details['cost']:,}")
    except Exception as e:
        print(f"❌ 预算估算服务异常: {e}")

def test_alert_service():
    print("\n测试智能安全提醒服务...")
    from services.alert_service import schedule_daily_weather_brief, generate_travel_reminder
    
    try:
        brief = schedule_daily_weather_brief(None)
        print("✅ 每日天气简报生成正常")
        print("   简报预览：")
        lines = brief.split('\n')[:8]
        for line in lines:
            print(f"   {line}")
    except Exception as e:
        print(f"❌ 每日天气简报异常: {e}")
    
    try:
        reminder = generate_travel_reminder("三亚", "2026-07-01", {"interests": ["nature"]})
        print("\n✅ 旅行提醒生成正常")
        print("   提醒预览：")
        lines = reminder.split('\n')[:6]
        for line in lines:
            print(f"   {line}")
    except Exception as e:
        print(f"❌ 旅行提醒异常: {e}")

if __name__ == "__main__":
    print("="*60)
    print("测试旅游助手新功能服务")
    print("="*60)
    
    test_itinerary_service()
    test_recommendation_service()
    test_budget_service()
    test_alert_service()
    
    print("\n" + "="*60)
    print("测试完成！")
    print("="*60)
