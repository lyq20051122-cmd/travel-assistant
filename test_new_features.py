#!/usr/bin/env python3
"""测试新功能API"""

import sys
sys.stdout.reconfigure(encoding='utf-8')
import requests

BASE_URL = "http://127.0.0.1:5000"

def test_recommendations():
    print("测试个性化推荐API...")
    try:
        response = requests.get(f"{BASE_URL}/api/recommendations")
        if response.status_code == 200:
            data = response.json()
            print("✅ 个性化推荐API正常")
            print(f"   季节：{data['recommendations']['season_name']}")
            print(f"   推荐城市数：{len(data['recommendations']['top_destinations'])}")
            for city in data['recommendations']['top_destinations'][:3]:
                print(f"   - {city['city']} (评分: {city['score']})")
        else:
            print(f"❌ 个性化推荐API失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 个性化推荐API异常: {e}")

def test_itinerary():
    print("\n测试智能行程规划API...")
    try:
        data = {
            "city": "杭州",
            "days": 3,
            "preferences": ["sightseeing", "food"],
            "budget": "medium"
        }
        response = requests.post(f"{BASE_URL}/api/itinerary/generate", json=data)
        if response.status_code == 200:
            result = response.json()
            itinerary = result['itinerary']
            print("✅ 智能行程规划API正常")
            print(f"   目的地：{itinerary['city']}")
            print(f"   天数：{itinerary['days']}天")
            for day_plan in itinerary['days_plan']:
                print(f"   Day{day_plan['day']}: {day_plan['date']}")
                if day_plan['morning']:
                    print(f"      上午: {day_plan['morning']['activity']} - {day_plan['morning']['place']}")
                if day_plan['afternoon']:
                    print(f"      下午: {day_plan['afternoon']['activity']} - {day_plan['afternoon']['place']}")
        else:
            print(f"❌ 智能行程规划API失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 智能行程规划API异常: {e}")

def test_budget():
    print("\n测试预算估算API...")
    try:
        data = {
            "city": "成都",
            "days": 5,
            "budget_level": "medium",
            "travel_style": "leisure"
        }
        response = requests.post(f"{BASE_URL}/api/budget/estimate", json=data)
        if response.status_code == 200:
            result = response.json()
            budget = result['budget']
            print("✅ 预算估算API正常")
            print(f"   目的地：{budget['city']}")
            print(f"   总预算：¥{budget['total_estimate']:,}")
            print("   费用明细：")
            for category, details in budget['breakdown'].items():
                print(f"      {details['description']}: ¥{details['cost']:,}")
        else:
            print(f"❌ 预算估算API失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 预算估算API异常: {e}")

def test_daily_brief():
    print("\n测试每日天气简报API...")
    try:
        response = requests.get(f"{BASE_URL}/api/alert/daily-brief")
        if response.status_code == 200:
            data = response.json()
            print("✅ 每日天气简报API正常")
            print("   简报内容预览：")
            print("   " + data['brief'][:200].replace('\n', '\n   '))
        else:
            print(f"❌ 每日天气简报API失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 每日天气简报API异常: {e}")

def test_travel_reminder():
    print("\n测试旅行提醒API...")
    try:
        data = {
            "destination": "三亚",
            "date": "2026-07-01",
            "preferences": {"interests": ["nature", "beach"]}
        }
        response = requests.post(f"{BASE_URL}/api/alert/travel-reminder", json=data)
        if response.status_code == 200:
            result = response.json()
            print("✅ 旅行提醒API正常")
            print("   提醒内容：")
            print("   " + result['reminder'][:150].replace('\n', '\n   '))
        else:
            print(f"❌ 旅行提醒API失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 旅行提醒API异常: {e}")

if __name__ == "__main__":
    print("="*60)
    print("测试旅游助手新功能API")
    print("="*60)
    
    test_recommendations()
    test_itinerary()
    test_budget()
    test_daily_brief()
    test_travel_reminder()
    
    print("\n" + "="*60)
    print("测试完成！")
    print("="*60)
