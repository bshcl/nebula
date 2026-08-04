# Nebula API

FastAPI backend for the Nebula NPC system: LangGraph workflow (sentiment → world → soul), SSE-style streaming chat, SQLite persistence (sessions, inventory, quests), Chroma RAG, and Google Maps MCP.

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
| `CORS_ORIGINS` | No | `*` (dev) or comma-separated allowed origins |

See `.env.example` for optional model overrides.

## Streaming protocol (`POST /api/v1/completions`)

The response uses `Content-Type: text/event-stream` but the body is a **raw UTF-8 text stream**, not standard SSE `data:` frames.

| Aspect | Behavior |
|--------|----------|
| Format | Plain text chunks as the LLM generates tokens |
| End signal | Final chunk may include `[[MOOD:{0-100}]]` for Unity mood sync |
| In-band tags | NPC may emit `[[ANIM:WAVE]]`, `[[GIFT:item_id]]`, etc. |
| Unity client | `NebulaStreamHandler` reads bytes directly via `DownloadHandlerScript` |

Example stream:

```text
[[ANIM:WAVE]] Hmph, you finally showed up...[[MOOD:72]]
```

If you integrate a new client, read the response body incrementally; do not expect `data: ...\n\n` SSE framing.

## API endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/` | Health welcome message |
| `GET` | `/health` | Liveness probe (`{"status":"ok"}`) |
| `POST` | `/api/v1/completions` | Stream NPC reply (SSE-style text stream) |
| `GET` | `/api/v1/sessions` | List session IDs |
| `GET` | `/api/v1/sessions/{id}` | Session metadata + message history |
| `DELETE` | `/api/v1/sessions/{id}` | Delete session and messages |
| `GET` | `/api/v1/inventory/{session_id}` | List stacked inventory items for a session |
| `GET` | `/api/v1/quests/{session_id}/{quest_id}` | Quest status (`not_started` / `ready_to_claim` / `claimed` / …) |
| `POST` | `/api/v1/quests/{session_id}/{quest_id}/ready` | Mark quest `ready_to_claim` |
| `POST` | `/api/v1/quests/{session_id}/{quest_id}/claim` | Claim reward (grants item + mood delta) |

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

Stream may include in-band signals such as `[[MOOD:75]]`, `[[ANIM:WAVE]]`, and `[[GIFT:item_id]]`.

### Inventory and quests (server authority)

- Mutations go through `inventory_service.grant_item` and `quest_service` (HTTP routes and Soul tools share these services).
- Soul Agent tools (`get_quest_status`, `mark_quest_ready`, `claim_quest_reward`, `send_gift`) inject `session_id` from graph state and call the same services.
- `send_gift` persists via `grant_item`, then instructs the model to emit `[[GIFT:item_id]]` only after a successful grant. The in-band tag is a Unity presentation cue, not the source of truth.

## Scripts

| Script | Purpose |
|--------|---------|
| `scripts/init_rag.py` | Build Chroma index from `app/data/world_settings.txt` |
| `scripts/check_models.py` | List available Google AI models for your key |
| `generate_docs.py` | Regenerate API snapshot markdown (optional) |
| `generate_unity_docs.py` | Regenerate Unity C# context markdown (optional) |

Run scripts from the `nebula-api` directory so `app` imports resolve.

## Tests and lint

```powershell
pip install -r requirements-dev.txt
ruff check app tests
pytest
```

CI runs the same checks on pull requests that touch `nebula-api/**` (see `.github/workflows/nebula-api-ci.yml`).

## Docker

From the monorepo root (requires `nebula-api/.env` with API keys):

```powershell
docker compose up --build
```

The image includes Python 3.12 and Node.js/npx for the Google Maps MCP subprocess. Data persists in Docker volumes (`nebula-api-data`, `nebula-api-logs`).

## Data files (local only, not in git)

| Path | Created by |
|------|------------|
| `app/data/nebula.db` | First API startup (`init_db`) |
| `app/data/chroma_db/` | `scripts/init_rag.py` |

## Unity client

Point the Unity client (`Nebula-Unity-Client`) at `http://127.0.0.1:8000/api/v1/completions`. Inventory and quest buttons call the REST routes above. See the monorepo root README for the F-interact loop and in-band signaling.

## Project layout

```text
nebula-api/
├── main.py              # FastAPI entrypoint + MCP lifespan
├── app/
│   ├── api/             # HTTP routes (chat, inventory, quests)
│   ├── chains/          # LangGraph + agents + tools
│   ├── core/            # config, database, RAG, prompts
│   ├── game/            # Quest / item definitions (static defs)
│   ├── models/          # ORM, Pydantic schemas, graph state
│   └── services/        # inventory, quest, DB helpers, background AI
└── scripts/             # One-off setup utilities
```
