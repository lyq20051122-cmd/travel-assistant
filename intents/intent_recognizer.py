def recognize_intent(message):

    # 问候语意图
    greetings = ["你好", "您好", "嗨", "哈喽", "hello", "hi", "早上好", "上午好", "下午好", "晚上好", "晚安", "您好啊", "你好啊"]
    for greeting in greetings:
        if greeting in message:
            return "greeting"

    # 感谢意图
    thanks = ["谢谢", "谢谢你", "非常感谢", "多谢", "辛苦了"]
    for thank in thanks:
        if thank in message:
            return "thanks"

    # 天气查询意图
    if "天气" in message:
        return "weather"

    # 旅游规划意图
    if "规划" in message or "旅游" in message or "旅行" in message:
        return "travel"

    # 闲聊意图
    return "chat"