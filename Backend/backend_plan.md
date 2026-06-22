# CryptoSense — Backend Development Plan

## Backend Scope
The backend is built with **Python + FastAPI**, handling data fetching, strategy logic, AI model, database interactions, and notifications. It serves as the core decision engine for the frontend.

## Tech Stack (Backend)
- **Framework**: FastAPI (async, auto-docs)
- **Database**: Supabase (Postgres) with SQLAlchemy or direct client
- **AI**: XGBoost + joblib for model persistence
- **Data**: CoinGecko API
- **Notifications**: SendGrid (email), Telegram Bot API
- **Scheduler**: APScheduler (local dev) / Cron (production)
- **Deployment**: Docker + Railway/Render

## Repository Structure (Backend only)
```
backend/
├── main.py                  # FastAPI app entry point
├── requirements.txt
│
├── data/
│   ├── fetcher.py           # CoinGecko OHLCV + current price
│   ├── cleaner.py           # Data validation, gap filling
│   └── storage.py           # Supabase CRUD helpers
│
├── strategy/
│   ├── ma_filter.py         # 50-day MA calculation & trend filter
│   ├── sip_timer.py         # Best entry window + double-month logic
│   └── backtester.py        # Historical backtest engine
│
├── model/
│   ├── features.py          # Feature engineering pipeline
│   ├── train.py             # XGBoost training + walk-forward validation
│   ├── predict.py           # Daily inference + confidence scoring
│   └── retrain_scheduler.py # Weekly model retraining
│
├── engine/
│   └── decision.py          # Core signal generation (MA + AI + risk rules)
│
├── notifications/
│   ├── email_sender.py      # SendGrid templates & sending
│   └── telegram_bot.py      # Telegram message sending
│
├── api/
│   ├── auth.py              # Supabase Google OAuth helpers
│   ├── users.py             # User config CRUD
│   ├── signals.py           # Signal history & generation endpoints
│   ├── logbook.py           # Portfolio logbook endpoints
│   └── backtest.py          # Backtest trigger & results
│
├── utils/
│   └── helpers.py           # Common utilities (date handling, etc.)
│
└── config/
    └── settings.py          # Environment & Supabase config
```

## Database Schema Implementation
See full schema in original plan.md. Implement using Supabase SQL editor or migrations.

Key tables to create:
- `users`
- `user_assets`
- `signals`
- `logbook`
- `backtest_results`

Use Row Level Security (RLS) policies tied to `auth.uid()`.

## Core Logic Implementation Order (Phases)

### Phase 1: Data Layer
1. Implement `data/fetcher.py` — CoinGecko daily OHLCV (2+ years) and current price
2. `data/cleaner.py` — Handle missing days, outliers
3. `data/storage.py` — Supabase insert/select helpers

### Phase 2: Strategy Layer
1. `strategy/ma_filter.py` — Calculate 50-day MA, return trend boolean
2. `strategy/sip_timer.py` — Monthly price percentile logic + double-month
3. `strategy/backtester.py` — Simulate trades with fees/slippage

### Phase 3: AI Model Layer
1. `model/features.py` — Generate all listed features
2. `model/train.py` — Training pipeline + metrics
3. `model/predict.py` — Load model, predict confidence
4. `model/retrain_scheduler.py`

### Phase 4: Decision Engine
- `engine/decision.py` — Orchestrate daily signal generation per user_asset

### Phase 5: API Layer
1. Setup FastAPI with CORS, dependency injection
2. Auth routes (Supabase integration)
3. CRUD endpoints for users, signals, logbook, backtests
4. Protected routes using Supabase JWT

### Phase 6: Notifications
1. Email templates (daily signal, monthly report)
2. Telegram integration
3. Trigger logic based on signal changes or best entry windows

## API Endpoints (Planned)

**Auth & Users**
- `POST /auth/google` — Callback
- `GET /users/me` — Current user config
- `PATCH /users/me` — Update preferences

**Signals**
- `GET /signals` — Latest signals for user assets
- `POST /signals/generate` — Force daily engine run (admin)

**Logbook**
- `GET /logbook`
- `POST /logbook` — Add entry
- `GET /logbook/summary` — P&L overview

**Backtest**
- `POST /backtest` — Run for symbol/date range
- `GET /backtest/results`

## Environment Variables (.env)
```
SUPABASE_URL=
SUPABASE_KEY=
SENDGRID_API_KEY=
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=  # for testing
COINGECKO_BASE_URL=https://api.coingecko.com/api/v3
```

## Development Commands
```bash
# Install
cd backend
pip install -r requirements.txt

# Run locally
uvicorn main:app --reload

# Run daily engine
python scripts/run_daily_engine.py

# Backtest
python -m strategy.backtester --symbol BTC
```

## Production Considerations
- Dockerize with multi-stage build
- Environment-specific config
- Rate limiting on CoinGecko (respect 30 calls/min)
- Error handling & logging (Sentry optional)
- Model versioning

## Testing Strategy
- Unit tests for features, MA calculation, signal logic
- Integration tests for API endpoints (with test DB)
- Backtest validation against known good periods

## Next Steps After Backend
Once backend is solid and APIs tested, proceed to Phase 4 (Frontend).

---
*Derived from plan.md — Backend-focused breakdown*