---
title: Purple Platform - Autonomous Purple Team
emoji: 🛡️
colorFrom: purple
colorTo: indigo
sdk: docker
app_port: 7860
pinned: false
license: mit
short_description: B2B SaaS where Red Team & AI Detection Engine co-evolve in isolated sandbox - OWASP/MITRE + posture score
tags:
  - cybersecurity
  - purple-team
  - langgraph
  - owasp
  - mitre-attack
---

# Purple Platform — Autonomous Purple Team

**One-liner:** B2B SaaS where autonomous **Red Team** and **AI Detection Engine** continuously attack/defend a target web app inside an isolated Docker sandbox, learning via **RAG + Knowledge Graph (NetworkX + ChromaDB)**, producing a **real-time Security Posture Score** (Detection Rate, MTTR, Coverage).

This Space hosts the **FastAPI backend** (`/health`, `/docs`, `/api/v1/*`) for demo. Full stack = API + Postgres/Redis/Chroma + Next.js dashboard (Vercel) + Expo mobile.

## Architecture
`Orchestrator (LangGraph)` → `Red Team (5 agents: IDOR, Auth Abuse, Injection, Business Logic, SSRF)` ↔ `Detection Engine (5 hardening agents)` → `Sandbox (Docker)` → `KG+RAG (OWASP Top10 + MITRE, episode memory)`

**Tech:** LangGraph/LangChain/Pydantic v2, Ollama (stub fallback → Groq/OpenRouter), sentence-transformers, ChromaDB, Docker, FastAPI, SQLAlchemy, Redis Streams, PostgreSQL, Next.js 14, Tailwind, Recharts, Expo, Socket.IO, Prometheus/Grafana, OpenTelemetry stub.

## API Docs
Once Space is running: `https://<your-space>.hf.space/docs`

## Local (full stack)
```bash
cp .env.prod.example .env
./deploy.sh --build
# web http://localhost:3000, api http://localhost:8001/docs, grafana http://localhost:3002
```

## HF Space - Quick Start
This Space uses **SQLite + in-memory mock** for Postgres/Redis/Chroma (no external DB needed for demo). For production, set secrets in **Settings → Variables and secrets**:

- `DATABASE_URL` (e.g. `postgresql+asyncpg://user:pass@host/db` - Neon/Supabase)
- `REDIS_URL` (`redis://...` or keep `memory://` for demo)
- `JWT_SECRET` (≥32 chars)
- `GROQ_API_KEY` / `OPENROUTER_API_KEY` (optional, Ollama stub works offline)

## Web Dashboard
Deployed on Vercel: **https://purple-team-rosy.vercel.app** (set `NEXT_PUBLIC_API_URL=https://<your-space>.hf.space` in Vercel env, then redeploy).

## Mobile
```bash
cd apps/mobile && npx expo start
```

## Demo Scenarios (≥3 required, 5 shipped)
`idor` (A01/A07, T1548), `injection` (A03, T1190), `business_logic` (A04, T1485) — plus `ssrf` (A10, T1590.005) and `broken_auth` (A07).

## Docs
See `deploy.sh`, `docker-compose.prod.yml`, `grafana/dashboards/purple-overview.json`.
