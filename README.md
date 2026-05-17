# NEURALCUT

AI-powered video creation studio. Conversational interface that turns a prompt into a finished short video by orchestrating script generation, image/visual generation, voiceover, and composition through a multi-agent pipeline.

Inspired by Director (video-db), ViMax / VideoAgent (HKUDS), story-flicks, Mora, and univa.online.

---

## What's in this repo

```
veedra/
├── frontend/         Next.js 14 (App Router) + TypeScript + Tailwind + Supabase auth
├── backend/          FastAPI + Celery + Redis. Agent orchestrator + provider adapters
├── supabase/         SQL migrations (schema, RLS, storage buckets, triggers)
├── docker-compose.yml
└── .env.example
```

## Architecture

```
┌────────────────────────────────────────────────────────────────────┐
│  Next.js frontend (Vercel / self-host)                              │
│  • Landing, auth, dashboard, /studio (chat-driven editor)           │
│  • Talks to Supabase directly for auth + reads                      │
│  • Talks to FastAPI for: agent runs, generation, video render       │
└──────────────────┬───────────────────────────────┬──────────────────┘
                   │                               │
                   ▼                               ▼
       ┌──────────────────────┐         ┌─────────────────────────┐
       │ Supabase             │         │ FastAPI gateway          │
       │ • Postgres + RLS     │◄────────┤ • REST + SSE             │
       │ • Auth               │         │ • Enqueues Celery jobs   │
       │ • Storage buckets    │         │ • Streams agent thoughts │
       └──────────────────────┘         └────────────┬─────────────┘
                                                     │
                                                     ▼
                                        ┌────────────────────────┐
                                        │ Celery workers          │
                                        │ • script_agent          │
                                        │ • visual_agent          │
                                        │ • voice_agent           │
                                        │ • compositor (ffmpeg)   │
                                        └────────────┬────────────┘
                                                     │
                                                     ▼
                                        ┌────────────────────────┐
                                        │ Provider adapters       │
                                        │ • OpenAI / Anthropic    │
                                        │ • Replicate / Stability │
                                        │ • ElevenLabs            │
                                        │ • Mock (default)        │
                                        └─────────────────────────┘
```

### The agent loop

A user prompt — *"60-second explainer on how solar panels work, friendly tone, vertical"* — hits `/api/agent/run`. The orchestrator decomposes it:

1. **script_agent** → scene-by-scene script with narration + visual descriptions
2. **visual_agent** → per-scene image generation (parallel)
3. **voice_agent** → TTS per scene (parallel)
4. **compositor** → ffmpeg stitches scenes + voice + transitions, uploads to Supabase Storage

Each step streams progress over SSE so the frontend shows the agent "thinking" live.

## Quickstart

```bash
cp .env.example .env             # fill in keys; mock mode works with none
docker compose up --build        # starts postgres, redis, backend, worker
cd frontend && npm install && npm run dev
# open http://localhost:3000
```

By default everything runs in **MOCK mode** — provider calls return placeholder data so you can verify the full pipeline end-to-end without spending a cent. Set `PROVIDER_MODE=live` in `.env` and supply the relevant API keys to switch to real generation.

### Supabase setup

You can either use the dockerized Postgres (zero-setup) or a real Supabase project:

- **Local**: migrations apply automatically on `docker compose up`
- **Hosted**: install Supabase CLI, then `supabase link --project-ref <ref>` and `supabase db push`

## What's working vs. what's a TODO

✅ Working
- Auth (email + magic link via Supabase)
- Projects CRUD with RLS
- Agent orchestrator with streaming SSE
- Job queue (Celery + Redis)
- ffmpeg composition pipeline
- Mock providers for all steps

🚧 Stubbed (clear extension points)
- Live provider adapters (signatures done, swap mock for real SDK calls)
- Video understanding agent (upload video → Q&A) — endpoint exists, model integration is the TODO
- Billing / quotas
- Render queue prioritization
- Collaborative editing

## License

MIT
