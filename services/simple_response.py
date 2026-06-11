import random

def get_greeting_response(message):
    greeting_responses = [
        "你好！有什么我可以帮你的吗？",
        "您好！很高兴为您服务。",
        "嗨！需要我帮您规划旅游路线吗？",
        "你好呀！请问有什么可以帮助您的？",
        "您好！我是旅游计划生成助手，随时为您服务。"
    ]
    
    # 根据具体问候语返回更贴切的回复
    if "早上好" in message or "上午好" in message:
        return "早上好！新的一天，有什么旅游计划吗？"
    elif "下午好" in message:
        return "下午好！需要我帮您查询天气或者规划行程吗？"
    elif "晚上好" in message:
        return "晚上好！今天玩得开心吗？需要什么帮助？"
    elif "晚安" in message:
        return "晚安！祝你好梦，明天见！"
    
    return random.choice(greeting_responses)

def get_thanks_response():
    thanks_responses = [
        "不客气！能帮到您我很开心。",
        "不用谢！祝您旅途愉快！",
        "这是我应该做的，有需要随时找我。",
        "不客气，希望您有一个美好的旅程！"
    ]
    return random.choice(thanks_responses)