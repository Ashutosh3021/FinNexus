# FinNexus — Production Error Report

> **Scope:** Static + dynamic scan of the FinNexus monorepo (Backend FastAPI, Frontend React/Vite, Bot module, and deploy configs `render.yaml` / `vercel.json`) to find everything that crashes the app **in production**.
>
> **Date:** 2026-07-09
> **Method:** Read every entry-point file; ran the real frontend build (`npm run build` → exit 0); grepped deploy configs and `requirements.txt`; followed the import graph `Backend/main.py → Bot.main → Bot.RAG/Bot.model/Bot.db`; verified `create_db` fallback behavior. No code was modified.

---

## TL;DR — what actually happens in production today

| Layer | Status in current deploy | Why |
|---|---|---|
| **Backend (Render)** | 🔴 **Never starts** | Two independent startup blockers (C1, C2). The web service exits before serving a single request. |
| **Frontend (Vercel)** | 🟡 **Builds & runs, but shows DEMO data** | Build passes, but `VITE_USE_API=false` is baked in, so users see mock data and the (already-down) backend is never called. |
| **Bot (Supabase path)** | 🔴 **Crashes on level completion** | Latent `.rpc()` bug (C3). Masked *today* only because the broken deploy falls back to SQLite; fires the moment Supabase is enabled. |

**Bottom line:** The user-facing "production app" is effectively a static mock demo. The real backend cannot start, and the moment it is fixed the Supabase code path will throw on every level completion. Fix C1 → C2 → C3 first.

---

## Severity legend
- 🔴 **CRITICAL** — guaranteed crash / blocks startup / blocks deploy.
- 🟠 **HIGH** — crashes in a real production configuration, or breaks a core feature.
- 🟡 **MEDIUM** — conditional crash / reliability hazard / functional break.
- ⚪ **LOW** — cosmetic or theoretical.

---

## 🔴 CRITICAL

### C1 — `gunicorn` is missing from `requirements.txt`, but `render.yaml` starts the service with it
- **Files:** `render.yaml:9` (startCommand), `requirements.txt` (no `gunicorn`)
- **Error:** `startCommand: gunicorn Backend.main:app -k uvicorn.workers.UvicornWorker ...`
- **Root cause:** `requirements.txt` never lists `gunicorn`. Render's Python runtime does not pre-install it, so the start command fails immediately with `gunicorn: command not found`. The web service is never launched.
- **Crash type:** Service startup failure (Render reports "build succeeded, deploy failed" / health-check failure).
- **Fix:** Add `gunicorn>=21.0` to `requirements.txt` (or switch the start command to `uvicorn Backend.main:app --host 0.0.0.0 --port $PORT`, since `uvicorn` is already a dependency).
- **Verified:** `grep -i gunicorn requirements.txt` → no match.

### C2 — `CORS_ORIGINS` is unset while `ENV=production`, so the backend calls `sys.exit(1)` at import
- **Files:** `render.yaml` (only sets `ENV`, `PORT`, `JWT_SECRET`, `PYTHON_VERSION`; `CORS_ORIGINS` is commented out at lines 19–27), `Backend/main.py:96–121`
- **Error:**
  ```python
  if _ENV == "production":
      if not _ALLOWED_ORIGINS:          # CORS_ORIGINS empty at boot
          logger.critical("STARTUP ABORTED: CORS_ORIGINS is not set in production. ...")
          sys.exit(1)                    # Backend/main.py:114
  ```
- **Root cause:** `render.yaml` forces `ENV=production` but never defines `CORS_ORIGINS`. On import, `_ALLOWED_ORIGINS` is `[]`, the production branch is taken, and the process exits with code 1 **before the `app` object is usable**. Every gunicorn worker dies instantly.
- **Note:** `JWT_SECRET` is fine — `render.yaml` uses `generateValue: true`, producing a value outside the insecure set, so the earlier `sys.exit(1)` at `Backend/main.py:79` is *not* triggered.
- **Crash type:** Process startup abort (code 1) — never serves traffic.
- **Fix:** Add to `render.yaml` `envVars`:
  ```yaml
  - key: CORS_ORIGINS
    value: https://<your-vercel-app>.vercel.app
  ```
  (No `localhost` entries — those also trigger `sys.exit(1)` at `Backend/main.py:115–121`.)

### C3 — `Bot/db.py:216` calls `.rpc()` on a table object → `AttributeError` on the Supabase path
- **File:** `Bot/db.py:216` (inside `SupabaseDB.save_level_progress`)
- **Code:**
  ```python
  self._table("user_bot_progress").rpc(          # ← table object has no .rpc()
      "increment_total_cash",
      {"p_user_id": user_id, "p_amount": reward},
  ).execute()
  ```
- **Root cause:** `self._table(name)` returns a PostgREST `SyncRequestBuilder`, which exposes only `select/insert/update/upsert/delete`. `rpc` lives on the **client** (`self._client`), not the table. So this raises `AttributeError: 'SyncRequestBuilder' object has no attribute 'rpc'`.
- **Impact:** `save_level_progress()` runs on **every** level completion (`update_user` / `_finish_level`). On Supabase this turns a successful session submit into a 500.
- **Why it is currently MASKED:** `render.yaml` does **not** set `SUPABASE_URL`/`SUPABASE_KEY`, so `create_db` (`Bot/db.py:558–568`) returns `SQLiteDB` (SQLite fallback). The `.rpc()` line is never reached *in the current broken deploy*. It **will** crash the moment Supabase is enabled — which `.env.example` and `DEPLOY.md` explicitly recommend for production.
- **Crash type:** Runtime 500 on the production DB path (Supabase).
- **Fix:** `self._client.rpc("increment_total_cash", {"p_user_id": user_id, "p_amount": reward}).execute()`

---

## 🟠 HIGH

### H1 — `render.yaml` installs the ENTIRE `requirements.txt` (data-pipeline + heavy ML) on the backend service
- **Files:** `render.yaml:6–8` (`pip install -r requirements.txt`), `requirements.txt`
- **Problem:** The backend deploy installs the whole monorepo requirements, including data-pipeline packages that are irrelevant to the API and notoriously hard to install: `nsepy==0.8`, `nsefin==0.1.5`, `pyzdata>=1.0.0`, `jugaad-data>=0.3.0`, `alpha-vantage==2.3.1`, `catboost`, `lightgbm`, plus `sentence-transformers`, `chromadb`, `xgboost`, `supabase`, etc.
- **Risk:** If **any** package is uninstallable or fails to compile on Render's build image, `pip install` aborts and the **build/deploy fails entirely**. Even on success, this bloats slug size and build time, risking Render's build timeout.
- **Crash type:** Build failure (no deploy) / timeout — HIGH risk.
- **Fix:** Create a lean `Backend/requirements.txt` (fastapi, uvicorn, gunicorn, pydantic, openai, chromadb, sentence-transformers, httpx, PyJWT, slowapi, supabase) and point `render.yaml` `buildCommand` at it. Keep the heavy ML/data deps out of the API service.

### H2 — Frontend deploys with `VITE_USE_API=false` → production serves mock data, never the backend
- **Files:** `Frontend/.env:9` (`VITE_USE_API=false`), `.env.example:78`, plus `VITE_API_URL=http://localhost:8000`
- **Problem:** `VITE_*` vars are baked in at **build time**. With `VITE_USE_API=false`, every page runs on static mock data — `.env.example` itself warns "otherwise users see demo data." Additionally `VITE_API_URL=http://localhost:8000` is wrong for production (only matters once API mode is on).
- **Impact:** Even after the backend is fixed (C1/C2), the deployed frontend will still show fake data unless `VITE_USE_API=true` and `VITE_API_URL` point at the Render backend. User-facing "production" is currently a demo.
- **Crash type:** Functional/configuration defect (not an exception, but a production-correctness break).
- **Fix:** In the Vercel project settings set `VITE_USE_API=true` and `VITE_API_URL=https://<your-render-backend>.onrender.com`, then redeploy. (Also ensure `CORS_ORIGINS` allows the Vercel domain — see C2.)

### H3 — Heavy work runs at import time, duplicated across 2 gunicorn workers → boot stall / crash loop
- **Files:** `Backend/main.py:155` (`bot = FinnexusBot.from_env()`), `Bot/main.py:598–623` (`from_env`), `Bot/model/main.py` (synthetic XGBoost pre-train + pickle write)
- **Problem:** `from_env()` runs synchronously at module import:
  - `RAGRetriever` opens Chroma and may trigger `run_full_ingestion` (downloads a `sentence-transformers` embedding model + ingests — network + CPU heavy).
  - `MLModel` trains a synthetic XGBoost model and **writes `hitl_xgb.pkl` / `hitl_scaler.pkl`** to `Bot/model/artifacts/`.
  - `render.yaml` launches `-w 2` workers, so this whole sequence runs **twice concurrently**, both writing the same pickle files (a write race).
- **Risk:** On Render's startup health-check window this can be slow enough to get the worker killed → crash/restart loop. Model downloads may also be blocked or OOM.
- **Crash type:** Reliability hazard / boot timeout (not a guaranteed exception, but a real production failure mode).
- **Fix:** Lazy-init the bot (defer `from_env()` to first request or a post-startup hook), use a single worker or pre-baked artifacts, and guard the pickle writes so concurrent workers don't race.

### H4 — `Data/Cleaned` does not exist → market endpoints return empty
- **Files:** `Backend/main.py:562` (`_DATA_ROOT = PROJECT_ROOT/"Data"/"Cleaned"`), `:566–585` (asset catalogue referencing `Crypto/BTC_cleaned.csv`, `Commodities/Gold_cleaned.csv`, …)
- **Problem:** The repo contains `Data/Raw_data/` and `Data/Features/` but **no `Data/Cleaned/`** (0 matches confirmed). Every `_read_csv_tail` hits a missing file, is caught, and returns `[]`, so `/market/prices` and `/market/trends` respond `{"prices": [], "count": 0}`.
- **Impact:** Functional break (no exception), but the entire market-data feature is dead until the cleaned CSVs exist. (Moot today only because the frontend is in mock mode — H2.)
- **Crash type:** Functional break (empty responses, not a 500).
- **Fix:** Generate `Data/Cleaned/*.csv` in a build/seed step, or repoint `_DATA_ROOT` at the actual data location.

---

## 🟡 MEDIUM

### M1 — `Bot/llm/__init__.py` imports modules that don't exist → `ModuleNotFoundError` if imported
- **File:** `Bot/llm/__init__.py:12–15`
- **Code:** `from Bot.llm.client import LLMClient` / `generator` / `evaluator` / `context` — but `Bot/llm/` contains **only** `__init__.py`.
- **Impact:** Any future `import Bot.llm` hard-fails. The live service imports `Bot.llm_generator` (not `Bot.llm`), so it doesn't crash *today*.
- **Fix:** Remove/fix the broken subpackage, or delete `Bot/llm/` if unused.

### M2 — `.single()` on `users` raises on a missing row (Supabase path)
- **File:** `Bot/db.py:247` (`add_paper_cash`), `:260` (`get_paper_cash`)
- **Problem:** PostgREST `.single()` returns HTTP 406 when zero rows match; supabase-py raises an unhandled `APIError`. Called on every completed level.
- **Why mostly-safe today:** The `users` row is normally upserted at session start (`increment_session_count` → `save_user_profile`), so a row usually exists by completion. Crashes only if that upsert is skipped/failed or the method is reached without a session.
- **Fix:** Drop `.single()`; use `.limit(1)` and handle empty `result.data`.

### M3 — Absolute `from Bot import ...` imports require the project root on `sys.path`
- **File:** `Bot/main.py:36–48` and throughout `Bot/` (`from Bot import config`, `from Bot.schemas import ...`, `from Bot.RAG.retriever import ...`)
- **Problem:** These resolve only if `FinNexus/` (repo root) is on `sys.path` — i.e. launched as `python -m Bot.main` or imported by `Backend/`. Starting the bot as `python Bot/main.py` raises `ModuleNotFoundError` at startup.
- **Fix:** Ensure the service is always launched from the repo root (Render `rootDir: .` + gunicorn does this correctly; document it for any standalone bot run).

### M4 — `chromadb.config.Settings` import is version-fragile (RAG silently disabled, not a crash)
- **File:** `Bot/RAG/retriever.py:32`
- **Problem:** `from chromadb.config import Settings` is guarded by `try/except ImportError`, so on modern chromadb (where `.config` was removed) `_CHROMA_OK` becomes `False` and **RAG silently stops working** instead of erroring.
- **Fix:** Drop the deprecated import; rely on `chromadb` APIs current in the pinned version.

---

## ⚪ LOW / cosmetic (Frontend)

- **L1 — `ToastContainer.tsx:39`** uses `animate-in slide-in-from-right-4 fade-in-0` etc., but `tailwindcss-animate` is **not installed** (`package.json` deps lack it; `tailwind.config.js` `plugins: []`). Toasts render without the enter animation. Build still passes. Fix: `npm i -D tailwindcss-animate` + add the plugin, or remove the classes.
- **L2 — `PaperTradingPage.tsx:10`** `useState<Asset>(assets[0])` assumes a non-empty asset list. Safe today (`assets` is seeded from `mockAssets`), but would throw if ever empty.
- **L3 — `useAppStore.ts:319`** `resp.questions.map(...)` assumes the `/v2/session/start` shape; inside `try/catch` with mock fallback, so never crashes.
- **L4 — `TrendsPage.tsx:154–155`** `Math.max(...recentPrices.map(...))` on an empty array yields `-Infinity`/`+Infinity`; handled downstream, only a flat sparkline.

> Note: A SPA deep-link 404 concern was raised during the frontend scan, but the **root `vercel.json`** already has `"rewrites": [{ "source": "/(.*)", "destination": "/" }]`, which serves `index.html` for client routes. Static assets are served before rewrites apply, so this is not a production issue. (Optional polish: use `destination: "/index.html"` for clarity.)

---

## Verification performed
- ✅ Frontend build: `cd Frontend && npm run build` (`tsc -b && vite build`) → **exit 0**. No TypeScript errors, no build-time crash. (The app will deploy; it just serves mock data — H2.)
- ✅ `grep -i gunicorn requirements.txt` → **no match** (confirms C1).
- ✅ Read `render.yaml` + `Backend/main.py:96–121` → confirmed `sys.exit(1)` when `CORS_ORIGINS` empty in production (confirms C2).
- ✅ Read `Bot/db.py:558–568` → confirmed `SQLiteDB` fallback when `SUPABASE_URL`/`SUPABASE_KEY` unset, so C3 is currently masked (confirms nuance).
- ✅ Read `Bot/db.py:204–219` → confirmed `.rpc()` is called on a table object (confirms C3).
- ✅ Confirmed `Data/Cleaned` absent in repo (confirms H4).

## Recommended fix order
1. **C1** — add `gunicorn` to `requirements.txt` (or switch start command to `uvicorn`).
2. **C2** — set `CORS_ORIGINS` (and `LLM_PROVIDER`/`LLM_API_KEY`, `SUPABASE_*`) in `render.yaml`.
3. **C3** — fix `Bot/db.py:216` `.rpc()` → `self._client.rpc(...)` **before** enabling Supabase.
4. **H1** — split backend requirements so the Render build doesn't install the data-pipeline stack.
5. **H2** — set `VITE_USE_API=true` + `VITE_API_URL` in Vercel and redeploy.
6. **H3** — move `FinnexusBot.from_env()` out of import time (lazy/post-startup init).
7. **H4** — generate `Data/Cleaned` CSVs (or repoint the data root).
8. Optionally address M1–M4 and the LOW frontend cosmetics.
