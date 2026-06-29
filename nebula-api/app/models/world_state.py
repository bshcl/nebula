from app.models.base_state import BaseState


class WorldState(BaseState):
    """
    世界感知状态：继承自 BaseState
    """

    location: str  # 当前定位（用于 Google Maps MCP）
    weather: str  # 缓存的天气信息
