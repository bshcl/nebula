"""Generate a markdown snapshot of Unity C# scripts for LLM context."""

import os

from app.config import settings

# Monorepo: nebula-api/../Nebula-Unity-Client/Assets/_Project/Scripts
UNITY_SCRIPTS_PATH = os.path.join(
    os.path.dirname(settings.ROOT_DIR),
    "Nebula-Unity-Client",
    "Assets",
    "_Project",
    "Scripts",
)
OUTPUT_FILE = os.path.join(settings.ROOT_DIR, "NEBULA_UNITY_CONTEXT.md")

EXCLUDE_EXTENSIONS = {".meta", ".unity", ".prefab", ".asset", ".controller", ".mat"}
EXCLUDE_DIRS = {"Plugins", "TextMesh Pro", "Editor"}


def generate_unity_context() -> None:
    if not os.path.exists(UNITY_SCRIPTS_PATH):
        print(f"Error: Unity scripts path not found: {UNITY_SCRIPTS_PATH}")
        return

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("# Nebula System | Unity client architecture snapshot\n\n")
        f.write("## 1. Script directory tree\n```text\n")

        for root, dirs, files in os.walk(UNITY_SCRIPTS_PATH):
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
            level = root.replace(UNITY_SCRIPTS_PATH, "").count(os.sep)
            indent = " " * 4 * level
            f.write(f"{indent}{os.path.basename(root)}/\n")
            sub_indent = " " * 4 * (level + 1)
            for file in files:
                if not any(file.endswith(ext) for ext in EXCLUDE_EXTENSIONS):
                    f.write(f"{sub_indent}{file}\n")

        f.write("```\n\n## 2. C# source files\n")

        for root, dirs, files in os.walk(UNITY_SCRIPTS_PATH):
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
            for file in files:
                if file.endswith(".cs"):
                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path, UNITY_SCRIPTS_PATH)

                    f.write(f"\n### File: {rel_path}\n")
                    f.write("```csharp\n")
                    try:
                        with open(file_path, "r", encoding="utf-8") as code_f:
                            f.write(code_f.read())
                    except OSError as exc:
                        f.write(f"// Read failed: {exc}")
                    f.write("\n```\n")

    print(f"Unity snapshot written to: {OUTPUT_FILE}")


if __name__ == "__main__":
    generate_unity_context()
