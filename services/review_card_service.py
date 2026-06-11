"""
旅行回顾卡片生成服务 (Travel Review Card Generator)
====================================================
智能生成旅行回顾卡片：利用 LLM + 行程数据 + 用户画像 + 天气历史
生成包含叙事、评分、亮点、建议的精美回顾卡片

核心能力：
- 多源上下文聚合（行程/画像/天气/对话/城市知识）
- LLM 驱动的结构化内容生成
- JSON 持久化存储
- Markdown 导出
"""
import json
import os
import re
from datetime import datetime
from typing import Dict, List, Optional

# 项目根目录与数据目录
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
REVIEW_CARDS_FILE = os.path.join(DATA_DIR, "review_cards.json")


# ============================================================
# 数据持久化
# ============================================================

def _ensure_data_dir():
    """确保数据目录存在"""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)


def load_review_cards() -> Dict[str, dict]:
    """加载所有回顾卡片"""
    _ensure_data_dir()
    if not os.path.exists(REVIEW_CARDS_FILE):
        return {}
    try:
        with open(REVIEW_CARDS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_review_cards(cards: Dict[str, dict]):
    """保存回顾卡片"""
    _ensure_data_dir()
    with open(REVIEW_CARDS_FILE, "w", encoding="utf-8") as f:
        json.dump(cards, f, ensure_ascii=False, indent=2)


# ============================================================
# 上下文收集
# ============================================================

def get_trip_weather_summary(destination: str, start_date: str, end_date: str) -> dict:
    """
    从 weather_history.json 提取行程期间的天气统计。
    返回摘要 dict，无数据时返回空摘要。
    """
    from services.data_storage import load_weather_history
    weather_history = load_weather_history()

    # 尝试城市名匹配（weather_history key 是中文城市名）
    city_records = weather_history.get(destination, [])

    # 如果直接匹配失败，尝试模糊匹配
    if not city_records:
        for city_name, records in weather_history.items():
            if destination in city_name or city_name in destination:
                city_records = records
                break

    trip_records = []
    for record in city_records:
        ts = record.get("timestamp", "")
        if ts[:10] >= start_date and ts[:10] <= end_date:
            trip_records.append(record)

    if not trip_records:
        return {
            "summary": f"暂无{destination}在旅行期间（{start_date}至{end_date}）的天气数据",
            "avg_temp": None,
            "max_temp": None,
            "min_temp": None,
            "rain_days": 0,
            "dominant_conditions": "未知",
            "record_count": 0
        }

    temps = []
    conditions = []
    for r in trip_records:
        data = r.get("data", {})
        if "temperature" in data:
            temps.append(data["temperature"])
        cond = data.get("condition", "")
        if cond:
            conditions.append(cond)

    if not temps:
        temps = [25]

    avg_temp = round(sum(temps) / len(temps), 1)
    max_temp = max(temps)
    min_temp = min(temps)

    # 统计降雨天数
    rain_days = 0
    for cond in conditions:
        if any(w in str(cond) for w in ["雨", "雪", "rain", "snow", "drizzle", "shower"]):
            rain_days += 1

    # 主导天气状况
    from collections import Counter
    cond_counter = Counter(conditions)
    dominant = cond_counter.most_common(2)
    dominant_str = "、".join([c for c, _ in dominant]) if dominant else "未知"

    summary_text = (
        f"旅行期间{destination}天气：平均气温{avg_temp}°C（最高{max_temp}°C，最低{min_temp}°C），"
        f"以{dominant_str}为主"
        + (f"，共有{rain_days}天有降水" if rain_days > 0 else "，天气晴好")
    )

    return {
        "summary": summary_text,
        "avg_temp": avg_temp,
        "max_temp": max_temp,
        "min_temp": min_temp,
        "rain_days": rain_days,
        "dominant_conditions": dominant_str,
        "record_count": len(trip_records)
    }


def estimate_trip_budget(days_plan: List[Dict], persona_budget_level: str = "medium") -> dict:
    """
    从 days_plan 各活动的 budget 字段估算总花费。
    解析 "¥120" / "¥100-200" / "¥0" 等格式。
    """
    actual = 0
    for day in days_plan:
        for period in ["morning", "afternoon", "evening"]:
            activity = day.get(period, {})
            budget_str = activity.get("budget", "¥0") if activity else "¥0"
            # 提取所有数字
            nums = re.findall(r"\d+", str(budget_str))
            if nums:
                # 如果是范围（如 ¥100-200），取上限
                actual += int(nums[-1])

    # 根据用户预算等级给出参考值
    budget_per_day = {"low": 500, "medium": 1000, "high": 2000}
    per_day = budget_per_day.get(persona_budget_level, 1000)
    estimated = per_day * max(len(days_plan), 1)

    return {
        "estimated": estimated,
        "actual": actual if actual > 0 else estimated,
        "currency": "CNY",
        "per_day": round(actual / max(len(days_plan), 1)) if actual > 0 else per_day
    }


def gather_trip_context(trip_id: str, user_id: str) -> dict:
    """
    聚合生成回顾卡片所需的所有上下文数据。
    返回完整的 context dict 供 LLM prompt 使用。
    """
    from services.trip_guardian_service import trip_guardian_service
    from services.persona_service import persona_service
    from services.conversation_service import get_conversation_history
    from services.city_service import get_city_by_id, get_all_cities

    # 1. 获取行程数据
    trip = trip_guardian_service._trips.get(trip_id)
    if not trip:
        raise ValueError(f"行程不存在: {trip_id}")

    # 2. 获取用户画像上下文
    persona_context = persona_service.generate_persona_context_for_prompt(user_id)
    persona = persona_service.get_persona(user_id)

    # 3. 获取天气摘要
    weather_result = get_trip_weather_summary(
        trip.destination, trip.start_date, trip.end_date
    )

    # 4. 获取城市知识
    city_info = None
    all_cities = get_all_cities()
    for city in all_cities:
        city_name = city.get("name", city.get("city", ""))
        if city_name in trip.destination or trip.destination in city_name:
            city_info = city
            break

    city_culture = ""
    if city_info:
        culture = city_info.get("culture", "")
        best_time = city_info.get("best_time", "")
        food_list = city_info.get("food", [])
        food_str = "、".join(food_list[:5]) if food_list else ""
        city_culture = f"城市文化：{culture}\n最佳旅行时间：{best_time}\n特色美食：{food_str}"

    # 5. 获取对话摘要（旅行期间的对话）
    conversation_history = get_conversation_history()
    trip_snippets = []
    for item in conversation_history:
        ts = item.get("timestamp", "")
        if ts[:10] >= trip.start_date and ts[:10] <= trip.end_date:
            if item.get("role") == "user":
                content = item.get("content", "")
                if len(content) > 80:
                    content = content[:80] + "..."
                trip_snippets.append(f"用户: {content}")
    conversation_text = "\n".join(trip_snippets[-10:]) if trip_snippets else "暂无旅行期间对话记录"

    # 6. 获取 guardian 干预记录
    guardian_interventions = ""
    if trip.intervention_log:
        interventions = []
        for log_entry in trip.intervention_log[-5:]:
            event = log_entry.get("event", log_entry.get("message", ""))
            interventions.append(f"- {event}")
        guardian_interventions = "行程中的主动提醒：\n" + "\n".join(interventions)

    # 7. 构建行程文本
    days_plan_text = ""
    for day in trip.days_plan:
        day_num = day.get("day", "?")
        day_date = day.get("date", "")
        days_plan_text += f"\n第{day_num}天（{day_date}）：\n"
        for period, label in [("morning", "上午"), ("afternoon", "下午"), ("evening", "晚上")]:
            activity = day.get(period, {})
            if activity:
                place = activity.get("place", "")
                act = activity.get("activity", "")
                duration = activity.get("duration", "")
                days_plan_text += f"  {label}: {act}"
                if place:
                    days_plan_text += f" @ {place}"
                if duration:
                    days_plan_text += f" ({duration})"
                days_plan_text += "\n"

    # 8. 获取用户画像摘要
    budget_level = persona.budget_level if persona else "medium"
    interests_summary = ""
    if persona:
        top_interests = persona.get_top_interests(5)
        interests_summary = f"偏好标签: {', '.join([f'{tag}({weight:.2f})' for tag, weight in top_interests])}"

    return {
        "trip": trip,
        "persona_context": persona_context,
        "persona": persona,
        "weather_summary": weather_result["summary"],
        "weather_detail": weather_result,
        "city_culture": city_culture,
        "conversation_text": conversation_text,
        "guardian_interventions": guardian_interventions,
        "days_plan_text": days_plan_text,
        "budget_level": budget_level,
        "interests_summary": interests_summary,
        "destination": trip.destination,
        "start_date": trip.start_date,
        "end_date": trip.end_date,
        "duration_days": len(trip.days_plan)
    }


# ============================================================
# LLM Prompt 构建与响应解析
# ============================================================

def build_review_prompt(context: dict) -> str:
    """构建 LLM prompt，要求生成结构化 JSON 回顾卡片"""

    prompt = f"""你是一位旅行回顾写作专家。请根据以下信息，为用户的旅行生成一份温暖的回顾卡片。

## 用户画像
{context['persona_context']}

## 旅行信息
目的地：{context['destination']}
日期：{context['start_date']} 至 {context['end_date']}（共{context['duration_days']}天）
行程安排：
{context['days_plan_text']}

## 旅行期间天气
{context['weather_summary']}

## 城市特色
{context['city_culture'] or '无额外城市信息'}

## 对话历史摘要（旅行期间的交流）
{context['conversation_text']}

## 行程守护者提醒
{context['guardian_interventions'] or '无特殊提醒'}

## 任务
请用中文生成旅行回顾卡片，严格按以下JSON格式返回（不要包含markdown代码块标记，直接返回纯JSON）：

{{
  "narrative": "一段温暖的旅行回顾叙事，150-250字，用第一人称角度，提到具体的景点和体验，语气像在和朋友分享旅行的美好",
  "ratings": {{
    "attractions": 1-5的整数,
    "food": 1-5的整数,
    "weather": 1-5的整数,
    "budget_match": 1-5的整数,
    "overall": 1-5的整数
  }},
  "highlights": ["亮点1（约15字）", "亮点2（约15字）", "亮点3（约15字）"],
  "tips": ["实用建议1", "实用建议2", "实用建议3"],
  "tags": ["标签1（2-4字）", "标签2（2-4字）", "标签3（2-4字）", "标签4（2-4字）", "标签5（2-4字）"]
}}

要求：
- narrative要有温度和画面感，必须提到至少1-2个行程中的具体景点名称和体验细节
- highlights每条约15字，概括最精彩的时刻或体验
- tips要实用，结合天气、季节和当地特色
- tags从用户兴趣偏好和旅行特点中提取，每个2-4字，共3-5个
- ratings要合理分布，整体评分不高于各分项平均分过多
- 必须返回纯JSON，不要包含任何markdown代码块标记```"""

    return prompt


def _parse_llm_response(raw_text: str) -> dict:
    """解析 LLM 返回的原始文本，提取结构化 JSON。多级降级策略。"""
    if not raw_text:
        return _build_fallback_card("LLM 返回为空")

    # 策略1: 直接 JSON 解析
    try:
        return json.loads(raw_text.strip())
    except json.JSONDecodeError:
        pass

    # 策略2: 剥离 markdown 代码块后解析
    cleaned = raw_text.strip()
    # 移除 ```json ... ``` 或 ``` ... ```
    code_block_match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", cleaned, re.DOTALL)
    if code_block_match:
        try:
            return json.loads(code_block_match.group(1).strip())
        except json.JSONDecodeError:
            pass

    # 策略3: 尝试从文本中提取 JSON 对象
    brace_match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if brace_match:
        try:
            return json.loads(brace_match.group(0))
        except json.JSONDecodeError:
            pass

    # 策略4: 正则逐字段提取
    return _regex_extract_card(raw_text)


def _regex_extract_card(raw_text: str) -> dict:
    """正则降级提取：从非标准 LLM 输出中尽量抓取字段"""
    result = _build_fallback_card("LLM 返回格式异常，使用降级提取")

    # 提取 narrative（取最长的一段中文字符串）
    narrative_match = re.search(r'"narrative"\s*:\s*"([^"]*)"', raw_text, re.DOTALL)
    if narrative_match:
        result["narrative"] = narrative_match.group(1)

    # 提取 ratings
    for key in ["attractions", "food", "weather", "budget_match", "overall"]:
        rating_match = re.search(rf'"{key}"\s*:\s*(\d)', raw_text)
        if rating_match:
            result["ratings"][key] = int(rating_match.group(1))

    # 提取 highlights
    highlights_match = re.search(r'"highlights"\s*:\s*\[(.*?)\]', raw_text, re.DOTALL)
    if highlights_match:
        items = re.findall(r'"([^"]*)"', highlights_match.group(1))
        if items:
            result["highlights"] = items[:3]

    # 提取 tips
    tips_match = re.search(r'"tips"\s*:\s*\[(.*?)\]', raw_text, re.DOTALL)
    if tips_match:
        items = re.findall(r'"([^"]*)"', tips_match.group(1))
        if items:
            result["tips"] = items[:3]

    # 提取 tags
    tags_match = re.search(r'"tags"\s*:\s*\[(.*?)\]', raw_text, re.DOTALL)
    if tags_match:
        items = re.findall(r'"([^"]*)"', tags_match.group(1))
        if items:
            result["tags"] = items[:5]

    return result


def _build_fallback_card(reason: str) -> dict:
    """生成降级卡片（规则型，不依赖 LLM）"""
    return {
        "narrative": f"这次旅行充满了美好的回忆，虽然有些小插曲，但每一个瞬间都值得珍藏。感谢旅行中的每一次相遇和每一处风景。",
        "ratings": {
            "attractions": 4,
            "food": 4,
            "weather": 3,
            "budget_match": 4,
            "overall": 4
        },
        "highlights": ["探索了新的目的地", "品尝了当地美食", "享受了美好的时光"],
        "tips": ["建议提前查看天气预报", "随身携带必要的药品", "多尝试当地特色小吃"],
        "tags": ["旅行", "美食", "风景", "文化", "回忆"]
    }


# ============================================================
# 卡片生成与 CRUD
# ============================================================

def generate_review_card(trip_id: str, user_id: str) -> dict:
    """
    主生成管道：
    1. 验证行程存在
    2. 收集所有上下文
    3. 构建 prompt 并调用 LLM
    4. 解析 LLM 响应
    5. 装配完整卡片
    6. 持久化
    """
    # 1. 收集上下文
    try:
        context = gather_trip_context(trip_id, user_id)
    except ValueError as e:
        return {"success": False, "message": str(e)}

    # 2. 检查是否已存在同 trip 的卡片
    existing_cards = load_review_cards()
    for card_id, card in existing_cards.items():
        if card.get("trip_id") == trip_id:
            # 返回已有卡片
            return {"success": True, "card": card, "existing": True}

    # 3. 调用 LLM
    from services.llm_service import ask_llm

    prompt = build_review_prompt(context)

    try:
        llm_response = ask_llm(prompt)
        card_content = _parse_llm_response(llm_response)
    except Exception as e:
        print(f"[ReviewCard] LLM调用失败: {e}，使用规则降级")
        card_content = _build_fallback_card(str(e))

    # 4. 预算估算（规则型，不依赖 LLM）
    budget_summary = estimate_trip_budget(
        context["trip"].days_plan, context["budget_level"]
    )

    # 5. 装配完整卡片
    card_id = f"rc_{user_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    card = {
        "card_id": card_id,
        "user_id": user_id,
        "trip_id": trip_id,
        "destination": context["destination"],
        "date_range": f"{context['start_date']} ~ {context['end_date']}",
        "duration_days": context["duration_days"],
        "generated_at": datetime.now().isoformat(),
        "overall_rating": card_content.get("ratings", {}).get("overall", 4),
        "ratings": card_content.get("ratings", _build_fallback_card("")["ratings"]),
        "highlights": card_content.get("highlights", ["探索了新的目的地", "品尝了当地美食", "享受了美好的时光"]),
        "weather_summary": context["weather_summary"],
        "weather_detail": context["weather_detail"],
        "budget_summary": budget_summary,
        "llm_narrative": card_content.get("narrative", ""),
        "tips": card_content.get("tips", []),
        "tags": card_content.get("tags", ["旅行", "回忆"]),
        "guardian_interventions": context["guardian_interventions"]
    }

    # 6. 持久化
    existing_cards[card_id] = card
    save_review_cards(existing_cards)

    # 7. 生成并存储 Markdown 导出内容
    card["export_markdown"] = _build_export_markdown(card)
    existing_cards[card_id]["export_markdown"] = card["export_markdown"]
    save_review_cards(existing_cards)

    return {"success": True, "card": card, "existing": False}


def list_cards_for_user(user_id: str) -> List[dict]:
    """列出用户的所有卡片，按生成时间倒序"""
    cards = load_review_cards()
    user_cards = [
        c for c in cards.values()
        if c.get("user_id") == user_id
    ]
    user_cards.sort(key=lambda c: c.get("generated_at", ""), reverse=True)
    return user_cards


def get_card(card_id: str) -> Optional[dict]:
    """获取单张卡片"""
    cards = load_review_cards()
    return cards.get(card_id)


def delete_card(card_id: str) -> bool:
    """删除卡片"""
    cards = load_review_cards()
    if card_id in cards:
        del cards[card_id]
        save_review_cards(cards)
        return True
    return False


# ============================================================
# Markdown 导出
# ============================================================

def _build_export_markdown(card: dict) -> str:
    """生成精美 Markdown 文档"""

    def stars(n: int) -> str:
        return "★" * int(n) + "☆" * (5 - int(n))

    r = card.get("ratings", {})
    md = f"""# 🗺️ {card['destination']} 旅行回顾

> **旅行日期**：{card.get('date_range', '')}
> **旅行天数**：{card.get('duration_days', '?')} 天
> **生成时间**：{card.get('generated_at', '')}

---

## ⭐ 综合评分：{r.get('overall', '?')}/5 {stars(r.get('overall', 4))}

| 维度 | 评分 |
|------|------|
| 🏛️ 景点 | {stars(r.get('attractions', 4))} {r.get('attractions', '?')}/5 |
| 🍜 美食 | {stars(r.get('food', 4))} {r.get('food', '?')}/5 |
| 🌤️ 天气 | {stars(r.get('weather', 3))} {r.get('weather', '?')}/5 |
| 💰 预算匹配 | {stars(r.get('budget_match', 4))} {r.get('budget_match', '?')}/5 |
| ⭐ 总体 | {stars(r.get('overall', 4))} {r.get('overall', '?')}/5 |

---

## 📝 旅行回顾

{card.get('llm_narrative', '')}

---

## ✨ 精彩亮点

"""
    for i, h in enumerate(card.get("highlights", []), 1):
        md += f"{i}. {h}\n"

    md += f"""
---

## 🌤️ 天气回顾

{card.get('weather_summary', '暂无天气数据')}

---

## 💰 预算概览

- 预估预算：¥{card.get('budget_summary', {}).get('estimated', '?')}
- 实际花费：¥{card.get('budget_summary', {}).get('actual', '?')}
- 日均花费：¥{card.get('budget_summary', {}).get('per_day', '?')}

---

## 💡 旅行建议

"""
    for i, tip in enumerate(card.get("tips", []), 1):
        md += f"{i}. {tip}\n"

    md += f"""
---

## 🏷️ 标签

"""
    for tag in card.get("tags", []):
        md += f"`{tag}` "

    md += f"""

---

*本回顾由 Travel Assistant 自动生成 | {card.get('generated_at', '')}*
"""
    return md


def export_card_markdown(card_id: str) -> Optional[str]:
    """导出卡片为 Markdown 并保存到 reports/ 目录"""
    card = get_card(card_id)
    if not card:
        return None

    md_content = card.get("export_markdown") or _build_export_markdown(card)

    # 保存到 reports 目录
    reports_dir = os.path.join(PROJECT_ROOT, "reports")
    os.makedirs(reports_dir, exist_ok=True)
    filename = f"review_{card_id}.md"
    filepath = os.path.join(reports_dir, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(md_content)

    # 更新卡片中的缓存
    cards = load_review_cards()
    if card_id in cards:
        cards[card_id]["export_markdown"] = md_content
        save_review_cards(cards)

    return md_content


# ============================================================
# 辅助：获取可用行程列表
# ============================================================

def get_available_trips(user_id: str) -> dict:
    """
    返回用户可以生成卡片的已完成行程 + 已生成卡片的行程。
    """
    from services.trip_guardian_service import trip_guardian_service

    all_trips = trip_guardian_service._trips
    existing_cards = load_review_cards()
    existing_trip_ids = {c["trip_id"] for c in existing_cards.values()}

    available = []
    generated = []

    for trip in all_trips.values():
        trip_data = {
            "trip_id": trip.trip_id,
            "destination": trip.destination,
            "start_date": trip.start_date,
            "end_date": trip.end_date,
            "duration_days": len(trip.days_plan),
            "status": trip.status,
            "guardian_phase": trip.guardian_phase
        }

        if trip.trip_id in existing_trip_ids:
            # 找到对应的卡片
            for card in existing_cards.values():
                if card.get("trip_id") == trip.trip_id and card.get("user_id") == user_id:
                    generated.append({
                        "card_id": card["card_id"],
                        "trip_id": trip.trip_id,
                        "destination": card["destination"],
                        "date_range": card["date_range"],
                        "generated_at": card["generated_at"],
                        "overall_rating": card.get("ratings", {}).get("overall", 0)
                    })
                    break
        else:
            available.append(trip_data)

    return {
        "available_trips": available,
        "generated_cards": generated
    }
