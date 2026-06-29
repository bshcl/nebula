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
