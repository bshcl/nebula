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
