from openai import OpenAI
from app.core.prompts import generate_system_prompt
from app.models.schemas import ChatRequest, ChatResponse, ChatMessage
from app.services import db_service


client = OpenAI(api_key="ollama", base_url="http://localhost:11434/v1")


def get_llm_stream(db, payload):
    system_prompt = generate_system_prompt(payload.bot_name, payload.bot_personality)
    messages = [{"role": "system", "content": system_prompt}] + [
        msg.model_dump() for msg in payload.history
    ]
    messages.append({"role": "user", "content": payload.message})

    # 这里我们不再等待AI生成完整回复后才返回，而是直接将流式响应返回给前端，这样前端就可以在AI生成回复的过程中，实时地显示内容，提升用户体验。
    full_reply = ""

    response = client.chat.completions.create(
        model="deepseek-r1:8b", messages=messages, stream=True
    )

    for chunk in response:
        if chunk.choices[0].delta.content:
            content = chunk.choices[0].delta.content
            full_reply += content
            yield content

    db_service.upsert_chat_session(
        db,
        payload.session_id,
        payload.bot_name,
        payload.bot_personality,
        payload.history
        + [
            {"role": "user", "content": payload.message},
            {"role": "assistant", "content": full_reply},
        ],
    )
