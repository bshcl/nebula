# check_models.py
import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

print("🚀 正在从东京连接 Google AI 目录...")

try:
    # 单词：List [lɪst] 列表。
    # 作用：获取当前 Key 支持的所有模型
    for m in genai.list_models():
        if "generateContent" in m.supported_generation_methods:
            print(f"✅ 可用模型: {m.name}")
except Exception as e:
    print(f"❌ 探测失败，请检查 API Key 是否正确: {e}")
