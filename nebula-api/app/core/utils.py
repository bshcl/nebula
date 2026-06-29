# app/core/utils.py


def ensure_string(content) -> str:
    """
    工业级数据清洗：确保将任何模型的混合输出转换为纯字符串。
    兼容：Gemini (List), OpenAI (String), Groq (String)
    """
    # 1. 如果已经是字符串，直接返回
    if isinstance(content, str):
        return content

    # 2. 如果是 Gemini 风格的列表 (多模态输出)
    if isinstance(content, list):
        # 提取所有类型为 'text' 的片段并拼接
        # 单词：Fragment [ˈfræɡmənt] 片段
        return "".join(
            [
                part.get("text", "") if isinstance(part, dict) else str(part)
                for part in content
            ]
        ).strip()

    # 3. 保底处理：强制转为字符串
    return str(content)
