# FinNexus - Financial Learning & Virtual Trading Platform

A production-ready fintech education platform built with Next.js 16, React 19, and Tailwind CSS. Learn financial concepts and practice trading with $124,500 in virtual funds.

## 📁 Project Structure

```
FinNexus/
├── app/
│   ├── (auth)/                      # Authentication routes
│   │   ├── login/page.jsx          # Login page
│   │   └── onboarding/page.jsx     # Level selection
│   ├── dashboard/
│   │   ├── layout.jsx              # Dashboard layout with context providers
│   │   └── page.jsx                # Main dashboard
│   ├── learn/
│   │   ├── page.jsx                # Learning center
│   │   └── [id]/page.jsx           # Individual lesson with quiz
│   ├── playground/page.jsx         # Prediction playground
│   ├── portfolio/page.jsx          # Portfolio management
│   ├── news/page.jsx               # Financial news & AI analysis
│   ├── advisor/page.jsx            # AI financial advisor chatbot
│   ├── page.jsx                    # Homepage
│   ├── layout.tsx                  # Root layout
│   └── globals.css                 # Global styles
├── components/
│   └── layout/
│       ├── Layout.jsx              # Main layout wrapper
│       ├── Navbar.jsx              # Top navigation bar
│       └── Sidebar.jsx             # Collapsible sidebar
├── context/
│   ├── UserContext.jsx             # User data & balance management
│   ├── PortfolioContext.jsx        # Holdings & portfolio metrics
│   ├── PlaygroundContext.jsx       # Prediction history & stats
│   └── NewsContext.jsx             # News feed & filtering
├── lib/
│   ├── mockData.js                 # All mock/sample data
│   └── utils.js                    # Helper functions
├── public/                         # Static assets
├── tailwind.config.js              # Tailwind configuration
├── next.config.mjs                 # Next.js configuration
└── package.json                    # Dependencies
```

## 🚀 Features

### Dashboard
- Real-time portfolio overview
- Win rate statistics
- Current trading streak
- Top holdings table
- Recent predictions
- Quick action buttons

### Learning Center
- 5 comprehensive lessons (Beginner to Advanced)
- Progress tracking with XP system
- Interactive quizzes with instant feedback
- Level-based learning paths
- Recommended lessons

### Prediction Playground
- Virtual asset trading (Stocks, Crypto, Commodities, ETFs)
- Risk-free prediction testing
- Win/loss tracking
- Streak counting
- Detailed prediction history

### Portfolio Management
- Complete holdings management
- Real-time P&L calculations
- Asset type distribution
- Buy/sell price tracking
- Type-based color coding

### Financial News
- Real-time news feed
- Sentiment analysis (Positive/Negative/Neutral)
- AI-powered analysis for each news item
- Category filtering (Macro, Earnings, Crypto, Commodities)
- Impact scoring

### AI Advisor
- 24/7 financial advice chatbot
- Simulated AI responses
- Message history
- Real-time typing indicator

### Sidebar Navigation
- Collapsible on desktop
- Bottom tab bar on mobile
- Current level badge
- XP progress bar
- Active link highlighting

## 🎨 Design System

### Colors
- **Primary**: Blue 600 (#2563eb) - Primary actions, accents
- **Background**: Slate 900 (#0f172a) - Dark theme base
- **Cards**: Slate 800 (#1e293b) - Content containers
- **Text**: Slate 100 (#f1f5f9) - Primary text
- **Success**: Green 400 (#4ade80) - Positive metrics
- **Alert**: Red 400 (#f87171) - Negative metrics

### Typography
- **Font**: Geist (sans-serif)
- **Headings**: Bold weights (600-700)
- **Body**: Regular weight (400)

## 📦 State Management

### Context API with localStorage Persistence
- **UserContext**: User profile, level, balance, XP
- **PortfolioContext**: Holdings, P&L calculations
- **PlaygroundContext**: Predictions, win rate, streaks
- **NewsContext**: News feed, category filtering

All contexts automatically persist to localStorage and hydrate on app load.

## 🔐 Authentication Flow

1. **Login Page** - Demo login (alex@finnexus.com / demo123)
2. **Onboarding** - Select experience level (Beginner/Intermediate/Advanced)
3. **Dashboard** - Access all features after authentication

## 💾 Mock Data

Comprehensive mock data included:
- 6 portfolio holdings (stocks, crypto, commodities, ETFs)
- 8 prediction history records
- 6 news items with AI analysis
- 5 lessons with quizzes
- Macro economic indicators

## 🛠️ Technologies

- **Framework**: Next.js 16 (App Router)
- **React**: 19.2.4
- **Styling**: Tailwind CSS 4.2
- **Icons**: Lucide React
- **Charts**: Recharts
- **UI Components**: Shadcn/ui
- **State**: React Context API
- **Package Manager**: pnpm

## 📖 Getting Started

### Installation

```bash
# Clone the repository
git clone <repo-url>
cd finnexus

# Install dependencies
pnpm install

# Run development server
pnpm dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

### Demo Account
- Email: alex@finnexus.com
- Password: demo123
- Virtual Balance: $124,500

## 🔄 Available Routes

### Public Routes
- `/` - Homepage
- `/(auth)/login` - Login page
- `/(auth)/onboarding` - Level selection

### Protected Routes (require layout)
- `/dashboard` - Main dashboard
- `/learn` - Learning center
- `/learn/[id]` - Individual lesson
- `/playground` - Prediction playground
- `/portfolio` - Portfolio management
- `/news` - Financial news
- `/advisor` - AI advisor chatbot

## 📱 Responsive Design

- Mobile-first approach
- Sidebar becomes bottom tab bar on mobile (<768px)
- Responsive grid layouts
- Touch-friendly buttons and inputs
- Optimized for all screen sizes

## 🎓 Learning Modules

1. **Introduction to Stock Markets** (Beginner)
2. **Technical Analysis Basics** (Intermediate)
3. **Portfolio Diversification** (Intermediate)
4. **Risk Management Strategies** (Intermediate)
5. **Cryptocurrency Fundamentals** (Intermediate)

Each lesson includes:
- Detailed content
- Multiple-choice quiz
- Progress tracking
- Completion badges

## 📊 Prediction System

Users can:
- Select from 4 assets (AAPL, BTC, SPY, MSFT)
- Predict price direction (Up/Down)
- Set virtual bet amount
- Track win rate and streak
- View detailed history

## 🔄 Context API Hooks

```javascript
// User Context
const { virtualBalance, updateBalance, level, xp, updateXP } = useUser();

// Portfolio Context
const { holdings, totalValue, totalPnL, addHolding, removeHolding } = usePortfolio();

// Playground Context
const { winRate, totalRounds, streak, submitPrediction } = usePlayground();

// News Context
const { filteredNews, setSelectedCategory, getNewsByCategory } = useNews();
```

## 🎨 Customization

### Colors
Edit `tailwind.config.js` to customize:
- Primary brand color
- Neutral palette
- Accent colors

### Mock Data
Edit `lib/mockData.js` to add:
- More portfolio holdings
- Additional lessons
- Extended news feed
- New prediction records

### Layout
Edit `components/layout/Layout.jsx` to modify:
- Sidebar width
- Navbar height
- Color scheme

## 📝 Notes

- This is an educational platform for demonstration purposes
- Virtual trading is simulated - not connected to real markets
- All data persists to localStorage (browser storage)
- No backend API required for basic functionality
- Can be extended with real API integration

## 🚀 Deployment

Deploy to Vercel:

```bash
# Push to GitHub
git push origin main

# Deploy from Vercel dashboard
# Connect your GitHub repository
# Vercel will auto-deploy on push
```

## 📄 License

This project is open source and available under the MIT License.

## 🤝 Contributing

Feel free to fork this project and submit pull requests for improvements!

---

**FinNexus** - Learn & Trade Virtual Markets | Built with Next.js & React
