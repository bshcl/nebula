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
