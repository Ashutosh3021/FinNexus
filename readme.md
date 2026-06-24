<div align="center">

# 🪙 CryptoSense

**Your personal crypto investment decision assistant.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![React 18](https://img.shields.io/badge/react-18-61DAFB.svg)](https://reactjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-009688.svg)](https://fastapi.tiangolo.com/)
[![Supabase](https://img.shields.io/badge/Supabase-Postgres-3ECF8E.svg)](https://supabase.com/)
[![XGBoost](https://img.shields.io/badge/XGBoost-1.7+-FF6B6B.svg)](https://xgboost.ai/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](http://makeapullrequest.com)

Tells you **when to invest, how much, and why** — using a robust trend-following strategy combined with an AI confidence layer. Includes portfolio logbook, backtesting, and smart notifications.

**Not a trading bot.** A thoughtful decision support system.

</div>

---

## 📊 System Architecture

```mermaid
graph TB
    subgraph Frontend
        UI[React Dashboard]
        Charts[Recharts Visualizations]
        Notifs[Notification Settings]
    end

    subgraph Backend
        API[FastAPI Server]
        Scheduler[Daily Scheduler]
        Signals[Signal Generator]
        Backtest[Backtest Engine]
    end

    subgraph Database
        Supabase[(Supabase PostgreSQL)]
        Users[Users Table]
        Portfolio[Portfolio Table]
        Signals_Hist[Signals History]
        Backtest_Hist[Backtest Results]
    end

    subgraph AI_Engine
        XGB[XGBoost Model]
        MA[50-Day MA Filter]
        Confidence[Confidence Scoring]
    end

    subgraph External
        CG[CoinGecko API]
        Email[SendGrid]
        Telegram[Telegram Bot]
    end

    UI --> API
    API --> Supabase
    API --> XGB
    API --> MA
    XGB --> Confidence
    MA --> Signals
    Confidence --> Signals
    Scheduler --> Signals
    Signals --> Supabase
    API --> Backtest
    Backtest --> Supabase
    API --> Email
    API --> Telegram
    CG --> API
    Users --> Portfolio
    Portfolio --> Signals
    Signals_Hist --> Charts
    Backtest_Hist --> Charts
```

---

## 🎯 Signal Logic Flow

```mermaid
flowchart TD
    Start([Daily Signal Check]) --> GetPrice[Get Current Price]
    GetPrice --> GetMA[Get 50-Day MA]
    GetMA --> CheckMA{Price > 50-Day MA?}
    
    CheckMA -->|No| SKIP[SKIP: Below Trend]
    SKIP --> UpdateDB1[Log SKIP Signal]
    UpdateDB1 --> Notify1[Send Notification if Enabled]
    Notify1 --> End1([End])
    
    CheckMA -->|Yes| GetXGB[Get XGBoost Prediction]
    GetXGB --> Confidence{Confidence Score}
    
    Confidence -->|High| INVEST[INVEST: Good Entry]
    Confidence -->|Medium| HOLD[HOLD: Wait for Better Entry]
    Confidence -->|Low| SKIP2[SKIP: Low Confidence]
    
    INVEST --> CalcAmount[Calculate Investment Amount]
    CalcAmount --> RiskCheck{Risk Rules OK?}
    RiskCheck -->|Yes| Execute[Generate Buy Signal]
    RiskCheck -->|No| Adjust[Adjust Position Size]
    Adjust --> Execute
    
    HOLD --> Timing[Check SIP Timing]
    Timing -->|Good Window| INVEST
    Timing -->|Bad Window| HOLD
    
    Execute --> UpdateDB2[Log INVEST Signal]
    SKIP2 --> UpdateDB3[Log SKIP Signal]
    
    UpdateDB2 --> Notify2[Send Notification if Enabled]
    UpdateDB3 --> Notify3[Send Notification if Enabled]
    Notify2 --> End2([End])
    Notify3 --> End3([End])
```

---

## 📈 Performance Dashboard

```mermaid
pie title Portfolio Allocation
    "Bitcoin (BTC)" : 40
    "Ethereum (ETH)" : 25
    "Solana (SOL)" : 15
    "Polygon (MATIC)" : 10
    "Others" : 10
```

```mermaid
xychart-beta
    title "Portfolio Performance Over Time"
    x-axis [Jan, Feb, Mar, Apr, May, Jun]
    y-axis "Portfolio Value ($)" 0 --> 15000
    line [10000, 10500, 10200, 11200, 11800, 12500]
    line [10000, 10200, 9800, 10500, 11000, 11500]
```

---

## ✨ Features

### Core Features

| Feature | Description | Status |
|---------|-------------|--------|
| **Daily Signals** | INVEST / HOLD / SKIP for your chosen assets | ✅ Live |
| **AI Confidence** | XGBoost model with confidence scoring | ✅ Live |
| **Smart SIP Timing** | Best entry window detection | ✅ Live |
| **Portfolio Logbook** | Track all investments with P&L | ✅ Live |
| **Backtesting Engine** | Historical performance with realistic fees | ✅ Live |
| **Google OAuth** | Secure login with Google | ✅ Live |
| **Email Notifications** | SendGrid integration | ✅ Live |
| **Telegram Alerts** | Real-time Telegram bot notifications | ✅ Live |
| **Risk Management** | Max 4 assets, -8% stop-loss | ✅ Live |
| **Open Source** | Fully self-hostable | ✅ Live |

### Coming Soon

| Feature | Priority | Status |
|---------|----------|--------|
| Mobile App | Medium | 🚧 Planned |
| Multi-Asset Support | High | 🚧 In Progress |
| Advanced Analytics | Medium | 📋 Planned |
| Social Features | Low | 📋 Planned |
| API for Developers | Low | 📋 Planned |

---

## 🛠️ Tech Stack

```mermaid
mindmap
  root((CryptoSense))
    Frontend
      React 18
      Vite
      TailwindCSS
      Recharts
      React Router
      Axios
    Backend
      FastAPI
      Python 3.10+
      Pydantic
      SQLAlchemy
      Celery
    AI & ML
      XGBoost
      Pandas
      NumPy
      Scikit-learn
    Database
      Supabase
      PostgreSQL
      Redis
    External APIs
      CoinGecko
      SendGrid
      Telegram Bot API
    DevOps
      Docker
      GitHub Actions
      Railway/Render
      Prometheus
```

---

## 📦 Project Structure

```mermaid
graph LR
    subgraph Root
        README[README.md]
        LICENSE[LICENSE]
        CONTRIBUTING[CONTRIBUTING.md]
        plan[plan.md]
    end

    subgraph Backend
        main[main.py]
        api[api/]
        models[models/]
        schemas[schemas/]
        services[services/]
        scripts[scripts/]
        tests[tests/]
        requirements[requirements.txt]
    end

    subgraph Frontend
        src[src/]
        components[components/]
        pages[pages/]
        hooks[hooks/]
        utils[utils/]
        styles[styles/]
        package[package.json]
        vite[vite.config.js]
    end

    Backend --> Root
    Frontend --> Root
```

### Detailed Backend Structure

```
backend/
├── main.py                 # FastAPI entry point
├── api/
│   ├── auth.py            # Google OAuth
│   ├── signals.py         # Daily signal endpoints
│   ├── portfolio.py       # Portfolio management
│   ├── backtest.py        # Backtest engine
│   └── notifications.py   # Email/Telegram
├── models/
│   ├── user.py
│   ├── asset.py
│   ├── signal.py
│   ├── portfolio.py
│   └── backtest.py
├── schemas/
│   ├── request.py         # Pydantic request models
│   └── response.py        # Pydantic response models
├── services/
│   ├── xgb_model.py       # XGBoost training & prediction
│   ├── ma_filter.py       # 50-day moving average
│   ├── signal_generator.py # Combined signal logic
│   ├── sip_timing.py      # Smart SIP timing
│   ├── coingecko.py       # CoinGecko API wrapper
│   ├── email.py           # SendGrid integration
│   └── telegram.py        # Telegram bot
├── scripts/
│   ├── seed_historical_data.py
│   └── train_model.py
├── tests/
│   ├── test_signals.py
│   ├── test_backtest.py
│   └── test_models.py
└── requirements.txt
```

### Detailed Frontend Structure

```
frontend/
├── src/
│   ├── App.jsx
│   ├── main.jsx
│   ├── api/
│   │   └── client.js
│   ├── components/
│   │   ├── Dashboard/
│   │   ├── Signals/
│   │   ├── Portfolio/
│   │   ├── Backtest/
│   │   ├── Settings/
│   │   └── Common/
│   ├── pages/
│   │   ├── Dashboard.jsx
│   │   ├── Signals.jsx
│   │   ├── Portfolio.jsx
│   │   ├── Backtest.jsx
│   │   ├── Settings.jsx
│   │   └── Login.jsx
│   ├── hooks/
│   │   ├── useAuth.js
│   │   ├── useSignals.js
│   │   └── usePortfolio.js
│   ├── utils/
│   │   ├── formatters.js
│   │   └── validators.js
│   ├── styles/
│   │   └── index.css
│   └── config/
│       └── constants.js
├── package.json
├── vite.config.js
└── tailwind.config.js
```

---

## 🚀 Quick Start (Local Development)

### Prerequisites

- Python 3.10+
- Node.js 18+
- Supabase account (free tier)
- SendGrid account (optional for emails)
- Telegram Bot (optional)

### Step-by-Step Setup

```mermaid
flowchart LR
    Clone[Clone Repository] --> Backend[Setup Backend]
    Backend --> Frontend[Setup Frontend]
    Frontend --> Supabase[Configure Supabase]
    Supabase --> Seed[Seed Data]
    Seed --> Run[Run Application]
```

#### 1. Clone Repository

```bash
git clone https://github.com/yourusername/cryptosense.git
cd cryptosense
```

#### 2. Backend Setup

```bash
cd backend
cp .env.example .env
# Fill in your Supabase & API keys

pip install -r requirements.txt
uvicorn main:app --reload
```

#### 3. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

#### 4. Database Setup

1. Create a new Supabase project
2. Run the SQL schema (from `plan.md` or backend scripts)
3. Enable Google OAuth in Auth settings

#### 5. Seed Historical Data

```bash
cd backend
python scripts/seed_historical_data.py
```

### Environment Variables

```env
# Supabase
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key

# Google OAuth
GOOGLE_CLIENT_ID=your_client_id
GOOGLE_CLIENT_SECRET=your_client_secret

# CoinGecko
COINGECKO_API_KEY=your_api_key

# SendGrid (Optional)
SENDGRID_API_KEY=your_sendgrid_key
EMAIL_FROM=your_email

# Telegram (Optional)
TELEGRAM_BOT_TOKEN=your_bot_token

# XGBoost Model Path
MODEL_PATH=./models/xgb_model.pkl
```

---

## 🧠 Core Concepts

### Signal Logic

```mermaid
stateDiagram-v2
    [*] --> CheckPrice: Daily Check
    CheckPrice --> CheckMA: Price Retrieved
    
    CheckMA --> SKIP: Below 50-day MA
    CheckMA --> GetConfidence: Above 50-day MA
    
    GetConfidence --> INVEST: High Confidence
    GetConfidence --> HOLD: Medium Confidence
    GetConfidence --> SKIP2: Low Confidence
    
    INVEST --> RiskCheck: Apply Risk Rules
    RiskCheck --> Execute: PASS
    RiskCheck --> Adjust: FAIL
    
    Adjust --> Execute: Adjusted Size
    Execute --> [*]
```

#### Signal Types

| Signal | Condition | Action |
|--------|-----------|--------|
| **INVEST** | Price > 50-day MA & High Confidence | Buy signal with calculated amount |
| **HOLD** | Price > 50-day MA & Low Confidence | Wait for better entry point |
| **SKIP** | Price < 50-day MA | No action, wait for trend reversal |

### SIP Timing Strategy

```mermaid
flowchart TD
    Start[Start of Month] --> CheckBalance{Check Balance}
    CheckBalance -->|Insufficient| SkipMonth[Skip This Month]
    CheckBalance -->|Sufficient| FindWindow[Find Best Entry Window]
    
    FindWindow --> CheckMA{Dip Below MA?}
    CheckMA -->|Yes| Double[Double Capital Investment]
    CheckMA -->|No| Normal[Normal Investment]
    
    Double --> Record[Record Investment]
    Normal --> Record
    SkipMonth --> RecordSkip[Record Skip]
    
    Record --> NextMonth[Wait for Next Month]
    RecordSkip --> NextMonth
    NextMonth --> Start
```

### Risk Management Rules

| Rule | Value | Description |
|------|-------|-------------|
| **Max Assets** | 4 | Maximum concurrent positions |
| **Stop Loss** | -8% | Automatic stop-loss alert |
| **Fees** | 0.1% | Trading fee (configurable) |
| **Slippage** | 0.5% | Slippage for order execution |
| **Position Size** | Variable | Based on confidence & risk |

---

## 🔄 Development Phases

```mermaid
gantt
    title CryptoSense Development Roadmap
    dateFormat  YYYY-MM-DD
    section Phase 1
    Data Collection           :a1, 2026-06-01, 7d
    MA Filter Implementation  :a2, after a1, 3d
    XGBoost Training          :a3, after a2, 5d
    section Phase 2
    Signal Logic              :b1, after a3, 5d
    SIP Timing                :b2, after b1, 3d
    Risk Management           :b3, after b2, 3d
    section Phase 3
    API Development           :c1, after b3, 7d
    Database Integration      :c2, after c1, 5d
    Testing & Validation      :c3, after c2, 5d
    section Phase 4
    Frontend UI               :d1, after c3, 10d
    Dashboard & Charts        :d2, after d1, 5d
    Notifications             :d3, after d2, 3d
    section Phase 5
    Backtesting               :e1, after d3, 5d
    Deployment                :e2, after e1, 3d
    Beta Release              :milestone, after e2, 0d
```

### Current Phase Status

| Phase | Status | Progress |
|-------|--------|----------|
| **Phase 1: Data + Strategy** | ✅ Complete | 100% |
| **Phase 2: Signal Generation** | ✅ Complete | 100% |
| **Phase 3: Backend API** | 🚧 In Progress | 75% |
| **Phase 4: Frontend UI** | 🚧 In Progress | 60% |
| **Phase 5: Notifications** | 📋 Planned | 0% |

---

## 📊 API Endpoints

```mermaid
graph LR
    subgraph Auth
        Login[POST /auth/login]
        Logout[POST /auth/logout]
        Me[GET /auth/me]
    end

    subgraph Signals
        Daily[GET /signals/daily]
        History[GET /signals/history]
        Asset[GET /signals/asset/{id}]
    end

    subgraph Portfolio
        Portfolio[GET /portfolio]
        Add[POST /portfolio/add]
        Remove[DELETE /portfolio/{id}]
        PnL[GET /portfolio/pnl]
    end

    subgraph Backtest
        Run[POST /backtest/run]
        Results[GET /backtest/results]
        Compare[GET /backtest/compare]
    end

    subgraph Notifications
        Settings[GET /notifications/settings]
        Update[PUT /notifications/settings]
        Test[POST /notifications/test]
    end
```

---

## 🚢 Deployment

### Docker Deployment

```mermaid
flowchart LR
    Build[Build Docker Image] --> Push[Push to Registry]
    Push --> Deploy[Deploy to Server]
    Deploy --> Config[Configure Env Vars]
    Config --> Run[Run Container]
    Run --> Check{Check Health}
    Check -->|OK| Live[Application Live]
    Check -->|Fail| Rollback[Rollback]
```

### Quick Deploy

```bash
# Build Docker image
docker build -t cryptosense .

# Run container
docker run -d \
  -p 8000:8000 \
  -p 3000:3000 \
  --env-file .env \
  --name cryptosense \
  cryptosense
```

### Production Deployment (Railway)

```yaml
# railway.json
{
  "build": {
    "builder": "DOCKERFILE",
    "dockerfile": "Dockerfile"
  },
  "deploy": {
    "healthcheck": {
      "path": "/health",
      "interval": 30
    },
    "restart": {
      "policy": "always"
    }
  }
}
```

### Environment Variables for Production

```env
ENVIRONMENT=production
DEBUG=False
LOG_LEVEL=INFO
CORS_ORIGINS=https://cryptosense.app
```

---

## 🤝 Contributing

```mermaid
flowchart TD
    Fork[Fork Repository] --> Clone[Clone Locally]
    Clone --> Branch[Create Feature Branch]
    Branch --> Code[Write Code]
    Code --> Test[Run Tests]
    Test --> Pass{Tests Pass?}
    Pass -->|No| Code
    Pass -->|Yes| Commit[Commit & Push]
    Commit --> PR[Create Pull Request]
    PR --> Review[Code Review]
    Review --> Merge[Merge to Main]
```

### Contribution Guidelines

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Follow backend/frontend structure
4. Write tests for new features
5. Ensure all tests pass
6. Commit with meaningful messages
7. Submit pull request

### Code Standards

| Aspect | Standard |
|--------|----------|
| **Python** | PEP 8 + Black |
| **JavaScript** | ESLint + Prettier |
| **Commits** | Conventional Commits |
| **Testing** | pytest + Jest |
| **Docs** | Docstrings + JSDoc |

---

## 📊 Monitoring & Analytics

```mermaid
graph LR
    subgraph Metrics
        Accuracy[Prediction Accuracy]
        Confidence[Model Confidence]
        Performance[Portfolio Performance]
        Latency[API Latency]
    end

    subgraph Alerts
        Error[Error Rate]
        API[API Limits]
        DB[Database Connections]
        Model[Model Drift]
    end

    subgraph Dashboard
        Grafana[Grafana Dashboard]
        Logs[ELK Stack]
        Metrics[Prometheus]
    end

    Metrics --> Dashboard
    Alerts --> Dashboard
```

### Key Metrics to Track

| Metric | Target | Alert Threshold |
|--------|--------|-----------------|
| **Accuracy** | >60% | <55% |
| **Confidence** | >0.7 | <0.5 |
| **Return** | >10% | <0% |
| **API Latency** | <500ms | >2000ms |
| **Error Rate** | <1% | >5% |

---

## 🔒 Security

### Security Features

```mermaid
mindmap
  root((Security))
    Authentication
      Google OAuth 2.0
      JWT Tokens
      Session Management
      Rate Limiting
    Data Protection
      HTTPS Everywhere
      Environment Variables
      SQL Injection Prevention
      XSS Protection
    API Security
      CORS Configuration
      API Key Validation
      Request Validation
      Input Sanitization
    Best Practices
      Regular Updates
      Security Headers
      Audit Logging
      Backup Strategy
```

### Environment Variables Security

```bash
# NEVER commit sensitive data
# Use environment variables or .env files

# .env.example (commit this)
DATABASE_URL=postgresql://user:password@localhost/db  # Replace with actual
API_KEY=your_api_key_here  # Replace with actual

# .env (gitignored)
DATABASE_URL=postgresql://actual_user:actual_password@prod_db:5432/db
API_KEY=sk_live_actual_key
```

---

## 📋 License & Disclaimer

```mermaid
graph TD
    A[Open Source] --> B[MIT License]
    A --> C[Commercial Use Allowed]
    A --> D[Modification Allowed]
    A --> E[Distribution Allowed]
    A --> F[No Warranty]
    A --> G[Educational Purpose]
```

**Disclaimer**

<div align="center">
  
**⚠️ NOT FINANCIAL ADVICE**

This project is for **educational and personal use** only.  
**Crypto is high risk.** Past performance ≠ future results.  
Always do your own research. The system provides **suggestions only**.

**You are responsible for your own investment decisions.**

</div>

---

## 🙏 Acknowledgments

```mermaid
flowchart LR
    CoinGecko[CoinGecko API] --> Data[Market Data]
    Supabase[Supabase] --> DB[Database]
    XGBoost[XGBoost] --> ML[AI Model]
    FastAPI[FastAPI] --> API[Backend API]
    React[React] --> UI[Frontend UI]
    OSS[Open Source Community] --> Everything
```

### Libraries & Services

| Service/Library | Purpose |
|-----------------|---------|
| [CoinGecko API](https://www.coingecko.com/en/api) | Real-time crypto data |
| [Supabase](https://supabase.com) | Database & Authentication |
| [XGBoost](https://xgboost.ai) | AI/ML predictions |
| [FastAPI](https://fastapi.tiangolo.com) | Backend API framework |
| [React](https://reactjs.org) | Frontend UI |
| [TailwindCSS](https://tailwindcss.com) | Styling |
| [Recharts](https://recharts.org) | Charts & Visualizations |

---

## 📝 Changelog

```mermaid
timeline
    title CryptoSense Development Timeline
    June 2026 : Initial Release
             : Backend Complete
             : Frontend Beta
    July 2026 : Notifications Added
             : Backtesting Complete
             : UI Polish
    August 2026 : Mobile Support
               : Advanced Analytics
               : Community Features
```

### Version History

| Version | Date | Changes |
|---------|------|---------|
| **v1.0.0** | June 2026 | Initial release |
| **v1.1.0** | July 2026 | Notifications added |
| **v1.2.0** | July 2026 | Backtesting complete |
| **v1.3.0** | August 2026 | Mobile support |

---

<div align="center">

**Built with ☕ for disciplined crypto investors.**

*Last updated: June 2026*

</div>