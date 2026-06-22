# CryptoSense

**Your personal crypto investment decision assistant.**

Tells you **when to invest, how much, and why** — using a robust trend-following strategy combined with an AI confidence layer. Includes portfolio logbook, backtesting, and smart notifications.

**Not a trading bot.** A thoughtful decision support system.

---

## Features

- Daily signals: **INVEST / HOLD / SKIP** for your chosen assets
- 50-day MA trend filter + XGBoost confidence scoring
- Smart SIP timing (best entry window detection)
- Portfolio logbook with P&L tracking
- Historical backtester with realistic fees
- Google OAuth login
- Email + Telegram notifications
- Fully open source & self-hostable

---

## Tech Stack

- **Frontend**: React + Vite + TailwindCSS + Recharts
- **Backend**: Python + FastAPI
- **Database**: Supabase (Postgres)
- **AI**: XGBoost
- **Data**: CoinGecko API
- **Notifications**: SendGrid + Telegram

---

## Quick Start (Local Development)

### Prerequisites
- Python 3.10+
- Node.js 18+
- Supabase account (free)
- SendGrid account (optional for emails)
- Telegram Bot (optional)

### Backend Setup

```bash
cd backend
cp .env.example .env
# Fill in your Supabase & API keys

pip install -r requirements.txt
uvicorn main:app --reload
```

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

### Database

1. Create a new Supabase project
2. Run the SQL schema (from `plan.md` or backend scripts)
3. Enable Google OAuth in Auth settings

### Seed Historical Data

```bash
cd backend
python scripts/seed_historical_data.py
```

---

## Project Structure

See detailed structure in `plan.md`.

---

## Core Concepts

### Signal Logic
1. **MA Filter**: Price must be above 50-day moving average
2. **AI Confidence**: XGBoost model predicts short-term direction
3. **Risk Rules**: Applied based on user preference
4. **Final Signal**:
   - INVEST: MA green + high confidence
   - HOLD: MA green + low confidence
   - SKIP: Below MA

### SIP Timing
- Detects good entry points within the month
- Optional double-capital next month after full skip

### Risk Management
- Max 4 assets
- -8% stop-loss alerts
- Fixed fees & slippage in backtests

---

## Development Phases

Refer to `plan.md` for complete phased roadmap.

**Current Priority**: Complete Phase 1 (Data + Strategy) → Phase 3 (Backend API).

---

## Deployment

- **Frontend**: GitHub Pages (static)
- **Backend**: Railway / Render (Docker)
- Scheduler: Platform cron jobs for daily signals

---

## Contributing

1. Fork the repo
2. Create feature branch
3. Follow backend/frontend structure
4. Test thoroughly (especially backtest accuracy)
5. Submit PR

---

## Disclaimer

This project is for educational and personal use.  
**Crypto is high risk.** Past performance ≠ future results.  
Always do your own research. The system provides suggestions only.

---

## License

MIT

---

**Built with ❤️ for disciplined crypto investors.**

*Last updated: June 2026*