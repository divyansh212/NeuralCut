# NeuralCut

A multi-agent text-to-video studio. Type a prompt; an orchestrator decomposes it
into agents (**script → visuals → voice → compose**); a Celery worker runs the
pipeline asynchronously; the browser watches progress stream live over Redis
pub/sub; the finished MP4 lands in Supabase Storage.

Runs end-to-end in **mock mode** with zero API keys. Switch to **live mode** to
use real generation (PyTorch/Stable Diffusion for images, an LLM for script, a
TTS API for voice).

## Stack

| Layer | Tech |
|-------|------|
| Frontend | Next.js 14 (App Router) + Tailwind CSS |
| API | FastAPI (synchronous front door only) |
| Workers | Celery |
| Broker + event bus | Redis (Celery broker **and** pub/sub for live progress) |
| DB / Auth / Storage | Supabase (Postgres + RLS + Storage) |
| Composition | ffmpeg (deterministic, always real) |
| Live image model | PyTorch + diffusers (optional) |
| Ops console | Streamlit (optional) |

## Architecture

```
Browser (Next.js studio)
   │  POST /jobs  (Supabase JWT)            GET /jobs/{id}/stream?token=… (SSE)
   ▼                                                  ▲
FastAPI ──writes job row──► Supabase Postgres         │ SUBSCRIBE job:{id}
   │  enqueue task                                    │
   ▼                                                  │
Redis ◄─────────── broker ─────────────┐              │
   ▼ task                              │ PUBLISH event │
Celery worker ─ orchestrator ─ agents ─┘
   script → visuals → voice → ffmpeg → upload to Supabase Storage → job=done
```

The API and the worker are **separate processes**. That's exactly why live
progress goes through Redis pub/sub, never an in-memory dict — a dict would let
the worker write to its own memory while the SSE endpoint reads from a different
empty one, and events vanish silently.

## Repo layout

```
neuralcut-platform/
├── frontend/            Next.js 14 + Tailwind  → deploy to Vercel
├── backend/             FastAPI + Celery + providers + Streamlit ops → deploy to Railway/Render
│   └── app/
│       ├── main.py          FastAPI app + CORS
│       ├── deps.py          real Supabase JWT auth (NO bypass)
│       ├── db.py            Supabase queries, always user-scoped
│       ├── storage.py       upload renders to Supabase Storage
│       ├── worker.py        Celery
│       ├── orchestrator.py  the pipeline
│       ├── compositor.py    ffmpeg (always real)
│       ├── events.py        Redis pub/sub publisher
│       ├── providers/       mock + live adapters (live = PyTorch image gen)
│       └── routes/          jobs.py, stream.py (SSE)
├── supabase/migrations/ 0001_init.sql, 0002_rls.sql, 0003_storage.sql
├── docker-compose.yml   redis + api + worker + ops (Streamlit)
├── render.yaml          Render blueprint
└── .env.example
```

---

## Local quickstart (Windows / PowerShell)

```powershell
# 1. env
Copy-Item .env.example .env        # then fill in Supabase keys (see below)

# 2. backend + redis + worker (+ Streamlit ops on :8501)
docker compose up --build

# 3. frontend, second terminal
cd frontend
Copy-Item .env.local.example .env.local   # fill in the 3 NEXT_PUBLIC_ vars
npm install
npm run dev
# open http://localhost:3000
```

Running the backend without Docker (two terminals):

```powershell
cd backend
pip install -r requirements.txt
# terminal 1 — API
uvicorn app.main:app --host 0.0.0.0 --port 8000
# terminal 2 — worker  (--pool=solo is required on Windows)
celery -A app.worker.celery_app worker --loglevel=info --pool=solo
```

In mock mode, submit a prompt in the Studio and you'll see
`script → visuals → voice → compose` events stream in, then a placeholder MP4.

---

## Supabase setup (do this first — prerequisite for everything)

1. Create a hosted Supabase project.
2. In **SQL Editor**, run the three migrations in order:
   `0001_init.sql`, `0002_rls.sql`, `0003_storage.sql`.
3. Grab keys from **Settings → API**:
   - Frontend: `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY`
   - Backend: `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_KEY`, `SUPABASE_JWT_SECRET`
4. After deploying the frontend, add its URL under **Authentication → URL
   Configuration** (Site URL + Redirect URLs) or magic-link callbacks are rejected.

> Service key and JWT secret are **backend-only** secrets. Never put them in any
> `NEXT_PUBLIC_*` var.

---

## Deploy

### Phase 1 — Frontend on Vercel
1. Import the repo, set **Root Directory** to `frontend`.
2. Set env vars before the first build: `NEXT_PUBLIC_SUPABASE_URL`,
   `NEXT_PUBLIC_SUPABASE_ANON_KEY`, `NEXT_PUBLIC_BACKEND_URL`
   (leave the backend URL as a localhost placeholder for now).
3. Deploy, then add the Vercel URL to Supabase auth allowlist.

### Phase 2 — Backend on Railway / Render
You need three things sharing one Redis + env: **Redis, an API service, a worker service.**

**Render** — import `render.yaml` as a Blueprint (it provisions all three on the
free tier), then fill the secret env vars in the dashboard.

**Railway** — add a Redis plugin, then two services from this repo:
- API: start `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Worker: start `celery -A app.worker.celery_app worker --loglevel=info`

Set on both: `SUPABASE_*`, `REDIS_URL`, `PROVIDER_MODE`, and `ALLOWED_ORIGINS`
= your Vercel URL (CORS).

### Phase 3 — wire together
Update Vercel's `NEXT_PUBLIC_BACKEND_URL` to the deployed API URL, redeploy.
Smoke test: sign in → submit a prompt → confirm events stream and a render appears.

---

## Going live (real generation)

Set `PROVIDER_MODE=live` and implement the three live adapters in
`backend/app/providers/live.py`:

- **Script** → an LLM (OpenAI), returning `[{scene, narration, visual_desc}]`.
- **Visuals** → already wired to **PyTorch + diffusers** (Stable Diffusion). Install
  the torch extras (`pip install -r requirements.txt` with the torch lines
  uncommented, or `pip install ".[torch]"`). A CUDA GPU is strongly recommended.
- **Voice** → a TTS API (ElevenLabs).

The compositor is always real ffmpeg — nothing to swap there.

## Streamlit ops console

`backend/streamlit/dashboard.py` is an internal console to submit jobs, watch the
live Redis stream, and preview renders without the web frontend — handy for
debugging the worker/pub-sub in isolation. Runs at `:8501` under compose, or
`streamlit run streamlit/dashboard.py` locally.

## Pre-public checklist

- [ ] `PROVIDER_MODE` set intentionally (`mock` for a free demo, `live` + keys for real output)
- [ ] No auth bypass in `deps.py` — real JWT verification only
- [ ] RLS enabled on all tables AND backend queries filter by `user_id`
- [ ] Service key / JWT secret only on the backend, never in `NEXT_PUBLIC_*`
- [ ] SSE proxy buffering disabled; stream endpoint authorizes job ownership
- [ ] Supabase redirect allowlist includes the production frontend URL
