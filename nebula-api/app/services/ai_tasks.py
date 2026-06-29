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
