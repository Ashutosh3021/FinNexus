# CryptoSense — Full Project Plan

---

## Product Vision

A personal crypto investment decision system that tells you **when to invest, how much, and why** — backed by a trend-following strategy and an AI confidence layer. Not a trading bot. A decision assistant with a logbook, backtest engine, and smart notifications. Built for real use, not a resume.

---

## Tech Stack

| Layer | Technology | Reason |
|-------|-----------|--------|
| Frontend | React + Vite | Fast, GitHub Pages deployable |
| Styling | TailwindCSS | Utility-first, clean dashboard UI |
| Charts | Recharts | Lightweight, React-native |
| Backend | Python FastAPI | Async, fast, clean API design |
| Database | Supabase (Postgres) | Free tier, scalable, built-in auth |
| Auth | Google OAuth via Supabase | One-click login, no password system |
| AI Model | XGBoost | Reliable, interpretable, fast to train |
| Market Data | CoinGecko API (free) | No key needed, 2+ years history |
| Email | SendGrid (free tier) | 100 emails/day free |
| Telegram | Telegram Bot API | 100% free, instant delivery |
| Scheduler | APScheduler (local) → Cron (cloud) | Runs daily signal engine |
| Cloud (Phase 6) | Railway or Render | Free tier available |

---

## Repository Structure

```
cryptosense/
│
├── backend/
│   ├── main.py                  # FastAPI entry point
│   ├── requirements.txt
│   │
│   ├── data/
│   │   ├── fetcher.py           # CoinGecko OHLCV fetcher
│   │   ├── cleaner.py           # Data cleaning + gap handling
│   │   └── storage.py           # Supabase read/write helpers
│   │
│   ├── strategy/
│   │   ├── ma_filter.py         # 50-day MA trend filter
│   │   ├── sip_timer.py         # Best entry window logic
│   │   └── backtester.py        # Full backtest engine
│   │
│   ├── model/
│   │   ├── features.py          # Feature engineering
│   │   ├── train.py             # XGBoost training pipeline
│   │   ├── predict.py           # Inference + confidence scoring
│   │   └── retrain_scheduler.py # Weekly retrain cron
│   │
│   ├── engine/
│   │   └── decision.py          # Combines MA + AI → signal output
│   │
│   ├── notifications/
│   │   ├── email_sender.py      # SendGrid integration
│   │   └── telegram_bot.py      # Telegram Bot API
│   │
│   └── api/
│       ├── auth.py              # Supabase Google OAuth routes
│       ├── users.py             # User config CRUD
│       ├── signals.py           # Signal fetch endpoints
│       ├── logbook.py           # Portfolio tracker endpoints
│       └── backtest.py          # Backtest trigger endpoint
│
├── frontend/
│   ├── index.html
│   ├── vite.config.js
│   ├── tailwind.config.js
│   │
│   └── src/
│       ├── main.jsx
│       ├── App.jsx
│       │
│       ├── pages/
│       │   ├── Landing.jsx          # Public landing page
│       │   ├── Onboarding.jsx       # Wizard for new users
│       │   ├── Dashboard.jsx        # Signal feed (home)
│       │   ├── Logbook.jsx          # Portfolio tracker
│       │   ├── Backtest.jsx         # Backtest view
│       │   └── Settings.jsx         # User preferences
│       │
│       ├── components/
│       │   ├── SignalCard.jsx        # Invest/Hold/Skip card
│       │   ├── ConfidenceBar.jsx     # Visual confidence meter
│       │   ├── LogbookEntry.jsx      # Single asset log row
│       │   ├── PnLSummary.jsx        # Portfolio P&L overview
│       │   ├── BacktestChart.jsx     # Returns over time chart
│       │   ├── WizardStep.jsx        # Reusable onboarding step
│       │   └── NotifBadge.jsx        # Alert status indicator
│       │
│       └── lib/
│           ├── supabase.js           # Supabase client init
│           ├── api.js                # FastAPI fetch helpers
│           └── utils.js              # Formatters, helpers
│
├── scripts/
│   ├── seed_historical_data.py   # One-time data seed
│   └── run_daily_engine.py       # Manual trigger for signals
│
├── .env.example
├── README.md
└── plan.md  ← this file
```

---

## Database Schema (Supabase / Postgres)

### `users`
| Column | Type | Notes |
|--------|------|-------|
| id | uuid | Primary key (from Supabase auth) |
| email | text | From Google account |
| telegram_chat_id | text | Nullable, set after bot link |
| sip_mode | enum | `best_entry` or `double_next` |
| risk_tolerance | enum | `low`, `medium`, `high` |
| created_at | timestamp | |

### `user_assets`
| Column | Type | Notes |
|--------|------|-------|
| id | uuid | |
| user_id | uuid | FK → users |
| symbol | text | e.g. `BTC`, `ETH` |
| monthly_capital | numeric | e.g. 500 |
| trade_mode | enum | `spot` or `long_term` |
| horizon_months | int | Nullable, for long term |
| is_active | boolean | |

### `signals`
| Column | Type | Notes |
|--------|------|-------|
| id | uuid | |
| symbol | text | |
| date | date | |
| signal | enum | `invest`, `hold`, `skip` |
| confidence | float | 0.0 – 1.0 |
| ma_trend | boolean | Price > 50MA |
| price_at_signal | numeric | |
| created_at | timestamp | |

### `logbook`
| Column | Type | Notes |
|--------|------|-------|
| id | uuid | |
| user_id | uuid | FK → users |
| symbol | text | |
| bought_price | numeric | User-entered |
| amount_invested | numeric | User-entered (₹) |
| quantity | numeric | Auto-calculated |
| buy_date | date | |
| current_price | numeric | Auto-fetched daily |
| notes | text | Optional |

### `backtest_results`
| Column | Type | Notes |
|--------|------|-------|
| id | uuid | |
| symbol | text | |
| start_date | date | |
| end_date | date | |
| total_return_pct | float | |
| win_rate | float | |
| max_drawdown | float | |
| sharpe_ratio | float | |
| run_at | timestamp | |

---

## Core Logic

### Decision Engine Flow

```
Every day at 8:00 AM IST (APScheduler):

For each active user_asset:
  1. Fetch latest OHLCV from CoinGecko
  2. Calculate 50-day MA
     → If price < 50MA: signal = SKIP (MA filter override)
  3. Run XGBoost model
     → Get confidence score (0–1)
  4. Apply risk threshold (based on user risk_tolerance):
     → Low:    invest if confidence > 0.70
     → Medium: invest if confidence > 0.65
     → High:   invest if confidence > 0.55
  5. Combine:
     → MA=True  + confidence above threshold → INVEST
     → MA=True  + confidence below threshold → HOLD
     → MA=False (any confidence)             → SKIP
  6. Save to signals table
  7. Check if notification should be sent:
     → If signal changed from yesterday → notify
     → If best entry window detected    → notify
```

### SIP Timing Logic

**Mode 1: Best Entry This Month (default)**
- Track daily price through the month
- If today's price is in the lowest 20th percentile of the month so far → flag as good entry
- Send alert: "Price near monthly low. Good time to invest ₹500."
- If no good window found by 25th of month → send reminder with current signal

**Mode 2: Double Next Month (user opt-in)**
- If signal = SKIP for entire month → flag for next month
- Next month capital = 2× normal
- Hard cap: only 1 skip→double cycle allowed. Never 3×.
- Warning shown in UI: "Double-month mode active. Review before confirming."

### AI Model — XGBoost

**Features (per asset, daily):**
- 7-day price return
- 30-day price return
- 14-day RSI
- MACD signal line delta
- Volume: 7-day avg vs 30-day avg ratio
- Distance from 50-day MA (%)
- 30-day price volatility (std dev of returns)
- BTC 7-day return (as market context, even for non-BTC assets)

**Target variable:**
- Binary: 1 if price 7 days later is > today's price, else 0

**Training:**
- Time-based split: train on first 80% of data, test on last 20%
- Walk-forward validation: retrain monthly on rolling 18-month window
- Evaluation metrics: accuracy, precision, F1, ROC-AUC

**Backtest rules:**
- Include 0.25% fee per trade (CoinSwitch avg)
- Include 0.15% slippage
- Invest fixed ₹500 on INVEST signals only
- Hold cash on HOLD/SKIP

---

## Build Phases

### Phase 1 — Data + Strategy Engine
**Goal:** Prove the MA strategy works on historical data before any AI.

Tasks:
- [ ] CoinGecko fetcher for OHLCV (daily candles, 2 years)
- [ ] Data cleaner (fill gaps, remove outliers)
- [ ] 50-day MA filter logic
- [ ] SIP backtester with fees + slippage
- [ ] Output: CSV + printed backtest stats

Deliverable: Run `python backtest.py --symbol BTC --from 2022-01-01` and see P&L.

---

### Phase 2 — AI Model
**Goal:** Add confidence scoring on top of the working strategy.

Tasks:
- [ ] Feature engineering pipeline
- [ ] XGBoost training script
- [ ] Walk-forward validation
- [ ] Confidence output (0–1 probability)
- [ ] Model serialization (save/load with joblib)
- [ ] Weekly retrain scheduler

Deliverable: `python predict.py --symbol ETH` outputs today's confidence score.

---

### Phase 3 — FastAPI Backend + Supabase
**Goal:** Wrap everything in a proper API with user data.

Tasks:
- [ ] Supabase project setup
- [ ] Google OAuth route
- [ ] User config endpoints (create, read, update)
- [ ] Signal generation endpoint
- [ ] Logbook CRUD endpoints
- [ ] Backtest trigger endpoint
- [ ] `.env` config for all keys

Deliverable: Postman/curl can hit all endpoints. Auth works.

---

### Phase 4 — Frontend (React + Vite)
**Goal:** Working dashboard deployable to GitHub Pages.

Tasks:
- [ ] Vite + React + Tailwind setup
- [ ] Supabase client + Google login
- [ ] Landing page
- [ ] Onboarding wizard (6 steps)
- [ ] Dashboard — signal feed
- [ ] Logbook page — add entry + view P&L
- [ ] Backtest page — trigger + view results
- [ ] Settings page
- [ ] GitHub Pages deploy config

Deliverable: `npm run build` → pushes to `gh-pages` branch, live URL works.

---

### Phase 5 — Notifications
**Goal:** Email and Telegram alerts working end-to-end.

Tasks:
- [ ] SendGrid account + template setup
- [ ] Email sender for: signals, monthly report, stop-loss alert
- [ ] Telegram bot creation (BotFather)
- [ ] Telegram sender for: instant signal alerts
- [ ] Notification trigger logic in decision engine
- [ ] User notification preferences respected

Deliverable: Signal runs → email arrives in inbox AND Telegram message received.

---

### Phase 6 — Cloud Deploy
**Goal:** System runs automatically, no laptop required.

Tasks:
- [ ] Dockerize FastAPI backend
- [ ] Deploy to Railway (free tier)
- [ ] Set up cron job for daily signal engine
- [ ] Set up weekly model retrain job
- [ ] Connect frontend env vars to production backend URL
- [ ] Monitor logs

Deliverable: Close laptop → signals still arrive next morning.

---

## Notification Templates

### Email — Daily Signal
```
Subject: CryptoSense Signal — BTC | {date}

Signal:     INVEST ✅
Confidence: 74%
Trend:      Bullish (Price above 50MA)
Suggested:  Invest ₹500 in BTC today

Reason: Strong uptrend confirmed. AI model sees positive momentum over next 7 days with 74% confidence.

[View Dashboard] [Update Settings]
```

### Email — Monthly Report
```
Subject: Your CryptoSense Monthly Report — {month}

Portfolio Summary
─────────────────
Total Invested:   ₹4,500
Current Value:    ₹5,120
Overall Return:   +13.8%

Asset Breakdown
BTC   ₹2,000 invested → ₹2,340 (+17%)
ETH   ₹1,500 invested → ₹1,620 (+8%)
SOL   ₹1,000 invested → ₹1,160 (+16%)

Signals This Month
5 INVEST / 2 HOLD / 1 SKIP

[View Full Report]
```

### Telegram — Instant Alert
```
🟢 INVEST — BTC
Confidence: 74% | Trend: ↑
Suggested: ₹500 today

Price near monthly low — good entry window.
```

---

## Risk Management Rules (Hardcoded, Not Optional)

These are enforced by the system, not left to the user:

1. Max 4 assets per user (prevents over-diversification into noise)
2. Stop-loss alert at -8% from logbook entry price (email + Telegram)
3. Double-next-month mode: max 1 cycle, never 3× capital
4. AI signal only fires when MA filter is also green
5. Confidence below 0.50 always = SKIP regardless of risk tolerance

---

## Future Features (Post-MVP)

- CoinSwitch PRO API integration (auto order placement)
- NIFTY 50 / Gold support
- Sentiment analysis from crypto news (NLP layer)
- Social signals (Fear & Greed Index)
- Export logbook as CSV / PDF
- Referral system for multi-user growth
- Mobile PWA with push notifications

---

## Key Constraints & Decisions

| Decision | Choice | Reason |
|----------|--------|--------|
| Exchange | CoinSwitch (manual) | No PRO API needed to start |
| Data source | CoinGecko | Free, reliable, 2yr history |
| Auth | Google only | Simple, no password management |
| Model | XGBoost | Interpretable, fast, doesn't need GPU |
| Backtest split | Time-based only | Random split = data leakage |
| SIP logic | Best entry this month | Safer than doubling next month |
| Max assets | 4 per user | Focus over diversification |

---

*Last updated: Phase 0 — Pre-build spec lock*