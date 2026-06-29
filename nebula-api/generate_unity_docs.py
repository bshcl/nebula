import os

# ==========================================
# 配置区
# ==========================================
# 💡 架构师提示：指向你 Unity 项目的 Scripts 文件夹
UNITY_SCRIPTS_PATH = "E:/UnityProject/Nebula-Unity-Client/Assets/_Project/Scripts"
OUTPUT_FILE = "NEBULA_UNITY_CONTEXT.md"

# 定义要排除的后缀和文件夹
EXCLUDE_EXTENSIONS = {".meta", ".unity", ".prefab", ".asset", ".controller", ".mat"}
EXCLUDE_DIRS = {"Plugins", "TextMesh Pro", "Editor"}


def generate_unity_context():
    if not os.path.exists(UNITY_SCRIPTS_PATH):
        print(f"❌ 错误：找不到路径 {UNITY_SCRIPTS_PATH}，请检查路径配置。")
        return

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("# 🧊 Nebula System | Unity 身体架构文档\n\n")
        f.write("## 1. 脚本目录结构\n```text\n")

        # 1. 生成目录树
        for root, dirs, files in os.walk(UNITY_SCRIPTS_PATH):
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
            level = root.replace(UNITY_SCRIPTS_PATH, "").count(os.sep)
            indent = " " * 4 * level
            f.write(f"{indent}{os.path.basename(root)}/\n")
            sub_indent = " " * 4 * (level + 1)
            for file in files:
                if not any(file.endswith(ext) for ext in EXCLUDE_EXTENSIONS):
                    f.write(f"{sub_indent}{file}\n")

        f.write("```\n\n## 2. C# 核心源代码\n")

        # 2. 提取代码内容
        for root, dirs, files in os.walk(UNITY_SCRIPTS_PATH):
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
            for file in files:
                if file.endswith(".cs"):
                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path, UNITY_SCRIPTS_PATH)

                    f.write(f"\n### 文件: {rel_path}\n")
                    f.write("```csharp\n")
                    try:
                        with open(file_path, "r", encoding="utf-8") as code_f:
                            f.write(code_f.read())
                    except Exception as e:
                        f.write(f"// 读取失败: {e}")
                    f.write("\n```\n")

    print(f"✅ Unity 档案已生成至: {OUTPUT_FILE}")


if __name__ == "__main__":
    generate_unity_context()
