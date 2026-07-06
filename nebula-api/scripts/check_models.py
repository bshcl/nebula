"""List Google Generative AI models available for the configured API key."""

import google.generativeai as genai

from app.core.config import settings


def main() -> None:
    genai.configure(api_key=settings.GOOGLE_API_KEY)
    print("Fetching Google AI model catalog...")

    try:
        for model in genai.list_models():
            if "generateContent" in model.supported_generation_methods:
                print(f"Available: {model.name}")
    except Exception as exc:
        print(f"Failed — check GOOGLE_API_KEY in .env: {exc}")


if __name__ == "__main__":
    main()
