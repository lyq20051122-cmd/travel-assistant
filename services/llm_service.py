from openai import OpenAI

from config import OPENAI_API_KEY
from config import OPENAI_BASE_URL

client = OpenAI(
    api_key=OPENAI_API_KEY,
    base_url=OPENAI_BASE_URL
)

def ask_llm(message):

    try:

        response = client.chat.completions.create(

            model="deepseek-chat",

            messages=[
                {
                    "role": "system",
                    "content": "你是旅游计划生成助手"
                },
                {
                    "role": "user",
                    "content": message
                }
            ],

            temperature=0.7
        )

        return response.choices[0].message.content

    except Exception as e:

        print("大模型调用失败：", e)

        return f"大模型调用失败：{str(e)}"