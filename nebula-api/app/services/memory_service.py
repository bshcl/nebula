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
