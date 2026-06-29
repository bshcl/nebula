from langchain_core.tools import tool
from app.core import mcp_manager
from app.core.rag_engine import rag_engine

# ==========================================
# 第一组：地理感知工具 (World Perception)
# 职责：通过 MCP 协议连接真实世界地图
# ==========================================


class MapTools:
    @staticmethod
    @tool
    async def search_nearby_places(query: str):
        """
        在地图上搜索地点、餐厅或建筑。
        参数 query: 具体的搜索关键词，例如 '涩谷车站附近的拉面店'。
        """
        print(f"🛠️ [MCP] 正在执行地图搜索: {query}")

        if not mcp_manager.mcp_session:
            return "错误：地图服务连接已断开，请稍后再试。"

        try:
            # 💡 原子化逻辑：只负责透传最核心的 query
            result = await mcp_manager.mcp_session.call_tool(
                "maps_search_places", {"query": query}
            )
            # 截断内容防止 Token 溢出
            return str(result.content)[:2000]
        except Exception as e:
            return f"地图搜索失败：{str(e)}"

    @staticmethod
    @tool
    async def get_place_details(place_id: str):
        """
        获取特定地点的详细信息。
        参数 place_id: 地点的唯一标识符（从搜索结果中获得）。
        """
        if not mcp_manager.mcp_session:
            return "错误：地图服务未就绪。"

        try:
            result = await mcp_manager.mcp_session.call_tool(
                "maps_place_details", {"place_id": place_id}
            )
            return str(result.content)[:2000]
        except Exception as e:
            return f"获取地点详情失败：{str(e)}"


# ==========================================
# 第二组：游戏逻辑工具 (Game Interaction)
# 职责：干预游戏世界，修改玩家背包或状态
# ==========================================


class InteractionTools:
    @staticmethod
    @tool
    def send_gift(item_name: str):
        """
        当玩家好感度(mood) >= 90 且玩家索要礼物时，调用此工具送给玩家礼物。
        参数 item_name: 礼物的名称。
        """
        # 💡 原子化逻辑：这里未来可以接入数据库 db_service.add_item_to_inventory
        print(f"\n🎁 [系统指令] 触发送礼逻辑: {item_name}")
        return f"系统消息：成功发放了 {item_name}。请在回复中告知玩家已送达。"


class WorldKnowledgeTools:
    @staticmethod
    @tool
    async def query_nebula_lore(query: str):
        """
        查询关于星云系统（Nebula System）、创始人TYORA、NPC Sakura背景或世界规则的官方设定。
        """
        retriever = rag_engine.get_retriever()
        if not retriever:
            return "错误：知识库尚未初始化，请联系架构师。"

        print(f"📚 [RAG] 正在检索知识库: {query}")
        # 💡 核心动作：异步检索
        docs = await retriever.ainvoke(query)

        if not docs:
            return "在设定集中未找到相关记载。"

        # 合并检索到的碎片，并加上来源标记
        context = "\n---\n".join([d.page_content for d in docs])
        return f"【星云设定集检索结果】：\n{context}"


# ==========================================
# 第三组：环境模拟工具 (Environment Mock)
# 职责：提供模拟的环境数据（用于测试或保底）
# ==========================================


class EnvironmentTools:
    @staticmethod
    @tool
    def get_weather_mock(city: str):
        """
        获取指定城市的实时天气信息。
        参数 city: 城市名称。
        """
        # 💡 原子化逻辑：纯粹的数据返回
        return f"{city}当前天气：晴朗，25度。心情指数：极佳。"
