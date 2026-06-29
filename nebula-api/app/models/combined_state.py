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
