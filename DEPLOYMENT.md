# Deployment Runbook

Three-tier architecture across three repos:

| Repo | Role | Hosted on | Domain |
|---|---|---|---|
| `corridor_agent_ui` | Next.js UI | Vercel | `corridor-ui.vercel.app` |
| `corridor-intelligence-platform-agents` | FastAPI + LangGraph + pipelines | Fly.io (or K8s via Jenkins) | `agents.corridor.app` |
| `corridor-data` | Pulled data artifacts | Cloudflare R2 | `r2://corridor-data` |

## Order of operations (first-time deploy)

1. **Create R2 bucket** (Cloudflare dashboard → R2 → create bucket `corridor-data`, private).
2. **Upload current `data/` snapshot** — run fresh pull in monorepo, then push to R2 (see below).
3. **Deploy agents backend to Fly.io** — it mounts the R2 bucket via rclone or pulls via fsspec.
4. **Deploy UI to Vercel** — reads from agents backend API.

## 1. Fresh data pull

Currently `run_all.py` lives in the agents repo (ported from monorepo).

```bash
cd corridor-intelligence-platform-agents
uv sync                         # installs all pipeline + API deps
cp .env.example .env            # fill in ACLED, GEE, COMTRADE creds
python run_all.py validate      # quick creds check
python run_all.py refresh --force   # full pull, ~30–60 min
python run_all.py report        # markdown freshness report
```

## 2. Push data to R2

### Option A — rclone (recommended, one-shot)

```bash
# install rclone once: https://rclone.org/install/
rclone config                   # add R2 remote: S3-compatible, account ID from Cloudflare, access/secret keys
rclone sync ./data r2:corridor-data/v1/data --progress --checksum
rclone sync ./outputs r2:corridor-data/v1/outputs --progress
```

### Option B — `aws s3 sync` (R2 is S3-compatible)

```bash
export AWS_ACCESS_KEY_ID=<R2_ACCESS_KEY>
export AWS_SECRET_ACCESS_KEY=<R2_SECRET_KEY>
export AWS_ENDPOINT_URL=https://<ACCOUNT_ID>.r2.cloudflarestorage.com
aws s3 sync ./data s3://corridor-data/v1/data
```

### Writing a manifest

Keep a small `corridor-data` GitHub repo containing only:
- `manifest.json` — `{ "version": "v1", "pulled_at": "...", "pipelines": {...} }`
- `README.md` — how to download/mount
- No raw files (those live in R2)

## 3. Deploy agents backend

### Fly.io

```bash
cd corridor-intelligence-platform-agents
fly auth login
fly launch --copy-config --no-deploy     # reads fly.toml
fly volumes create corridor_data --region fra --size 10
fly secrets set \
  OPENAI_API_KEY=sk-... \
  GEMINI_API_KEY=... \
  OPENROUTER_API_KEY=sk-or-... \
  ACLED_USERNAME=... ACLED_PASSWORD=... \
  COMTRADE_API_KEY=... \
  GEE_PROJECT=... \
  BACKEND_API_KEY="$(openssl rand -hex 32)" \
  DATABASE_URI=... REDIS_URI=...
fly deploy
```

To hydrate the volume from R2 on first boot, add an init container or run once:

```bash
fly ssh console -C "rclone sync r2:corridor-data/v1/data /data"
```

### Kubernetes (Jenkins path)

The existing `Jenkinsfile` already handles this. Add a new stage that hydrates the PVC from R2 before the pod starts, or run `rclone sync` on a CronJob every 24h.

## 4. Deploy UI

```bash
cd corridor_agent_ui
vercel login
vercel link
vercel env add BACKEND_URL production              # https://agents.corridor.app
vercel env add LANGGRAPH_BACKEND_URL production    # https://agents.corridor.app
vercel env add PROJECTS_API_URL production         # https://agents.corridor.app
vercel env add THREADS_API_URL production          # https://agents.corridor.app
vercel env add NEXT_PUBLIC_LANGGRAPH_API_URL production   # https://corridor-ui.vercel.app
vercel --prod
```

Update agents `CORS_ORIGINS` (or `fly secrets set CORS_ORIGINS=https://corridor-ui.vercel.app`) after the UI domain is live.

## 5. Post-deploy checks

```bash
# Backend liveness
curl https://agents.corridor.app/api/healthz/live

# Auth gating (should 401 without key)
curl -i https://agents.corridor.app/api/corridor/info
curl -i -H "X-API-Key: $BACKEND_API_KEY" https://agents.corridor.app/api/corridor/info

# UI
open https://corridor-ui.vercel.app
```

## Rotating secrets

```bash
NEW=$(openssl rand -hex 32)
fly secrets set BACKEND_API_KEY=$NEW
vercel env rm BACKEND_API_KEY production
vercel env add BACKEND_API_KEY production   # paste $NEW
vercel --prod
```

## Monitoring

- Fly metrics: `fly logs`, `fly status`
- LangSmith: set `LANGCHAIN_TRACING_V2=true`, `LANGSMITH_API_KEY=...`, `LANGSMITH_PROJECT=corridor_intelligence`
- Vercel: built-in logs + analytics
- Sentry (optional): add `@sentry/nextjs` on UI and `sentry-sdk[fastapi]` on backend
