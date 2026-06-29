from app.models.base_state import BaseState


class NPCState(BaseState):
    """
    NPC 灵魂状态：继承自 BaseState
    """

    mood: int  # 好感度 (0-100)
    summary: str  # 长期记忆摘要
