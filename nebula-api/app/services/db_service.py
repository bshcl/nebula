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
