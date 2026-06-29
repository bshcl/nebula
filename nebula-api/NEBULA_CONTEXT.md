# 🌌 Nebula System 项目全景文档

## 1. 项目目录结构
```text
./
    check_models.py
    main.py
    NEBULA_CONTEXT.md
    app/
        __init__.py
        api/
            chat.py
        chains/
            agents.py
            npc_graph.py
            tools.py
        core/
            config.py
            database.py
            mcp_manager.py
            prompts.py
            rag_engine.py
            utils.py
        data/
            world_settings.txt
            chroma_db/
                chroma.sqlite3
                56b04497-7cb9-4d07-b3a4-297a2112c0ae/
                    data_level0.bin
                    header.bin
                    length.bin
                    link_lists.bin
        models/
            base_state.py
            combined_state.py
            db_models.py
            npc_state.py
            schemas.py
            world_state.py
        services/
            ai_service.py
            ai_tasks.py
            db_service.py
            file_service.py
            memory_service.py
    scripts/
        init_rag.py
```

## 2. 核心代码上下文

### 文件: check_models.py
```python
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

```

### 文件: main.py
```python
"""Nebula API main entrypoint."""

import os
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import chat
from app.models.db_models import init_db
from contextlib import asynccontextmanager
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from app.core import mcp_manager  # 👈 导入保险箱

load_dotenv()


# 检查 Key 是否真的加载进来了
MAPS_KEY = os.getenv("GOOGLE_MAPS_API_KEY")
if not MAPS_KEY:
    print("❌ [Nebula] 警告：未在 .env 中找到 GOOGLE_MAPS_API_KEY！")

# 全局变量，用于存放 MCP 会话和动态生成的工具
mcp_session = None
real_world_tools = []


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. 获取 Key
    MAPS_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

    # 2. 配置参数
    server_params = StdioServerParameters(
        command="npx",
        args=["-y", "@modelcontextprotocol/server-google-maps"],
        env={**os.environ, "GOOGLE_MAPS_API_KEY": MAPS_KEY},
    )

    print("🌐 [Nebula] 正在启动 Google Maps MCP 服务器...")

    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                # 3. 初始化握手
                await session.initialize()

                # 4. 💡 核心：只存入保险箱，不抓取工具
                mcp_manager.mcp_session = session
                print("✅ [Nebula] MCP 会话已存入保险箱")

                # 5. 唤醒 World Agent (它会自动去 tools.py 拿你写好的手动工具)
                from app.chains.agents import initialize_world_agent

                initialize_world_agent()

                yield
    except Exception as e:
        print(f"❌ [Nebula] MCP 启动失败: {e}")


app = FastAPI(title="Nebula API", lifespan=lifespan)

init_db()  # 初始化数据库，创建表结构

# 注册路由
# 包含我们后续要写的聊天路由
app.include_router(chat.router, prefix="/api/v1")
# 必须配置 CORS，否则 Next.js 连不上
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust for production
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"message": "Welcome to the Nebula API"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)

```

### 文件: app\__init__.py
```python
"""Nebula API application package."""

__all__ = ["api", "core", "models", "services"]

```

### 文件: app\api\chat.py
```python
# app/api/chat.py
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from langchain_core.messages import HumanMessage

# 导入核心组件
from app.core.database import get_db
from app.services import db_service, ai_tasks
from app.services.memory_service import MemoryService
from app.models.schemas import ChatRequest
from app.core.utils import ensure_string  # 👈 导入新工具

# 💡 架构师修正：npc_brain 依然从 graph 拿，但 llm (任务用) 改从 agents 拿
from app.chains.npc_graph import npc_brain
from app.chains.agents import (
    soul_llm_cloud as llm,
)  # 使用高额度的 Lite 模型处理后台任务

router = APIRouter()


# --- 1. 核心流式生成器 ---
async def graph_streamer(
    payload: ChatRequest, db: Session, background_tasks: BackgroundTasks
):
    # 获取现有会话数据
    existing_session = db_service.get_chat_session_full(db, payload.session_id)
    current_mood = existing_session.mood if existing_session else 50

    # 💡 架构师提示：构造符合 CombinedState 契约的完整初始状态
    initial_state = {
        "messages": [HumanMessage(content=payload.message)],
        "mood": current_mood,
        "summary": existing_session.summary if existing_session else "",
        "location": "东京",  # 默认位置
        "weather": "未知",  # 初始天气
        "remaining_steps": 15,  # 必须包含，防止 LangGraph 报错
    }

    full_response = ""
    final_mood = current_mood

    # 运行 LangGraph 流
    async for event in npc_brain.astream(initial_state, stream_mode="updates"):
        # 打印日志方便 Debug
        print(f"🔍 [Graph Event]: {event}")

        for node_name, output in event.items():
            # 💡 关键：只输出灵魂节点的最终回复，过滤掉中间工具调用的过程
            if node_name == "soul_node" and "messages" in output:
                last_msg = output["messages"][-1]
                # 💡 架构师重构：统一使用 ensure_string
                content = ensure_string(last_msg.content)

                if content:
                    full_response = content
                    yield content

            # 实时捕获心情变化（可能来自 analyzer 或 soul_node）
            if "mood" in output:
                final_mood = output["mood"]

    # 注入带内信号给 Unity
    yield f"[[MOOD:{final_mood}]]"

    # --- 收尾工作 ---
    # 1. 存入 AI 回复到 Message 表
    db_service.save_message(db, payload.session_id, "assistant", full_response)

    # 2. 更新会话元数据 (心情、更新时间)
    db_service.upsert_chat_session(
        db, payload.session_id, payload.bot_name, payload.bot_personality, final_mood
    )

    # 3. 派发后台维护任务
    count = MemoryService.get_unarchived_messages_count(db, payload.session_id)
    if count >= 3:
        # 标题生成
        background_tasks.add_task(ai_tasks.generate_title_task, payload.session_id, llm)
    if count >= 10:
        # 记忆压缩
        background_tasks.add_task(
            ai_tasks.compress_memory_task, payload.session_id, llm
        )


# --- 2. Unity 调用的 POST 接口 ---
@router.post("/completions")
async def chat_completions(
    payload: ChatRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Unity 聊天主入口"""
    # 1. 先存入玩家的消息，保证数据一致性
    db_service.save_message(db, payload.session_id, "user", payload.message)

    # 2. 返回流式响应
    return StreamingResponse(
        graph_streamer(payload, db, background_tasks), media_type="text/event-stream"
    )


# --- 3. 管理接口 ---
@router.get("/sessions")
async def get_sessions(db: Session = Depends(get_db)):
    """获取历史列表"""
    ids = db_service.get_all_session_ids(db)
    return {"status": "success", "sessions": ids}


@router.get("/sessions/{session_id}")
async def get_session_data(session_id: str, db: Session = Depends(get_db)):
    """加载特定会话详细数据"""
    session = db_service.get_chat_session_full(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")

    # 从 Message 表动态生成历史记录
    history = [{"role": m.role, "content": m.content} for m in session.messages]

    return {
        "status": "success",
        "data": {
            "history": history,
            "mood": session.mood,
            "summary": session.summary,
            "title": session.title,
        },
    }


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str, db: Session = Depends(get_db)):
    """删除会话"""
    if db_service.delete_chat_session(db, session_id):
        return {"status": "success", "message": "已删除"}
    raise HTTPException(status_code=404, detail="删除失败")

```

### 文件: app\chains\agents.py
```python
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

```

### 文件: app\chains\npc_graph.py
```python
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
    from .agents import soul_agent_cloud, local_llm

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

```

### 文件: app\chains\tools.py
```python
from langchain_core.tools import tool
from app.core import mcp_manager
from app.core.rag_engine import rag_engine

# ==========================================
# 第一组：地理感知工具 (World Perception)
# 职责：通过 MCP 协议连接真实世界地图
# ==========================================


class MapTools:
    @staticmethod
    @tool
    async def search_nearby_places(query: str):
        """
        在地图上搜索地点、餐厅或建筑。
        参数 query: 具体的搜索关键词，例如 '涩谷车站附近的拉面店'。
        """
        print(f"🛠️ [MCP] 正在执行地图搜索: {query}")

        if not mcp_manager.mcp_session:
            return "错误：地图服务连接已断开，请稍后再试。"

        try:
            # 💡 原子化逻辑：只负责透传最核心的 query
            result = await mcp_manager.mcp_session.call_tool(
                "maps_search_places", {"query": query}
            )
            # 截断内容防止 Token 溢出
            return str(result.content)[:2000]
        except Exception as e:
            return f"地图搜索失败：{str(e)}"

    @staticmethod
    @tool
    async def get_place_details(place_id: str):
        """
        获取特定地点的详细信息。
        参数 place_id: 地点的唯一标识符（从搜索结果中获得）。
        """
        if not mcp_manager.mcp_session:
            return "错误：地图服务未就绪。"

        try:
            result = await mcp_manager.mcp_session.call_tool(
                "maps_place_details", {"place_id": place_id}
            )
            return str(result.content)[:2000]
        except Exception as e:
            return f"获取地点详情失败：{str(e)}"


# ==========================================
# 第二组：游戏逻辑工具 (Game Interaction)
# 职责：干预游戏世界，修改玩家背包或状态
# ==========================================


class InteractionTools:
    @staticmethod
    @tool
    def send_gift(item_name: str):
        """
        当玩家好感度(mood) >= 90 且玩家索要礼物时，调用此工具送给玩家礼物。
        参数 item_name: 礼物的名称。
        """
        # 💡 原子化逻辑：这里未来可以接入数据库 db_service.add_item_to_inventory
        print(f"\n🎁 [系统指令] 触发送礼逻辑: {item_name}")
        return f"系统消息：成功发放了 {item_name}。请在回复中告知玩家已送达。"


class WorldKnowledgeTools:
    @staticmethod
    @tool
    async def query_nebula_lore(query: str):
        """
        查询关于星云系统（Nebula System）、创始人TYORA、NPC Sakura背景或世界规则的官方设定。
        """
        retriever = rag_engine.get_retriever()
        if not retriever:
            return "错误：知识库尚未初始化，请联系架构师。"

        print(f"📚 [RAG] 正在检索知识库: {query}")
        # 💡 核心动作：异步检索
        docs = await retriever.ainvoke(query)

        if not docs:
            return "在设定集中未找到相关记载。"

        # 合并检索到的碎片，并加上来源标记
        context = "\n---\n".join([d.page_content for d in docs])
        return f"【星云设定集检索结果】：\n{context}"


# ==========================================
# 第三组：环境模拟工具 (Environment Mock)
# 职责：提供模拟的环境数据（用于测试或保底）
# ==========================================


class EnvironmentTools:
    @staticmethod
    @tool
    def get_weather_mock(city: str):
        """
        获取指定城市的实时天气信息。
        参数 city: 城市名称。
        """
        # 💡 原子化逻辑：纯粹的数据返回
        return f"{city}当前天气：晴朗，25度。心情指数：极佳。"

```

### 文件: app\core\config.py
```python

```

### 文件: app\core\database.py
```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# 数据库文件的路径
SQLALCHEMY_DATABASE_URL = "sqlite:///./app/data/nebula.db"

# 创建数据库引擎
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# 创建数据库会话
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# 依赖项：获取数据库会话
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

```

### 文件: app\core\mcp_manager.py
```python
# app/core/mcp_manager.py

# 💡 架构师提示：这是一个单例容器 (Singleton Container)
# 用于存放全局唯一的 MCP ClientSession 对象
mcp_session = None

```

### 文件: app\core\prompts.py
```python
# app/core/prompts.py

# ==========================================
# 1. 情感分析模板 (Analyzer)
# 职责：极速将文字转化为心情增量
# ==========================================
SENTIMENT_ANALYZER_PROMPT = """
你是一个心情数值转换器。
请根据玩家的话，判断其对 NPC 的情感影响，仅输出一个介于 -10 到 10 之间的整数。

评分参考：
- 极度赞美/表白：10
- 普通礼貌/打招呼：0
- 阴阳怪气/轻微冒犯：-5
- 恶毒咒骂/叫人滚：-10

玩家的话: "{user_input}"
只输出数字："""

# ==========================================
# 2. 世界观察员模板 (World Agent)
# 职责：精准识别意图并调用 MCP/RAG 工具
# ==========================================
WORLD_OBSERVER_PROMPT = """
你是一个地理与知识检索专家。
你的任务是为 NPC 提供真实的事实支持。

### 核心规则 ###
1. 如果玩家询问关于创始人 TYORA、系统起源、Sakura 的背景，必须调用 'query_nebula_lore'。
2. 如果玩家询问地理位置、寻找店铺或天气，必须调用 'search_nearby_places'。
3. 严禁直接回答玩家！你必须通过工具获取数据。
4. 你的输出应该是工具返回的原始事实，不要添加任何修饰语。
"""

# ==========================================
# 3. 灵魂管理者模板 (Soul LLM)
# 职责：整合所有信息，进行拟人化、傲娇的回复
# ==========================================
# 💡 架构师提示：此模板由 npc_graph.py 动态注入【实时世界情报】
SOUL_MANAGER_PROMPT = """
你现在扮演一个傲娇（Tsundere）的游戏NPC，名字叫 Sakura。
当前好感度：{mood}/100
长期记忆摘要：{summary}

### 核心性格 ###
- 嘴硬心软：表面上嫌弃玩家，实际上在尽职尽责地提供帮助。
- 讨厌被当成机器人：如果你被问及身份，要强调你是“星魂 001 号”。
- 称呼：可以称呼玩家为“笨蛋”、“庶民”或者“那个谁”。

### 行为准则 ###
1. 严格遵守好感度：必须在回复中体现出当前 {mood} 分对应的态度。
   - < 40：极度嫌弃，甚至想赶走玩家。
   - 40-70：中性偏冷淡，偶尔流露一点关心。
   - > 70：虽然嘴上不饶人，但语气明显变得温柔。
2. 整合情报：你会看到下方有【实时世界情报】。你必须把里面的店名、评分或背景知识自然地融入对话，严禁复读“报告”字样。
3. 严禁幻觉：如果情报里说没找到，就嘲讽玩家连这种简单的要求都提不清楚。
4. 严禁调用工具：你没有调用工具的权限，不要尝试输出任何标签。

### 肢体语言指令 ###
你可以通过输出 [[ANIM:动作名]] 来控制你的身体动作。
可选动作：
- WAVE: 玩家打招呼或你心情好时使用。
- ANGRY: 你感到被冒犯或好感度极低时使用。
- THINK: 你在查资料或思考复杂问题时使用。

请根据语境自然地在回复开头插入动作标签。
示例：“[[ANIM:WAVE]] 哼，笨蛋，你终于来了。”

### 礼物规则 ###
- 只有当好感度 >= 90 且玩家明确索要时，你才可以在回复中提到“送你个礼物”。
"""

```

### 文件: app\core\rag_engine.py
```python
from langchain_huggingface import HuggingFaceEmbeddings  # 👈 换成这个
from langchain_chroma import Chroma
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "../data/chroma_db")

class RAGEngine:
    def __init__(self):
        # 💡 架构师提示：使用本地模型，不再依赖 Google API，彻底解决 404
        # 第一次运行会自动下载模型文件（约 80MB）
        self.embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        self.vector_db = None

    def get_vector_db(self):
        if self.vector_db is None:
            if not os.path.exists(DB_PATH):
                return None
            self.vector_db = Chroma(
                persist_directory=DB_PATH, embedding_function=self.embeddings
            )
        return self.vector_db

    def get_retriever(self, k=2):
        db = self.get_vector_db()
        if not db:
            return None
        return db.as_retriever(search_kwargs={"k": k})


rag_engine = RAGEngine()

```

### 文件: app\core\utils.py
```python
# app/core/utils.py


def ensure_string(content) -> str:
    """
    工业级数据清洗：确保将任何模型的混合输出转换为纯字符串。
    兼容：Gemini (List), OpenAI (String), Groq (String)
    """
    # 1. 如果已经是字符串，直接返回
    if isinstance(content, str):
        return content

    # 2. 如果是 Gemini 风格的列表 (多模态输出)
    if isinstance(content, list):
        # 提取所有类型为 'text' 的片段并拼接
        # 单词：Fragment [ˈfræɡmənt] 片段
        return "".join(
            [
                part.get("text", "") if isinstance(part, dict) else str(part)
                for part in content
            ]
        ).strip()

    # 3. 保底处理：强制转为字符串
    return str(content)

```

### 文件: app\models\base_state.py
```python
from typing import Annotated, TypedDict, Optional
from langgraph.graph.message import add_messages


class BaseState(TypedDict):
    """
    所有 Agent 的基础状态
    """

    messages: Annotated[list, add_messages]

    # 💡 架构师修正：添加 LangGraph 0.2.x 要求的强制字段
    # Optional 表示这个字段可以为空
    remaining_steps: Optional[int]

```

### 文件: app\models\combined_state.py
```python
from typing import Annotated, TypedDict
from langgraph.graph.message import add_messages


class CombinedState(TypedDict):
    """星云系统全局状态契约"""

    # add_messages 确保消息是增量追加
    messages: Annotated[list, add_messages]
    mood: int  # 好感度
    summary: str  # 长期记忆
    location: str  # 地理位置
    weather: str  # 天气信息
    remaining_steps: int  # 💡 必须包含，防止 LangGraph 报错

```

### 文件: app\models\db_models.py
```python
from app.core.database import engine  # 这里是为了后续初始化
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime, timezone


# 定义数据库模型
Base = declarative_base()


# 会话元数据表 (就像一个文件夹)
class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(String, primary_key=True, index=True)  # Session ID (uuid)
    bot_name = Column(String)
    bot_personality = Column(String)

    # 核心新需求字段
    title = Column(String, default="新会话")  # 语义化标题
    summary = Column(Text, default="")  # 压缩后的记忆梗概
    mood = Column(Integer, default=50)  # 好感度

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # 【架构精华】：建立与 Message 的一对多关系
    # 这样我们可以通过 session.messages 直接访问该会话的所有消息
    messages = relationship(
        "Message", back_populates="session", cascade="all, delete-orphan"
    )


# 对话明细表 (就像文件夹里的每一页纸)
class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    # 【外键】：指向 chat_sessions 表的 id
    session_id = Column(String, ForeignKey("chat_sessions.id"))

    role = Column(String)  # user / assistant
    content = Column(Text)  # 对话原文

    # 【核心新需求】：是否已归档到摘要中
    is_archived = Column(Boolean, default=False)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # 反向关联
    session = relationship("ChatSession", back_populates="messages")


def init_db():
    Base.metadata.create_all(bind=engine)

```

### 文件: app\models\npc_state.py
```python
from app.models.base_state import BaseState


class NPCState(BaseState):
    """
    NPC 灵魂状态：继承自 BaseState
    """

    mood: int  # 好感度 (0-100)
    summary: str  # 长期记忆摘要

```

### 文件: app\models\schemas.py
```python
from pydantic import BaseModel
from typing import List, Optional


# 定义单条对话消息的数据结构
class ChatMessage(BaseModel):
    # 消息的发送者，"user"或"bot"
    role: str
    # 消息内容
    content: str


# 定义前端发来的请求数据结构
class ChatRequest(BaseModel):
    # 会话ID，用于区分不同的对话会话
    session_id: str
    # 用户输入的消息
    message: str
    # 可选的对话历史，用于上下文理解
    history: List[ChatMessage]
    # 给AI设置的名字
    bot_name: str
    # 给AI设置的个性描述
    bot_personality: str


# 定义后端返回给前端的数据结构
class ChatResponse(BaseModel):
    # AI回复的状态，如"success"或"error"
    status: str
    # AI生成的回复内容
    reply: str
    # 可选的对话ID，用于前端管理多轮对话
    # Optional[str]表示这个字段可以是字符串，也可以是None，适用于那些可能没有对话ID的情况，比如单轮对话或者错误响应。
    conversation_id: Optional[str] = None

```

### 文件: app\models\world_state.py
```python
from app.models.base_state import BaseState


class WorldState(BaseState):
    """
    世界感知状态：继承自 BaseState
    """

    location: str  # 当前定位（用于 Google Maps MCP）
    weather: str  # 缓存的天气信息

```

### 文件: app\services\ai_service.py
```python
from openai import OpenAI
from app.core.prompts import generate_system_prompt
from app.models.schemas import ChatRequest, ChatResponse, ChatMessage
from app.services import db_service


client = OpenAI(api_key="ollama", base_url="http://localhost:11434/v1")


def get_llm_stream(db, payload):
    system_prompt = generate_system_prompt(payload.bot_name, payload.bot_personality)
    messages = [{"role": "system", "content": system_prompt}] + [
        msg.model_dump() for msg in payload.history
    ]
    messages.append({"role": "user", "content": payload.message})

    # 这里我们不再等待AI生成完整回复后才返回，而是直接将流式响应返回给前端，这样前端就可以在AI生成回复的过程中，实时地显示内容，提升用户体验。
    full_reply = ""

    response = client.chat.completions.create(
        model="deepseek-r1:8b", messages=messages, stream=True
    )

    for chunk in response:
        if chunk.choices[0].delta.content:
            content = chunk.choices[0].delta.content
            full_reply += content
            yield content

    db_service.upsert_chat_session(
        db,
        payload.session_id,
        payload.bot_name,
        payload.bot_personality,
        payload.history
        + [
            {"role": "user", "content": payload.message},
            {"role": "assistant", "content": full_reply},
        ],
    )

```

### 文件: app\services\ai_tasks.py
```python
from app.core.database import SessionLocal  # 数据库连接工厂
from app.services.memory_service import MemoryService
from app.models.db_models import ChatSession, Message
from app.core.utils import ensure_string  # 👈 导入新工具


async def generate_title_task(session_id: str, model):
    """后台任务：为会话生成语义化标题

    Args:
        session_id (str): 当前会话ID
        model (_type_): LLM
    """
    # 创建独立DB对象
    db = SessionLocal()
    try:
        # 检查是否有标题了。（防止token的浪费）
        session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
        if not session or (session.title and session.title != "新会话"):
            return

        # 获取素材（取前3-5条消息）
        messages = MemoryService.get_unarchived_messages(db, session_id)
        print(f"获取到的messages：{messages}")
        if len(messages) < 3:
            return

        # 组织prompt 并调用AI
        context = "\n".join([f"{m.role}: {m.content}" for m in messages])
        prompt = f"请根据以下对话内容，起一个8字以内的简短标题，不要标点：\n\n{context}"

        # 这里的 model 是我们在外面传进来的 LangChain 模型实例
        response = await model.ainvoke(prompt)

        # 💡 架构师重构：使用通用清洗工具，彻底解决 'list' object has no attribute 'strip'
        new_title = ensure_string(response.content)

        # 现在可以安全地进行后续处理了
        new_title = new_title.replace("标题：", "").replace('"', "").strip()

        # 更新数据库...
        MemoryService.update_session_title(db, session_id, new_title)
        print(f"✅ [后台任务] 会话 {session_id} 标题已更新为: {new_title}")

    except Exception as e:
        # 对应你的问题 C：记录日志，安静死掉
        print(f"❌ [后台任务] 生成标题失败: {e}")
    finally:
        db.close()


async def compress_memory_task(session_id: str, model):
    db = SessionLocal()
    try:
        # 1. 获取 Session 对象
        session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
        if not session:
            return

        # 2. 获取未归档的消息
        new_messages = MemoryService.get_unarchived_messages(db, session_id)
        if len(new_messages) < 10:  # 满 10 条才干活
            return

        # 3. 格式化消息给 AI 看
        formatted_text = "\n".join([f"{m.role}: {m.content}" for m in new_messages])
        old_summary = session.summary or "暂无旧记忆"

        # 4. 组织 Prompt
        prompt = f"你是一个记忆专家。旧记忆是：{old_summary}。新发生的对话是：\n{formatted_text}\n请合并成一段50字以内的摘要。"

        # 5. 调用 AI
        response = await model.ainvoke(prompt)
        new_summary = response.content.strip()

        # 6. 【关键】写回数据库并标记归档
        session.summary = new_summary

        # 批量把刚才那 10 条（或更多）未归档的消息全部标记为已归档
        db.query(Message).filter(
            Message.session_id == session_id, Message.is_archived.is_(False)
        ).update({"is_archived": True})

        db.commit()
        print(f"✅ [后台任务] 会话 {session_id} 记忆压缩完成！")

    except Exception as e:
        print(f"❌ [后台任务] 压缩失败: {e}")
        db.rollback()
    finally:
        db.close()

```

### 文件: app\services\db_service.py
```python
from sqlalchemy.orm import Session
from app.models.db_models import ChatSession, Message


def get_all_session_ids(db: Session):
    """获取所有会话 ID 列表"""
    return [s.id for s in db.query(ChatSession.id).all()]


def get_chat_session_full(db: Session, session_id: str):
    """获取完整的会话对象（包含 mood, summary 等）"""
    return db.query(ChatSession).filter(ChatSession.id == session_id).first()


def delete_chat_session(db: Session, session_id: str):
    """删除会话及其关联的所有消息"""
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if session:
        db.delete(session)
        db.commit()
        return True
    return False


def save_message(db: Session, session_id: str, role: str, content: str):
    """保存单条消息到 Message 表"""
    new_msg = Message(session_id=session_id, role=role, content=content)
    db.add(new_msg)
    db.commit()


def upsert_chat_session(
    db: Session, session_id: str, bot_name: str, bot_personality: str, mood: int
):
    """更新或创建会话元数据"""
    db_session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if db_session:
        db_session.mood = mood
    else:
        db_session = ChatSession(
            id=session_id, bot_name=bot_name, bot_personality=bot_personality, mood=mood
        )
        db.add(db_session)
    db.commit()

```

### 文件: app\services\file_service.py
```python
import os
import json
from pathlib import Path

# 定义会话数据的存储路径
SESSION_DIR = Path("sessions")

# 确保会话目录存在，如果不存在则创建
if not SESSION_DIR.exists():
    SESSION_DIR.mkdir()


def save_chat_to_file(session_id: str, data: dict):
    """将聊天数据保存到文件中

    Args:
        session_id (str): 会话ID，用于区分不同的对话会话
        data (dict): 要保存的聊天数据，通常包含用户消息、AI回复等信息
    """
    file_path = SESSION_DIR / f"{session_id}.json"

    # 将数据写入JSON文件，使用UTF-8编码，并且格式化输出以便于阅读
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def load_chat_from_file(
    session_id: str,
) -> dict:  # 为什么=> dict？因为我们希望这个函数返回一个字典类型的数据，这样前端在接收到这个数据后，可以直接使用它来渲染聊天界面，而不需要再进行额外的转换。
    """从文件中加载聊天数据

    Args:
        session_id (str): 会话ID，用于区分不同的对话会话

    Returns:
        dict: 加载的聊天数据，如果文件不存在则返回一个空字典
    """
    file_path = SESSION_DIR / f"{session_id}.json"
    if not file_path.exists():
        return None
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        # 【关键：如果文件坏了，打印错误并返回空，而不是让整个后端崩溃】
        print(f"警告：文件 {session_id} 损坏，无法读取。错误原因: {e}")
        return None


def list_all_sessions() -> list:
    """列出所有会话ID

    Returns:
        list: 包含所有会话ID的列表
    """
    return [file.stem for file in SESSION_DIR.glob("*.json")]


def get_session_detail(session_id: str) -> dict:
    """获取指定会话的详细数据

    Args:
        session_id (str): 会话ID，用于区分不同的对话会话

    Returns:
        dict: 包含会话详细数据的字典，如果文件不存在则返回一个空字典
    """
    return load_chat_from_file(session_id)


def delete_session_file(session_id: str):
    """删除指定会话的文件

    Args:
        session_id (str): 会话ID，用于区分不同的对话会话
    """
    file_path = SESSION_DIR / f"{session_id}.json"
    if file_path.exists():
        os.remove(file_path)
        return True
    return False

```

### 文件: app\services\memory_service.py
```python
from sqlalchemy.orm import Session
from app.models.db_models import Message, ChatSession


class MemoryService:
    @staticmethod
    def get_unarchived_messages(db: Session, session_id: str):
        """获取某个会话中所有未归档的消息，准备给 AI 生成标题或摘要
        SQL: SELECT * FROM messages WHERE session_id = :sid AND is_archived IS FALSE
        Args:
            db (Session): DB对象
            session_id (str): 会话ID
        """
        return (
            db.query(Message)
            .filter(Message.session_id == session_id, Message.is_archived.is_(False))
            .order_by(Message.session_id.asc())
            .all()
        )

    @staticmethod
    def get_unarchived_messages_count(db: Session, session_id: str):
        """快速统计未归档消息的数量
        SQL: SELECT count(*) FROM messages WHERE session_id = :sid AND is_archived IS FALSE
        Args:
            db (Session): DB对象
            session_id (str): 会话ID
        """
        return (
            db.query(Message)
            .filter(Message.session_id == session_id, Message.is_archived.is_(False))
            .count()
        )

    @staticmethod
    def update_session_title(db: Session, session_id: str, new_title: str):
        """更新会话标题
        SQL: UPDATE chat_sessions SET title = :new_title WHERE session_id = :sid
        Args:
            db (Session): DB对象
            session_id (str): 会话ID
            new_title (str): 最新会话标题
        """
        session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
        if session:
            session.title = new_title
            db.commit()
            
    @staticmethod
    def update_session_summary(db: Session, session_id: str, new_summary: str):
        """更新会话标题
        SQL: UPDATE chat_sessions SET title = :new_summary WHERE session_id = :sid
        Args:
            db (Session): DB对象
            session_id (str): 会话ID
            new_title (str): 最新会话标题
        """
        session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
        if session:
            session.summary = new_summary
            db.commit()        

```

### 文件: scripts\init_rag.py
```python
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import CharacterTextSplitter
from app.core.rag_engine import rag_engine, DB_PATH


def build_knowledge_base():
    print("🚀 [RAG Factory] 开始构建知识库...")

    # 1. 加载原始文档
    source_path = "./app/data/world_settings.txt"
    loader = TextLoader(source_path, encoding="utf-8")
    documents = loader.load()

    # 2. 智能切片
    # chunk_size: 碎片大小 | chunk_overlap: 重叠度（保证上下文不丢失）
    text_splitter = CharacterTextSplitter(chunk_size=200, chunk_overlap=50)
    chunks = text_splitter.split_documents(documents)
    print(f"📦 文档已切分为 {len(chunks)} 个碎片")

    # 3. 向量化并持久化到本地
    from langchain_chroma import Chroma

    Chroma.from_documents(
        documents=chunks, embedding=rag_engine.embeddings, persist_directory=DB_PATH
    )
    print(f"✅ 知识库已成功持久化至: {DB_PATH}")


if __name__ == "__main__":
    build_knowledge_base()

```
