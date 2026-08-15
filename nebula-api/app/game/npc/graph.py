import re

from langchain_core.messages import AIMessage, BaseMessage, SystemMessage
from langgraph.graph import END, START, StateGraph

from app.agentkit.observability import get_trace
from app.config import get_logger, settings
from app.game.npc.agents import local_llm, soul_llm_cloud
from app.game.npc.prompts import SENTIMENT_ANALYZER_PROMPT, SOUL_MANAGER_PROMPT
from app.game.npc.routing import post_analyzer_router
from app.game.npc.state import CombinedState

logger = get_logger(__name__)

WORLD_REPORT_PREFIX = "[World Observer Report]:"


async def call_world_agent(state: CombinedState) -> dict[str, list[BaseMessage]]:
    """Invoke the cloud World Observer agent with graceful degradation."""
    from app.game.npc.agents import world_agent_cloud

    logger.debug("Entering World node (cloud path)")

    if world_agent_cloud is None:
        trace = get_trace()
        if trace:
            trace.mark_fallback("world_agent_unavailable")
        return {
            "messages": [
                AIMessage(content="System warning: World perception module is not running.")
            ]
        }

    try:
        result = await world_agent_cloud.ainvoke(state)
        last_msg = result["messages"][-1]
        last_msg.content = f"{WORLD_REPORT_PREFIX} {last_msg.content}"
        return {"messages": [last_msg]}
    except Exception as exc:
        logger.info("World node cloud fallback triggered: %s", exc)
        trace = get_trace()
        if trace:
            trace.mark_fallback("world_cloud")
        return {
            "messages": [
                AIMessage(
                    content=(
                        f"{WORLD_REPORT_PREFIX} "
                        "Unable to fetch geographic data due to network issues."
                    )
                )
            ]
        }


async def call_soul_agent(state: CombinedState) -> dict[str, list[BaseMessage]]:
    """Invoke the cloud Soul agent, falling back to local Ollama on failure."""
    from app.game.npc.agents import soul_agent

    logger.debug("Entering Soul node")

    clean_history: list[BaseMessage] = []
    world_report = "No geographic intelligence available."
    for message in state["messages"]:
        if WORLD_REPORT_PREFIX in str(message.content):
            world_report = str(message.content)
        else:
            clean_history.append(message)

    try:
        result = await soul_agent.ainvoke(state)
        return {"messages": result["messages"]}
    except Exception as exc:
        logger.info("Soul node cloud fallback — switching to local Ollama: %s", exc)
        trace = get_trace()
        if trace:
            trace.mark_fallback("soul_local_ollama")
        offline_instruction = SOUL_MANAGER_PROMPT.format(
            mood=state["mood"], summary=state.get("summary", "")
        )
        offline_instruction += f"\n\n### Live World Intel ###\n{world_report}"
        offline_instruction += (
            "\n\nNote: You are in [OFFLINE WEAK MODE]. "
            "Append [[SYSTEM:OFFLINE]] at the end of your reply."
        )

        messages = [SystemMessage(content=offline_instruction)] + clean_history
        response = await local_llm.ainvoke(messages)

        if "[[SYSTEM:OFFLINE]]" not in str(response.content):
            response.content = f"{response.content} [[SYSTEM:OFFLINE]]"

        return {"messages": [response]}


def analyze_sentiment(state: CombinedState) -> dict[str, int]:
    """Analyze user sentiment and update NPC mood (cloud-first, silent fallback)."""
    user_input = state["messages"][-1].content
    formatted_prompt = SENTIMENT_ANALYZER_PROMPT.format(user_input=user_input)

    try:
        res = soul_llm_cloud.invoke(formatted_prompt)
        content_text = (
            res.content
            if isinstance(res.content, str)
            else "".join(part.get("text", "") for part in res.content if isinstance(part, dict))
        )
        numbers = re.findall(r"-?\d+", content_text)
        score = int(numbers[0]) if numbers else 0
    except Exception as exc:
        logger.info("Sentiment analyzer fallback — mood unchanged: %s", exc)
        score = 0
        trace = get_trace()
        if trace:
            trace.mark_fallback("sentiment_analyzer")
    new_mood = max(
        settings.MOOD_MIN,
        min(settings.MOOD_MAX, state["mood"] + score),
    )
    logger.debug("Mood shift: %s -> %s", state["mood"], new_mood)
    return {"mood": new_mood}


def npc_angry(state: CombinedState) -> dict[str, list[AIMessage]]:
    """Return an in-character refusal when mood is below the angry threshold."""
    return {
        "messages": [
            AIMessage(content=("（NPC glares at you）I'm in a terrible mood — leave me alone!"))
        ]
    }


builder = StateGraph(CombinedState)

builder.add_node("analyzer", analyze_sentiment)
builder.add_node("world_node", call_world_agent)
builder.add_node("soul_node", call_soul_agent)
builder.add_node("angry_node", npc_angry)

builder.add_edge(START, "analyzer")
builder.add_conditional_edges(
    "analyzer",
    post_analyzer_router,
    {"angry": "angry_node", "world": "world_node", "soul": "soul_node"},
)
builder.add_edge("angry_node", END)
builder.add_edge("world_node", "soul_node")
builder.add_edge("soul_node", END)

npc_brain = builder.compile()
