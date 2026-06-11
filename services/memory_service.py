import json
import os

# 使用项目根目录的绝对路径，确保在任何目录下运行都能找到数据文件
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MEMORY_FILE = os.path.join(PROJECT_ROOT, "memory.json")


# 保存记忆
def save_memory(new_memory):

    memory = load_memory()

    memory.update(new_memory)

    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(memory, f, ensure_ascii=False, indent=4)


# 读取记忆
def load_memory():

    if not os.path.exists(MEMORY_FILE):
        return {}

    with open(MEMORY_FILE, "r", encoding="utf-8") as f:
        return json.load(f)