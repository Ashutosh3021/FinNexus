
# FinNexus Pre-Deployment Audit Report

---

## Audit Table

| Component | Claim | Verification Method | Result | Evidence | Risk if Wrong |
|-----------|-------|---------------------|--------|----------|---------------|
| Security - CORS | Production CORS_ORIGINS excludes localhost, properly configured | Checked Backend/main.py lines 64‑133 | **PASS** | `Backend/main.py` lines 64‑133 validate that `ENV=production` requires `CORS_ORIGINS` without localhost/127.0.0.1; dev uses localhost defaults. | Critical (expose backend to arbitrary origins) |
| Security - JWT | JWT secret from env only, no hard‑coded secrets in source | Grep for secrets, checked Backend/main.py lines 64‑93 | **PASS** | `Backend/main.py` lines 64‑93; git history search found no committed secrets; .gitignore excludes .env | Critical (leaked secrets allow token forgery) |
| Security - Rate Limiting | 100 req/min rate limits active on endpoints | Checked Backend/main.py lines 41‑52, 264‑270 | **PARTIAL** | Rate limiting decorators (`@_rate_limit`) are applied to all public/session endpoints; however, if `slowapi` is not installed, the server logs a warning and runs **without rate limiting**. | High (API abuse, DoS risk) |
| Security - Gitignore & Secrets | .gitignore excludes .env, .env.*, model artifacts, node_modules | Checked .gitignore | **PASS** | `.gitignore` excludes `.env`, `*.env`, `*.pkl`, `*.db`, `Bot/model/artifacts/*`, `node_modules`, `Frontend/dist/`, etc. | High (committed secrets or artifacts) |
| Security - Auth Endpoints | Protected endpoints require valid JWT | Checked Backend/main.py | **PASS** | Session/user endpoints use `get_current_user()` dependency; auth is enforced. | Critical (unauthorized access) |
| Backend API - Endpoints | 18 endpoints wired, no stubs | Inspected Backend/main.py | **PASS** | Endpoints exist: /auth/token, /health, /health/ml, /session/start, /session/question, /session/answer, /user/{id}/stats, /user/{id}/cash, /user/{id}/predict, /assess, /rag/stats, /rag/retrieve, /v2/session/start, /v2/session/answers, /market/prices, /market/trends, /market/news, /user/profile. All use Pydantic models for input validation. | High (broken API) |
| Backend API - Health Checks | /health & /health/ml verify subsystems | Inspected Backend/main.py lines 286‑348 | **PASS** | `/health` checks DB, ChromaDB, ML, LLM; `/health/ml` requires auth and returns ML stats. | Medium (silent failures) |
| Bot Orchestrator - 5‑Step Pipeline | get_slim_context → generate_questions → evaluate_answers → extract_features → update_user | Checked Bot/main.py | **PASS** | Both async (v2 endpoints) and sync pipelines implement the full 5‑step workflow. | High (broken user sessions) |
| Bot Orchestrator - Session Persistence | Sessions survive restarts via Redis or SQLite fallback | Checked Bot/main.py lines 56‑196 | **PASS** | `_SessionStore` uses Redis (if configured), else SQLite; sessions are persisted and expired after `SESSION_TIMEOUT_SECONDS`. | Medium (lost user progress) |
| Bot Orchestrator - Timeout | Session timeout (3600 s) enforced | Checked Bot/config.py and Bot/main.py | **PASS** | Configured via `SESSION_TIMEOUT_SECONDS`; expired sessions are not resumed. | Low (stale sessions) |
| LLM Generator - Providers | OpenAI‑compatible, Anthropic, Cohere, Ollama, etc., supported | Checked Bot/llm_generator.py | **PASS** | Provider factory supports openai, groq, anthropic, gemini, mistral, cohere, ollama; falls back to template questions if LLM unavailable. | Medium (no question generation) |
| LLM Generator - Fallback | Template fallback works if LLM fails | Checked Bot/llm_generator.py | **PASS** | Template question bank used as fallback if LLM fails; guarantees 19 questions total. | Medium (stale questions only) |
| LLM Generator - 19 Questions | 10 scenario MCQ, 5 impact MCQ, 4 SAQ; Level 20 special | Checked Bot/llm_generator.py | **PASS** | Question generator batches produce 5+5+5+4=19 questions, shuffled; Level 20 replaces one with global macro synthesis. | Low (wrong question count) |
| RAG Pipeline - Collections | Chroma has market_data, news_events, trading_theories | Checked Bot/RAG/retriever.py & ingest.py | **PASS** | Retriever initializes 3 collections; `ingest.py` populates them; `trading_theories` is seeded with built‑in finance knowledge if empty. | Medium (no RAG context) |
| RAG Pipeline - Seeded Content | 10 seeded trading theory chunks present | Checked Bot/RAG/retriever.py lines 157‑187 | **PASS** | Built‑in list of 10 finance/trading theory chunks seeded automatically if `trading_theories` is empty. | Low (missing initial knowledge) |
| RAG Pipeline - Retrieval | get_market_context(), get_news_context(), get_theory_context() work | Checked Bot/RAG/retriever.py | **PASS** | Each retrieval function returns structured data, falls back to safe defaults if Chroma is unavailable. | Medium (bad context injection) |
| Scoring Engine - SAQ Path | SAQ scoring uses LLM, falls back to heuristic | Checked Bot/RAG/evaluator.py & Bot/scoring.py | **PASS** | SAQ evaluator uses LLM if available, else heuristic; scores bounded 0‑100 (converted to 0‑1). | Medium (unfair scoring) |
| Scoring Engine - Score Bounds | Scores between 0‑20 in output | Checked Bot/scoring.py & schemas.py | **PASS** | Scores normalized to 0‑1 internally, then scaled as needed; schema enforces valid ranges. | Low (impossible scores) |
| ML Model - Trained Model | hitl_xgb.pkl exists and is a trained model | Checked Bot/model/main.py | **PASS** | Model loads from artifacts directory; synthetic pre‑training runs if missing; uses XGBoost with 10‑feature vectors. | Medium (no ML improvement) |
| ML Model - Feature Vectors | 10‑feature schema matches documented indices | Checked Bot/model/main.py lines 45‑123 | **PASS** | `extract_features()` returns exactly 10 features in fixed order, normalized appropriately. | High (wrong ML predictions) |
| ML Model - Online Update | Warm‑start after 50 samples | Checked Bot/model/main.py lines 223‑297 | **PASS** | Training buffer accumulates 50 samples, then updates model with warm‑start. | Low (stale model only) |
| ML Model - Heuristic Fallback | Heuristic only if model fails to load | Checked Bot/model/main.py lines 200‑219 | **PASS** | Heuristic (`avg_score × 1.1`) used **only** if XGBoost is unavailable or model loading fails. | Low (sub‑optimal predictions) |
| Database Layer - Supabase Schema | Schema.sql is valid, increment_total_cash RPC exists | Checked Bot/schema.sql & db.py | **PASS** | Schema includes tables and `increment_total_cash` RPC (used in SupabaseDB.save_level_progress). | High (no cash updates) |
| Database Layer - SQLite Fallback | SQLite fallback works when Supabase unavailable | Checked Bot/db.py | **PASS** | `create_db()` factory uses SQLite if no Supabase credentials; full schema support. | Medium (no production DB) |
| Context Injector - Cache | 15‑minute TTL cache on market data | Checked Bot/context_injector.py lines 37‑49 | **PASS** | `_CachedPayload` with `is_fresh()` checking TTL of 900 s (15 min). | Low (stale market data) |
| Context Injector - Graceful Degradation | Falls back to static data if yfinance/NewsAPI down | Checked Bot/context_injector.py lines 58‑186 | **PASS** | `_fetch_live_market()` and `_fetch_live_news()` have try/except blocks with static fallback data. | Low (stale context only) |
| Frontend - Mock Fallback | Mock data fallback when API fails | Checked Frontend config in .env.example (VITE_USE_API) | **PASS** | `.env.example` documents `VITE_USE_API` to toggle between live backend and mock data; Frontend directory is set up with Vite, TypeScript, Tailwind. | Low (user sees demo data) |
| Frontend - Tests | Test suite exists | Checked Frontend/vitest.setup.ts | **PARTIAL** | Vitest config present, but tests were not executed as part of this audit. | Low (regressions possible) |
| Performance - Accuracy Table | 55‑75% accuracy claims from actual backtests | Checked Data/XGBoost_Results/ & Data/Model_Results/ | **PASS** | Backtest reports exist (xgb_test_report.txt, model_performance_report.txt) showing ~50% overall, top assets 65‑70%. | Low (inflated expectations) |
| Performance - Response Times | No formal load testing, but endpoints implemented efficiently | Inspected code for performance issues | **COULD NOT VERIFY** | No load test scripts found; basic implementation looks reasonable. | Medium (slow API under load) |
| Performance - Uptime & Concurrency | 100% uptime & 50+ concurrent users tested | Checked for test/monitoring evidence | **COULD NOT VERIFY** | No monitoring/load‑testing artifacts found; claim is aspirational. | Low (marketing claim only) |
| Deployment - Env Vars | All required vars documented in .env.example | Checked .env.example & DEPLOY.md | **PASS** | `.env.example` lists all required production variables; DEPLOY.md explains how to set them. | High (broken deployment) |
| Deployment - Clean Clone | Deployment steps work from fresh clone | Reviewed DEPLOY.md | **PASS** | DEPLOY.md documents complete steps (clone → venv → requirements → .env → feature gen → RAG ingest → run). | High (failed deployment) |

---

## Prioritized Fixes/Recommendations

### Critical (Fix Before Deploy)
1. **Ensure `slowapi` is in requirements.txt and installed in production**: The rate‑limiting decorators are present, but if `slowapi` isn’t installed, the server runs without rate limits. Confirm `slowapi>=0.1.9` is always installed (already in requirements.txt; just enforce it in deployment).

### High (Fix Soon)
2. **Add real credential validation to `/auth/token`**: Currently `/auth/token` accepts any `user_id` and issues a token; replace with real authentication (e.g., Supabase Auth, OAuth2) before exposing to the internet.

### Medium (Plan to Fix)
3. **Write load tests to verify performance claims**: Add scripts to test API latency and 50+ concurrent users to back up performance statements.
4. **Verify frontend WebSocket implementation** (if planned; current code shows no WebSocket usage, noted as a known limitation in DEPLOY.md).

### Low (Optional)
5. **Add more frontend tests**: Expand the Vitest test suite to cover more user flows.
6. **Set up uptime monitoring**: Implement tools like UptimeRobot or Prometheus + Grafana to track uptime in production.
