# Nebula System

Full-stack AI NPC demo: **FastAPI + LangGraph** backend, **Unity** 3D client, token streaming, in-band mood/animation signals, and multi-layer LLM fallback.

Detailed write-up (streaming): [Zenn article](https://zenn.dev/tyora/articles/dc4610389adae0)

```
nebula/
├── nebula-api/          # Python backend (FastAPI, LangGraph, Chroma RAG)
├── Nebula-Unity-Client/ # Unity 6 client (streaming chat UI)
└── docker-compose.yml   # Optional containerized API
```

## Architecture

```mermaid
flowchart LR
    Unity[Unity Client] -->|POST stream| API[FastAPI]
    API --> LG[LangGraph]
    LG --> A[Sentiment]
    LG --> W[World Agent]
    LG --> S[Soul Agent]
    W --> MCP[Maps MCP]
    S --> LLM[Gemini / Groq]
    S -.-> Ollama[Ollama fallback]
    API --> DB[(SQLite)]
    S --> RAG[(Chroma RAG)]
```

**Stream path:** LLM tokens → `yield` → HTTP body chunks → Unity `NebulaStreamHandler` → UI append.

**In-band signals:** `[[MOOD:50]]`, `[[ANIM:WAVE]]`, `[[SYSTEM:OFFLINE]]` embedded in the text stream.

## Prerequisites

| Component | Requirement |
|-----------|---------------|
| Backend | Python 3.11+, Node.js/npx (Maps MCP), API keys |
| Unity | Unity 6, .NET / Newtonsoft.Json |
| Optional | Ollama `llama3.2` for offline soul fallback |
| Docker | Docker Desktop (optional) |

## Quick start — Backend (local)

```powershell
cd nebula-api
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

copy .env.example .env
# Edit .env: GOOGLE_API_KEY, GROQ_API_KEY, GOOGLE_MAPS_API_KEY

python scripts\init_rag.py
venv\Scripts\uvicorn.exe main:app --reload
```

- API: `http://127.0.0.1:8000`
- Health: `GET /health` → `{"status":"ok"}`
- Chat: `POST /api/v1/completions` (streaming)

Smoke test:

```powershell
.\scripts\demo.ps1
```

## Quick start — Docker

```powershell
# Ensure nebula-api/.env exists with API keys
docker compose up --build
```

First start may take 1–2 minutes (RAG index build + embedding model download).

```powershell
curl http://localhost:8000/health
```

**Demo tip:** set `SKIP_WORLD_NODE=true` in `.env` for faster replies during demos.

## Quick start — Unity

1. Open `Nebula-Unity-Client` in Unity 6
2. Open `Assets/_Project/Scenes/SampleScene.unity`
3. Select `NPC_Star` → **Nebula Manager** → confirm **API Base Url** = `http://localhost:8000/api/v1/completions`
4. Play → send a message

### Font setup (CJK + Japanese)

MSYH covers Chinese/English. For Japanese kana, add fallback once in Editor:

**MSYH SDF → Fallback Font Assets → `NotoSansJP-Regular SDF`**

(`NotoSansJP` assets live under `Assets/_Project/Art/Fonts/`.)

## API keys

| Variable | Purpose |
|----------|---------|
| `GOOGLE_API_KEY` | Gemini (primary) |
| `GROQ_API_KEY` | Groq fallback |
| `GOOGLE_MAPS_API_KEY` | Maps MCP / world tools |

See `nebula-api/.env.example` for all options.

## Development status

| Area | Phase | Status |
|------|-------|--------|
| **Phase 0** — refactor & engineering | nebula-api A–G | ✅ v1.0, token streaming, pytest + CI |
| | Unity client 0–3 | ✅ streaming UI, modular layout, API URL + JP fonts |
| | Demo & Ship | ✅ Docker, `/health`, README, `demo.ps1` ([#23](https://github.com/bshcl/nebula/pull/23), [#24](https://github.com/bshcl/nebula/pull/24)) |
| **Phase 1** — productionization | Tool calling, memory, guardrails, eval, observability | ⏳ next |

## License

Personal learning / open-source project. Font licenses: see `Assets/TextMesh Pro/Fonts/` and `NotoSansJP` (OFL).
