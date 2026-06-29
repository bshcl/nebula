import os
import json
from pathlib import Path

# 定义会话数据的存储路径
SESSION_DIR = Path("sessions")

# 确保会话目录存在，如果不存在则创建
if not SESSION_DIR.exists():
    SESSION_DIR.mkdir()


def save_chat_to_file(session_id: str, data: dict):
    """将聊天数据保存到文件中

    Args:
        session_id (str): 会话ID，用于区分不同的对话会话
        data (dict): 要保存的聊天数据，通常包含用户消息、AI回复等信息
    """
    file_path = SESSION_DIR / f"{session_id}.json"

    # 将数据写入JSON文件，使用UTF-8编码，并且格式化输出以便于阅读
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def load_chat_from_file(
    session_id: str,
) -> dict:  # 为什么=> dict？因为我们希望这个函数返回一个字典类型的数据，这样前端在接收到这个数据后，可以直接使用它来渲染聊天界面，而不需要再进行额外的转换。
    """从文件中加载聊天数据

    Args:
        session_id (str): 会话ID，用于区分不同的对话会话

    Returns:
        dict: 加载的聊天数据，如果文件不存在则返回一个空字典
    """
    file_path = SESSION_DIR / f"{session_id}.json"
    if not file_path.exists():
        return None
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        # 【关键：如果文件坏了，打印错误并返回空，而不是让整个后端崩溃】
        print(f"警告：文件 {session_id} 损坏，无法读取。错误原因: {e}")
        return None


def list_all_sessions() -> list:
    """列出所有会话ID

    Returns:
        list: 包含所有会话ID的列表
    """
    return [file.stem for file in SESSION_DIR.glob("*.json")]


def get_session_detail(session_id: str) -> dict:
    """获取指定会话的详细数据

    Args:
        session_id (str): 会话ID，用于区分不同的对话会话

    Returns:
        dict: 包含会话详细数据的字典，如果文件不存在则返回一个空字典
    """
    return load_chat_from_file(session_id)


def delete_session_file(session_id: str):
    """删除指定会话的文件

    Args:
        session_id (str): 会话ID，用于区分不同的对话会话
    """
    file_path = SESSION_DIR / f"{session_id}.json"
    if file_path.exists():
        os.remove(file_path)
        return True
    return False
