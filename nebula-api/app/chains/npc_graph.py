import re
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import AIMessage, SystemMessage

from app.models.combined_state import CombinedState
from app.core.prompts import SENTIMENT_ANALYZER_PROMPT, SOUL_MANAGER_PROMPT
from app.chains.agents import soul_llm_cloud, local_llm


# ==========================================
# 1. 节点逻辑：带降级保护的 World Node
# ==========================================
async def call_world_agent(state: CombinedState):
    from .agents import world_agent_cloud

    print("🌍 [Debug] 正在进入 World Node (尝试云端)...")

    if world_agent_cloud is None:
        return {"messages": [AIMessage(content="【系统警告】：世界感知模块未启动。")]}

    try:
        # 尝试调用云端 Agent (Gemini/Groq)
        result = await world_agent_cloud.ainvoke(state)
        last_msg = result["messages"][-1]
        last_msg.content = f"【世界观察员报告】：{last_msg.content}"
        return {"messages": [last_msg]}
    except Exception as e:
        print(f"⚠️ [World降级] 云端感知失败: {e}")
        # 如果云端查不到地图，直接返回一个空报告，不中断程序
        return {
            "messages": [
                AIMessage(
                    content="【世界观察员报告】：由于网络波动，暂时无法获取地理信息。"
                )
            ]
        }


# ==========================================
# 2. 节点逻辑：带降级保护的 Soul Node
# ==========================================
async def call_soul_agent(state: CombinedState):
    from .agents import soul_agent_cloud

    print("🎭 [Debug] 正在进入 Soul Node...")

    # 数据清洗逻辑
    clean_history = []
    world_report = "暂无相关地理信息。"
    for m in state["messages"]:
        if "【世界观察员报告】" in m.content:
            world_report = m.content
        else:
            clean_history.append(m)

    try:
        # --- 尝试 A 路径：云端 Agent ---
        result = await soul_agent_cloud.ainvoke(state)
        return {"messages": result["messages"]}

    except Exception as e:
        # --- 尝试 B 路径：本地保底 (Ollama) ---
        print(f"🚨 [Soul降级] 云端大脑宕机，正在唤醒本地 Ollama... 错误: {e}")

        # 注入虚弱信号和离线指令
        offline_instruction = SOUL_MANAGER_PROMPT.format(
            mood=state["mood"], summary=state.get("summary", "")
        )
        offline_instruction += f"\n\n### 实时世界情报 ###\n{world_report}"
        offline_instruction += "\n\n注意：你现在处于【离线虚弱模式】，请在回复末尾务必加上 [[SYSTEM:OFFLINE]]。"

        messages = [SystemMessage(content=offline_instruction)] + clean_history

        # 调用本地模型
        response = await local_llm.ainvoke(messages)

        # 强制补丁：确保信号存在
        if "[[SYSTEM:OFFLINE]]" not in response.content:
            response.content += " [[SYSTEM:OFFLINE]]"

        return {"messages": [response]}


# ==========================================
# 3. 节点逻辑：情感分析与路由
# ==========================================
def analyze_sentiment(state: CombinedState):
    """情感分析节点：优先尝试云端，失败则默认不改变心情"""
    user_input = state["messages"][-1].content
    formatted_prompt = SENTIMENT_ANALYZER_PROMPT.format(user_input=user_input)

    try:
        res = soul_llm_cloud.invoke(formatted_prompt)
        # 处理 Gemini 可能返回的 List 类型 content
        content_text = (
            res.content
            if isinstance(res.content, str)
            else "".join(
                [p.get("text", "") for p in res.content if isinstance(p, dict)]
            )
        )
        numbers = re.findall(r"-?\d+", content_text)
        score = int(numbers[0]) if numbers else 0
    except Exception:
        print("⚠️ [Analyzer降级] 情感分析失败，保持现状。")
        score = 0

    new_mood = max(0, min(100, state["mood"] + score))
    print(f"🧠 [Analyzer] 心情变化: {state['mood']} -> {new_mood}")
    return {"mood": new_mood}


def npc_angry(state: CombinedState):
    return {
        "messages": [
            AIMessage(content="（NPC 狠狠地瞪了你一眼）我现在心情糟透了，离我远点！")
        ]
    }


def mood_router(state: CombinedState):
    return "angry" if state["mood"] < 20 else "normal"


# ==========================================
# 4. 构建工作流图
# ==========================================
builder = StateGraph(CombinedState)

builder.add_node("analyzer", analyze_sentiment)
builder.add_node("world_node", call_world_agent)
builder.add_node("soul_node", call_soul_agent)
builder.add_node("angry_node", npc_angry)

builder.add_edge(START, "analyzer")
builder.add_conditional_edges(
    "analyzer", mood_router, {"angry": "angry_node", "normal": "world_node"}
)
builder.add_edge("world_node", "soul_node")
builder.add_edge("soul_node", END)
builder.add_edge("angry_node", END)

npc_brain = builder.compile()
