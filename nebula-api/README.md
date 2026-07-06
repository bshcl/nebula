# Nebula API

FastAPI backend for the Nebula NPC system: LangGraph workflow (sentiment → world → soul), SSE streaming chat, SQLite persistence, Chroma RAG, and Google Maps MCP.

## Prerequisites

- Python 3.11+ (3.14 tested in development)
- [Node.js](https://nodejs.org/) / `npx` (for Google Maps MCP at startup)
- API keys: Google AI, Groq, Google Maps
- Optional: [Ollama](https://ollama.com/) with `llama3.2` for offline soul fallback

## Quick start

```powershell
cd nebula-api
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

copy .env.example .env
# Edit .env and set GOOGLE_API_KEY, GROQ_API_KEY, GOOGLE_MAPS_API_KEY

python scripts\init_rag.py
uvicorn main:app --reload
```

API base URL: `http://127.0.0.1:8000`

Logs: console and `LOG_DIR` (default `E:\log\nebula-api.log`).

## Environment variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GOOGLE_API_KEY` | Yes | Gemini primary / backup models |
| `GROQ_API_KEY` | Yes | Groq fallback when Gemini fails |
| `GOOGLE_MAPS_API_KEY` | Yes | Maps MCP (world observer tools) |
| `LOG_LEVEL` | No | Default `INFO`; use `DEBUG` for LangGraph traces |
| `LOG_DIR` | No | Default `E:\log` |

See `.env.example` for optional model overrides.

## API endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/` | Health welcome message |
| `POST` | `/api/v1/completions` | Stream NPC reply (SSE-style text stream) |
| `GET` | `/api/v1/sessions` | List session IDs |
| `GET` | `/api/v1/sessions/{id}` | Session metadata + message history |
| `DELETE` | `/api/v1/sessions/{id}` | Delete session and messages |

### Chat request body (`ChatRequest`)

```json
{
  "session_id": "unity-session-123",
  "message": "Hello Sakura",
  "history": [],
  "bot_name": "Sakura",
  "bot_personality": "tsundere NPC"
}
```

`history` is a legacy field from the Unity client; conversation context is loaded from SQLite on the server.

Stream may include in-band signals such as `[[MOOD:75]]` and `[[ANIM:WAVE]]`.

## Scripts

| Script | Purpose |
|--------|---------|
| `scripts/init_rag.py` | Build Chroma index from `app/data/world_settings.txt` |
| `scripts/check_models.py` | List available Google AI models for your key |
| `generate_docs.py` | Regenerate API snapshot markdown (optional) |
| `generate_unity_docs.py` | Regenerate Unity C# context markdown (optional) |

Run scripts from the `nebula-api` directory so `app` imports resolve.

## Data files (local only, not in git)

| Path | Created by |
|------|------------|
| `app/data/nebula.db` | First API startup (`init_db`) |
| `app/data/chroma_db/` | `scripts/init_rag.py` |

## Unity client

Point the Unity client (`Nebula-Unity-Client`) at `http://127.0.0.1:8000/api/v1/completions`. See the monorepo root README for SSE and in-band signaling details.

## Project layout

```text
nebula-api/
├── main.py              # FastAPI entrypoint + MCP lifespan
├── app/
│   ├── api/             # HTTP routes
│   ├── chains/          # LangGraph + agents + tools
│   ├── core/            # config, database, RAG, prompts
│   ├── models/          # ORM, Pydantic schemas, graph state
│   └── services/        # DB helpers, background AI tasks
└── scripts/             # One-off setup utilities
```
