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
