import os

# 1. 定义要排除的“噪音”文件夹和文件
EXCLUDE_DIRS = {
    ".venv",
    "venv",
    "__pycache__",
    ".git",
    "node_modules",
    ".next",
    "var",
    ".pytest_cache",
    ".ruff_cache",
}
EXCLUDE_FILES = {"nebula.db", "package-lock.json", "generate_docs.py", ".env"}


def generate_project_map(root_dir, output_file):
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("# 🌌 Nebula System 项目全景文档\n\n")
        f.write("## 1. 项目目录结构\n```text\n")

        # 生成目录树
        for root, dirs, files in os.walk(root_dir):
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
            level = root.replace(root_dir, "").count(os.sep)
            indent = " " * 4 * level
            f.write(f"{indent}{os.path.basename(root)}/\n")
            sub_indent = " " * 4 * (level + 1)
            for file in files:
                if file not in EXCLUDE_FILES:
                    f.write(f"{sub_indent}{file}\n")

        f.write("```\n\n## 2. 核心代码上下文\n")

        # 读取并合并核心代码
        for root, dirs, files in os.walk(root_dir):
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
            for file in files:
                if file.endswith((".py", ".cs", ".css")) and file not in EXCLUDE_FILES:
                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path, root_dir)

                    f.write(f"\n### 文件: {rel_path}\n")
                    f.write(
                        "```" + ("csharp" if file.endswith(".cs") else "python") + "\n"
                    )
                    try:
                        with open(file_path, "r", encoding="utf-8") as code_f:
                            f.write(code_f.read())
                    except Exception as e:
                        f.write(f"读取失败: {e}")
                    f.write("\n```\n")

    print(f"✅ 文档已生成至: {output_file}")


if __name__ == "__main__":
    generate_project_map(".", "NEBULA_CONTEXT.md")
