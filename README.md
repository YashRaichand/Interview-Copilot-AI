# Interview Copilot AI

AI-powered interview preparation platform. Upload a resume and job description to get instant ATS scoring, missing-skill detection, AI-generated interview questions, adaptive mock interviews, real-time answer evaluation, and a personalized 30-day learning roadmap.

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python, FastAPI, SQLAlchemy (async), Alembic |
| ML/NLP | PyTorch, Transformers, Sentence-Transformers, spaCy, scikit-learn, XGBoost |
| Database | PostgreSQL |
| Cache | Redis |
| Frontend | Next.js 14, TypeScript, TailwindCSS, Framer Motion, Recharts |
| Auth | JWT + Google OAuth (optional) |
| Storage | Cloudinary |
| AI | Anthropic Claude API |
| Deployment | Docker, Render |
| Monitoring | Prometheus, Grafana |
| CI/CD | GitHub Actions |

## Quick Start (Local Development)

### Option A — Docker Compose (recommended)

```bash
git clone <repo-url> interview-copilot-ai
cd interview-copilot-ai
cp backend/.env.example backend/.env
# Edit backend/.env and set ANTHROPIC_API_KEY, CLOUDINARY_* credentials
docker-compose up --build
```

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Option B — Manual Setup

```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm
cp .env.example .env  # fill in your credentials
alembic upgrade head
uvicorn app.main:app --reload
```

```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

## Deploying to Render

1. Push this repo to GitHub.
2. Render Dashboard → **New** → **Blueprint** → connect the repo.
3. When prompted, fill in the `sync: false` secrets: `ANTHROPIC_API_KEY`, `CLOUDINARY_*`.
4. Click **Deploy Blueprint**.
5. Once both services are live, go to the frontend service's **Environment** tab and set `NEXT_PUBLIC_API_URL` to your backend's full URL (e.g. `https://interview-copilot-backend.onrender.com`) — **must include `https://`**.
6. Go to the backend service's **Environment** tab and set `BACKEND_CORS_ORIGINS` to a JSON array containing your frontend's full URL, e.g. `["https://interview-copilot-frontend.onrender.com"]`.
7. Both services will auto-redeploy with the new values. Registration and login will then work end-to-end.

## Troubleshooting — Bugs Already Fixed In This Codebase

These were discovered and fixed during real production deployment. If you fork or regenerate parts of this project, watch for these regressions:

1. **`bcrypt`/`passlib` password hashing crash on registration (500 error)** — `bcrypt==5.0.0` silently breaks `passlib==1.7.4`'s hashing backend. Fixed by pinning `bcrypt==4.0.1` in `requirements.txt` and by explicitly truncating passwords to bcrypt's 72-byte limit in `auth_service.py` before hashing.
2. **`spacy`/`typer` dependency conflict** — `spacy==3.7.4` requires `typer<0.10`, which conflicts with `fastapi-cli`'s `typer>=0.15` requirement, making `pip install` unresolvable. Fixed by using `spacy==3.8.2`.
3. **`request.client` is `None` behind Render's reverse proxy** — the rate limiter crashed reading `request.client.host`. Fixed in `dependencies.py`'s `get_client_ip()`, which reads `X-Forwarded-For` first and falls back gracefully.
4. **`BACKEND_CORS_ORIGINS` format** — must be a JSON array string (`["https://..."]`), not a bare URL. A bare string crashes `pydantic-settings` on startup with a `SettingsError`.
5. **Render Redis "Key Value" `fromService` properties** — only `connectionString`, `host`, and `port` are valid; `password` and `url` are not. Use `property: connectionString` and read it via `REDIS_URL` in `config.py`.
6. **Render free-tier limit: one database + one Key Value instance** — deploying a second Blueprint with its own Postgres/Redis fails with "cannot have more than one active free tier database/Key Value instance." Delete old ones first, or upgrade the plan.
7. **`npm ci` requires a committed `package-lock.json`** — this repo doesn't commit one, so the frontend Dockerfile uses `npm install` instead.
8. **Next.js standalone output has no `/public` directory** — copying a nonexistent folder fails the Docker build. The Dockerfile runs `mkdir -p ./public` instead of copying it.
9. **Hardcoding `ENV PORT=3000` in the frontend Dockerfile** — Render injects its own `PORT` (typically `10000`) at runtime; a hardcoded value causes Render's port scan to time out. Don't set `ENV PORT` at all — Next.js's standalone server reads it from the environment automatically.
10. **ESLint blocking production builds** — a single unescaped-apostrophe lint error failed the entire Docker build. Fixed with `eslint: { ignoreDuringBuilds: true }` in `next.config.js` (linting still runs in CI separately).
11. **Pydantic `model_answer` field warning** — Pydantic v2 warns when a field starts with `model_` (its reserved namespace). Fixed with `model_config = ConfigDict(protected_namespaces=())` on the relevant schemas.
12. **Dead `/demo` link on the landing page** — the "Watch Demo" button pointed to a route that didn't exist, producing a 404. Fixed by pointing it to an in-page anchor (`#features`) instead.

## Project Structure

```
interview-copilot-ai/
├── backend/
│   ├── app/
│   │   ├── api/v1/          # Route handlers
│   │   ├── models/          # SQLAlchemy ORM models
│   │   ├── schemas/         # Pydantic schemas
│   │   ├── services/        # Business logic
│   │   ├── nlp/             # Resume/JD parsers, ATS scorer, question generator, answer evaluator, roadmap generator
│   │   ├── ml/               # Resume classifier, success predictor, answer scorer
│   │   └── utils/            # PDF, Cloudinary, Redis, logging
│   ├── migrations/           # Alembic
│   ├── tests/                 # pytest suite (unit + API + regression tests for the bugs above)
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── app/               # Next.js App Router pages
│   │   ├── components/        # layout, charts, interview chat UI
│   │   └── lib/api.ts          # Typed API client
│   └── Dockerfile
├── docker-compose.yml
├── render.yaml
└── .github/workflows/ci.yml
```

## License

MIT
