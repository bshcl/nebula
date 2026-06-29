import os
from dotenv import load_dotenv

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from langchain_ollama import ChatOllama
from langgraph.prebuilt import create_react_agent

from app.models.combined_state import CombinedState
from app.core.prompts import WORLD_OBSERVER_PROMPT, SOUL_MANAGER_PROMPT
from app.chains.tools import (
    MapTools,
    InteractionTools,
    EnvironmentTools,
    WorldKnowledgeTools,
)

load_dotenv()
GOOGLE_KEY = os.getenv("GOOGLE_API_KEY")
GROQ_KEY = os.getenv("GROQ_API_KEY")

# ==========================================
# 1. 定义底层模型 (LLMs)
# ==========================================


# 云端逻辑链：Gemini 报错时自动切换到 Groq
def create_cloud_llm(model_name, temperature=0):
    primary = ChatGoogleGenerativeAI(
        model=model_name, google_api_key=GOOGLE_KEY, temperature=temperature
    )
    backup = ChatGroq(
        model="llama-3.1-70b-versatile", groq_api_key=GROQ_KEY, temperature=temperature
    )
    return primary.with_fallbacks([backup])


world_llm_cloud = create_cloud_llm("gemini-3.5-flash", temperature=0)
soul_llm_cloud = create_cloud_llm("gemini-3.1-flash-lite", temperature=0.7)

# 本地保底模型 (Ollama) - 纯净模型，不绑定工具以保证绝对稳定
local_llm = ChatOllama(model="llama3.2", temperature=0)

# ==========================================
# 2. 定义工具集
# ==========================================
SOUL_TOOLS = [InteractionTools.send_gift]
WORLD_TOOLS = [
    MapTools.search_nearby_places,
    MapTools.get_place_details,
    EnvironmentTools.get_weather_mock,
    WorldKnowledgeTools.query_nebula_lore,
]

# ==========================================
# 3. 实例化云端 Agent (作为主路径)
# ==========================================

# 灵魂管理者云端版
soul_agent_cloud = create_react_agent(
    model=soul_llm_cloud,
    tools=SOUL_TOOLS,
    state_schema=CombinedState,
    name="soul_manager_cloud",
    prompt=SOUL_MANAGER_PROMPT,
)

# 世界观察员云端版 (动态初始化)
world_agent_cloud = None


def initialize_world_agent():
    global world_agent_cloud
    world_agent_cloud = create_react_agent(
        model=world_llm_cloud,
        tools=WORLD_TOOLS,
        state_schema=CombinedState,
        name="environment_data_cloud",
        prompt=WORLD_OBSERVER_PROMPT,
    )
    print("🧠 [Nebula] 云端 World Agent 已就绪。")
