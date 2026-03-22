# ChainWatch — Blockchain Security Intelligence

AI-powered multi-chain wallet analyser running inside an **OpenGradient TEE** (Trusted Execution Environment).  
Streams real-time analysis events over **Server-Sent Events** from a FastAPI backend to a React + TypeScript frontend.

---

## Architecture

```
chainwatch/
├── backend/                  # FastAPI + LangGraph ReAct agent
│   ├── app/
│   │   ├── main.py           # FastAPI app, CORS, lifespan
│   │   ├── core/
│   │   │   └── config.py     # Pydantic-Settings (env vars)
│   │   ├── models/
│   │   │   └── schemas.py    # Request / response schemas
│   │   ├── services/
│   │   │   ├── blockchain_tools.py  # LangChain tools (balance, yields, news)
│   │   │   └── agent_service.py     # LangGraph agent + SSE streaming bridge
│   │   └── api/v1/
│   │       ├── analysis.py   # GET /api/v1/analysis/stream  (SSE)
│   │       └── health.py     # GET /api/v1/health
│   └── requirements.txt
│
└── frontend/                 # React 18 + TypeScript + Vite + Tailwind
    └── src/
        ├── api/              # SSE client hook (useAnalysis)
        ├── components/
        │   ├── analysis/     # AddressInput, StepProgress, ToolCallFeed,
        │   │                 # ScanningVisual, ReportDisplay
        │   ├── layout/       # Header
        │   └── ui/           # CyberPanel, GlitchText, MatrixRain, TerminalLog
        ├── hooks/
        ├── pages/            # HomePage
        ├── store/            # Zustand (analysisStore)
        ├── types/            # TypeScript interfaces
        └── utils/            # Helpers (formatElapsed, detectChain, …)
```

---

## Prerequisites

| Tool | Version |
|------|---------|
| Python | ≥ 3.11 |
| Node.js | ≥ 20 |
| npm / pnpm | any recent |
| OpenGradient private key | from [app.opengradient.ai](https://app.opengradient.ai) |

---

## Quick Start

### 1 — Clone & configure

```bash
git clone <repo>
cd chainwatch
```

### 2 — Backend

```bash
cd backend

# Create & activate virtual environment
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# Install dependencies (opengradient==0.9.0 pinned)
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env — set OG_PRIVATE_KEY=<your_key>

# Start development server
uvicorn app.main:app --reload --port 8000
```

API docs available at **http://localhost:8000/docs**

### 3 — Frontend

```bash
cd frontend

npm install
npm run dev
```

Frontend available at **http://localhost:5173**

---

## Environment Variables

### Backend (`backend/.env`)

| Variable | Required | Description |
|----------|----------|-------------|
| `OG_PRIVATE_KEY` | ✅ | OpenGradient wallet private key |
| `FRONTEND_ORIGIN` | optional | CORS origin (default: `http://localhost:5173`) |

---

## SSE Event Protocol

The analysis endpoint `GET /api/v1/analysis/stream?address=<addr>` streams newline-delimited JSON events:

| `type` | Payload fields | Description |
|--------|---------------|-------------|
| `status` | `message` | Informational log line |
| `step_start` | `step`, `title` | A pipeline step begins |
| `step_complete` | `step` | A pipeline step finished |
| `tool_call` | `name`, `args`, `call_id` | Agent invokes a tool |
| `tool_result` | `name`, `content`, `call_id` | Tool returned a result |
| `complete` | `report` | Final markdown report |
| `error` | `message` | Fatal error |
| `stream_end` | — | Stream sentinel — close connection |

---

## Tech Stack

**Backend**
- FastAPI 0.111 + Uvicorn (ASGI)
- Pydantic v2 + pydantic-settings
- opengradient==0.9.0 (TEE LLM adapter)
- LangGraph (ReAct agent)
- LangChain Core (tool definitions)

**Frontend**
- React 18 + TypeScript (strict)
- Vite 5
- Tailwind CSS 3
- Framer Motion 11
- Zustand 4 (state management)
- react-markdown (report rendering)
- Lucide React (icons)

---

## Supported Chains

| Chain | Detection | Native | Tokens |
|-------|-----------|--------|--------|
| Ethereum / EVM | `0x` + 40 hex | ETH | ERC-20 via Ankr |
| Arbitrum | `0x` + 40 hex | ETH | ERC-20 via Ankr |
| Solana | base58 32-44 | SOL | SPL (Token + Token-2022) |
| SUI | `0x` + 64 hex | SUI | all coins |
| Bitcoin | `bc1`/`1`/`3` | BTC | — |
