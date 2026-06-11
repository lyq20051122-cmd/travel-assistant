import json
import os

# 使用项目根目录的绝对路径，确保在任何目录下运行都能找到数据文件
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CITY_DATA_FILE = os.path.join(PROJECT_ROOT, "data", "city_knowledge.json")

def load_city_data():
    """加载城市知识库数据"""
    if not os.path.exists(CITY_DATA_FILE):
        return {"cities": []}
    
    with open(CITY_DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def get_all_cities():
    """获取所有城市列表"""
    data = load_city_data()
    return data.get("cities", [])

def get_city_by_id(city_id):
    """根据城市ID获取城市详情"""
    cities = get_all_cities()
    for city in cities:
        if city.get("id") == city_id:
            return city
    return None

def search_cities(keyword):
    """搜索城市（按名称或省份）"""
    cities = get_all_cities()
    results = []
    keyword_lower = keyword.lower()
    
    for city in cities:
        if (keyword_lower in city.get("name", "").lower() or 
            keyword_lower in city.get("province", "").lower()):
            results.append(city)
    
    return results