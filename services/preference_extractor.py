def extract_preferences(message):

    preferences = {}

    # 喜欢海边
    if "海边" in message:
        preferences["travel_type"] = "海边旅行"

    # 喜欢爬山
    if "爬山" in message:
        preferences["travel_type"] = "爬山旅行"

    # 喜欢美食
    if "美食" in message:
        preferences["interest"] = "美食"

    # 喜欢拍照
    if "拍照" in message:
        preferences["interest"] = "拍照"

    # 喜欢安静
    if "安静" in message:
        preferences["environment"] = "安静"

    # 喜欢自由行
    if "自由行" in message:
        preferences["travel_mode"] = "自由行"

    # 喜欢跟团
    if "跟团" in message:
        preferences["travel_mode"] = "跟团"

    # 预算低
    if "便宜" in message or "省钱" in message:
        preferences["budget"] = "低预算"

    # 高预算
    if "高端" in message or "豪华" in message:
        preferences["budget"] = "高预算"

    return preferences