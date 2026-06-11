import json
import os
from datetime import datetime

# 使用项目根目录的绝对路径，确保在任何目录下运行都能找到数据文件
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONVERSATION_FILE = os.path.join(PROJECT_ROOT, "conversation_history.json")

def save_conversation(user_message, ai_response):
    history = load_conversation()
    
    history.append({
        "role": "user",
        "content": user_message,
        "timestamp": datetime.now().isoformat()
    })
    history.append({
        "role": "assistant",
        "content": ai_response,
        "timestamp": datetime.now().isoformat()
    })
    
    with open(CONVERSATION_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=4)

def load_conversation():
    if not os.path.exists(CONVERSATION_FILE):
        return []
    
    with open(CONVERSATION_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def clear_conversation():
    if os.path.exists(CONVERSATION_FILE):
        os.remove(CONVERSATION_FILE)

def get_conversation_history():
    return load_conversation()

def get_recent_conversations(limit=10):
    """获取最近的对话记录列表（按日期分组）"""
    history = load_conversation()
    
    if not history:
        return []
    
    # 按日期分组
    grouped = {}
    for item in history:
        timestamp = item.get("timestamp", "")
        if timestamp:
            date = timestamp.split("T")[0]
            if date not in grouped:
                grouped[date] = []
            grouped[date].append(item)
    
    # 转换为列表并按日期排序（最新的在前）
    result = []
    for date in sorted(grouped.keys(), reverse=True)[:limit]:
        messages = grouped[date]
        # 获取第一条用户消息作为会话标题
        first_user_msg = next((m["content"] for m in messages if m["role"] == "user"), "")
        # 获取会话时间（第一条消息的时间）
        first_time = messages[0].get("timestamp", "") if messages else ""
        
        result.append({
            "date": date,
            "time": first_time,
            "preview": first_user_msg[:50] + "..." if len(first_user_msg) > 50 else first_user_msg,
            "message_count": len(messages) // 2  # 每轮对话包含用户和助手消息
        })
    
    return result

def get_conversation_by_date(date_str):
    """获取指定日期的对话记录"""
    history = load_conversation()
    
    result = []
    for item in history:
        timestamp = item.get("timestamp", "")
        if timestamp.startswith(date_str):
            result.append(item)
    
    return result