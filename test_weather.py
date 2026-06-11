"""
天气API测试脚本
用于验证WeatherAPI.com是否正常工作
"""
import requests
import sys

# WeatherAPI.com 测试URL
TEST_API_KEY = "demo"  # 使用demo key测试

def test_weather_api(api_key):
    """测试天气API"""
    print("=" * 60)
    print("天气API测试")
    print("=" * 60)
    
    # 测试1：实时天气
    print("\n[测试1] 实时天气查询...")
    url = f"https://api.weatherapi.com/v1/current.json?key={api_key}&q=beijing&lang=zh"
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        
        if "error" in data:
            print(f"❌ 测试失败: {data['error']['message']}")
            return False
        
        print(f"✅ API连接成功!")
        print(f"   城市: {data['location']['name']}")
        print(f"   天气: {data['current']['condition']['text']}")
        print(f"   温度: {data['current']['temp_c']}°C")
        print(f"   湿度: {data['current']['humidity']}%")
        return True
        
    except requests.exceptions.Timeout:
        print("❌ 请求超时")
        return False
    except requests.exceptions.RequestException as e:
        print(f"❌ 网络错误: {e}")
        return False

def test_forecast(api_key):
    """测试天气预报"""
    print("\n[测试2] 天气预报查询...")
    url = f"https://api.weatherapi.com/v1/forecast.json?key={api_key}&q=shanghai&days=3&lang=zh"
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        
        if "error" in data:
            print(f"❌ 天气预报测试失败: {data['error']['message']}")
            return False
        
        print(f"✅ 天气预报API正常")
        print(f"   预报天数: {len(data['forecast']['forecastday'])}天")
        return True
        
    except Exception as e:
        print(f"❌ 天气预报测试失败: {e}")
        return False

def test_search(api_key):
    """测试城市搜索"""
    print("\n[测试3] 城市搜索测试...")
    url = f"https://api.weatherapi.com/v1/search.json?key={api_key}&q=guang"
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        
        if isinstance(data, list) and len(data) > 0:
            print(f"✅ 搜索API正常，找到 {len(data)} 个结果")
            print(f"   示例: {data[0]['name']}")
            return True
        
        print("⚠️ 搜索API响应异常")
        return False
        
    except Exception as e:
        print(f"❌ 搜索测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("\n" + "=" * 60)
    print("WeatherAPI.com API 测试")
    print("=" * 60)
    print("\n测试说明:")
    print("- 如果看到 'API连接成功'，说明API配置正确")
    print("- 如果看到 'Invalid key' 或 'API key not found'，")
    print("  请检查您的API Key是否正确")
    print("- 如果看到网络错误，请检查网络连接")
    print()
    
    # 读取配置文件中的API Key
    try:
        with open("config.py", "r", encoding="utf-8") as f:
            content = f.read()
            for line in content.split("\n"):
                if "WEATHER_API_KEY" in line and "=" in line:
                    api_key = line.split("=")[1].strip().strip('"').strip("'")
                    if api_key and api_key != "YOUR_WEATHER_API_KEY":
                        print(f"找到配置的API Key: {api_key[:10]}...")
                        break
            else:
                print("⚠️ 未找到有效的API Key")
                print("请编辑 config.py 文件，设置您的WeatherAPI.com API Key")
                print("\n获取API Key: https://www.weatherapi.com/")
                return
    except Exception as e:
        print(f"❌ 读取配置文件失败: {e}")
        return
    
    # 执行测试
    results = []
    results.append(test_weather_api(api_key))
    results.append(test_forecast(api_key))
    results.append(test_search(api_key))
    
    # 输出结果
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"✅ 所有测试通过! ({passed}/{total})")
        print("\n您的天气API配置正确，可以正常使用！")
    else:
        print(f"⚠️ 部分测试失败 ({passed}/{total})")
        print("\n常见问题解决方案:")
        print("1. 确保API Key正确无误")
        print("2. 检查API Key是否已激活")
        print("3. 确认API调用次数未超限")
        print("4. 查看 https://www.weatherapi.com/docs/ 获取帮助")

if __name__ == "__main__":
    main()