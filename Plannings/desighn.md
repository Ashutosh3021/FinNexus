# CryptoSense — Frontend Design Document

---

## Design Philosophy

**Theme:** Dark, data-dense, trustworthy — like a Bloomberg terminal built for regular people.

**Aesthetic Direction:** Financial-grade dark UI. Deep navy/charcoal backgrounds, sharp white typography, electric green for positive signals, amber for warnings, red for negatives. No gradients on gradients. No purple AI aesthetic. Feels like something you'd trust with real money.

**One thing users will remember:** The signal card — a single clean card that says INVEST / HOLD / SKIP with a confidence ring. Instantly scannable. No noise.

**Font Pairing:**
- Display / Numbers: `IBM Plex Mono` — monospaced, financial, precise
- Body / Labels: `DM Sans` — clean, readable, modern without being generic

**Color Palette:**
```
Background:       #0A0F1E   (deep navy black)
Surface:          #111827   (card background)
Surface elevated: #1A2235   (hover states, modals)
Border:           #1E293B   (subtle dividers)

Text primary:     #F1F5F9   (near white)
Text secondary:   #94A3B8   (muted labels)
Text muted:       #475569   (disabled, timestamps)

Signal green:     #10B981   (INVEST)
Signal amber:     #F59E0B   (HOLD)
Signal red:       #EF4444   (SKIP / loss)

Accent blue:      #3B82F6   (links, active states)
Accent glow:      #10B98130 (green glow on cards)
```

---

## Page 1 — Landing Page (`/`)

**Purpose:** Convert visitors to sign up. Public-facing. No data shown.

### Layout
```
┌─────────────────────────────────────────────┐
│  NAVBAR: Logo (left)        [Sign in] (right)│
├─────────────────────────────────────────────┤
│                                              │
│  HERO (centered, full viewport height)       │
│                                              │
│  Small tag: "AI-Powered Crypto Decisions"   │
│                                              │
│  H1: "Stop Guessing.                        │
│       Start Investing Smart."               │
│                                              │
│  Subtext: "CryptoSense watches the market   │
│  for you. Tells you exactly when to invest, │
│  when to hold, and when to walk away."      │
│                                              │
│  [Get Started Free — Google Sign In]         │
│                                              │
│  ↓ scroll indicator                          │
│                                              │
├─────────────────────────────────────────────┤
│  SIGNAL PREVIEW (3 mock cards, side by side) │
│  BTC: INVEST 74%  ETH: HOLD 61%  SOL:SKIP   │
├─────────────────────────────────────────────┤
│  HOW IT WORKS (3 steps, horizontal)          │
│  1. Pick assets   2. Set capital   3. Get   │
│     & risk            & risk          alerts │
├─────────────────────────────────────────────┤
│  FOOTER: minimal — links + "Not financial   │
│  advice" disclaimer                          │
└─────────────────────────────────────────────┘
```

### Component Details
- Hero background: subtle animated grid mesh (CSS only, dark navy lines on black)
- H1 font size: 64px display, IBM Plex Mono, white
- CTA button: solid electric green, black text, no border radius > 6px
- Signal preview cards: semi-transparent, blurred, slight glow — teaser of the real product
- Scroll indicator: thin animated line, pulses downward

---

## Page 2 — Onboarding Wizard (`/onboarding`)

**Purpose:** Collect user config after first Google login. One-time flow.

### Layout — Stepper
```
┌─────────────────────────────────────────────┐
│  Step indicator: ● ● ○ ○ ○ ○   Step 2 of 6  │
├─────────────────────────────────────────────┤
│                                              │
│  [Step content — changes per step]           │
│                                              │
├─────────────────────────────────────────────┤
│  [← Back]                    [Continue →]    │
└─────────────────────────────────────────────┘
```

### Step 1 — Choose Assets
```
"Which assets do you want to track?"
(Select 1 to 4)

┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐
│  ₿   │  │  Ξ   │  │  ◎   │  │  ◈   │
│ BTC  │  │ ETH  │  │ SOL  │  │ BNB  │
└──────┘  └──────┘  └──────┘  └──────┘
┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐
│  ✦   │  │  ●   │  │  ◆   │  │  ⬡   │
│ ADA  │  │ DOT  │  │ AVAX │  │ MATIC│
└──────┘  └──────┘  └──────┘  └──────┘

Selected assets get a green border + checkmark.
Counter: "2/4 selected"
```

### Step 2 — Trade Mode
```
"How do you plan to invest?"

┌─────────────────────┐  ┌─────────────────────┐
│  ⚡ SPOT TRADE       │  │  📈 LONG TERM        │
│                     │  │                     │
│  Buy and sell based │  │  Invest monthly,    │
│  on short signals   │  │  hold for months+   │
│                     │  │                     │
│  (weekly signals)   │  │  → If selected:     │
│                     │  │  "How long?"        │
│                     │  │  [3M] [6M] [1Y] [2Y+]│
└─────────────────────┘  └─────────────────────┘

Note: Applied per asset. If user has both BTC and ETH,
each asset gets its own mode selection.
```

### Step 3 — Capital
```
"How much will you invest per month?"

Per asset (shown for each selected asset):

BTC  [₹ ______500______]
ETH  [₹ ______300______]

Total monthly commitment: ₹800

Note shown below:
"This is for planning only. You invest manually 
 through CoinSwitch. We just track and signal."
```

### Step 4 — Risk Tolerance
```
"How should we calibrate signals for you?"

[━━━━━━━━━━━━━●━━━━━━━━━] MEDIUM (default)

○ CONSERVATIVE     ○ MODERATE     ○ AGGRESSIVE
  Invest only at     Balanced        More signals,
  high confidence    approach        more risk
  (>70%)             (>65%)          (>55%)

Visual: horizontal slider with 3 stops
Below each: plain english explanation
```

### Step 5 — SIP Mode
```
"What should we do if the market is bad this month?"

┌─────────────────────────┐  ┌─────────────────────────┐
│  🎯 FIND BEST ENTRY     │  │  💰 DOUBLE NEXT MONTH   │
│  (Recommended)          │  │                         │
│                         │  │  Skip this month.       │
│  We watch the month     │  │  Invest 2× next month   │
│  for a price dip and    │  │  when market recovers.  │
│  alert you then.        │  │                         │
│  Same ₹500, better      │  │  ⚠️ Higher risk.        │
│  price.                 │  │  Use with caution.      │
└─────────────────────────┘  └─────────────────────────┘
```

### Step 6 — Notifications
```
"Where should we send your alerts?"

Email (required):
[your@email.com ✓ from Google]

Telegram (optional but recommended):
[Connect Telegram]
  → Opens instructions: "Message @CryptoSenseBot, 
    then paste your chat ID here"
[Chat ID: ____________]

Notification frequency:
○ Every signal change (recommended)
○ Daily summary only
○ Only when it's time to invest
```

---

## Page 3 — Dashboard (`/dashboard`) — Main Home

**Purpose:** Daily signal feed. Most-visited page.

### Layout
```
┌─────────────────────────────────────────────────┐
│ NAVBAR: Logo | Dashboard Logbook Backtest     ⚙️ │
├──────────────┬──────────────────────────────────┤
│              │                                  │
│  SIDEBAR     │  MAIN CONTENT                    │
│  (240px)     │                                  │
│              │                                  │
│  Your Assets │  TODAY'S SIGNALS                 │
│  ──────────  │  ─────────────────────────────   │
│  ₿ BTC  ↑   │  [Signal Card] [Signal Card]     │
│  Ξ ETH  →   │  [Signal Card] [Signal Card]     │
│  ◎ SOL  ↑   │                                  │
│              │  PORTFOLIO SNAPSHOT              │
│  ──────────  │  ─────────────────────────────   │
│  Today       │  Total ₹4,500 → ₹5,120  +13.8%  │
│  8:00 AM     │  [Mini sparklines per asset]     │
│  Last run    │                                  │
│              │  RECENT ALERTS                   │
│  [Run Now]   │  ─────────────────────────────   │
│              │  • BTC signal changed: INVEST    │
│              │  • ETH near monthly low          │
│              │  • Monthly report ready          │
│              │                                  │
└──────────────┴──────────────────────────────────┘
```

### Signal Card Component
```
┌────────────────────────────────┐
│  ₿ BTC / USDT          Apr 20  │
│                                │
│  ┌──────────────┐              │
│  │   INVEST     │  ◉ 74%       │
│  └──────────────┘  confidence  │
│                                │
│  Trend:  ↑ Bullish             │
│  MA:     ✅ Above 50MA         │
│  Price:  ₹68,42,300            │
│                                │
│  "Strong momentum. Good        │
│   entry window this month."    │
│                                │
│  [Log a purchase]              │
└────────────────────────────────┘
```

**Signal card color coding:**
- INVEST → green left border + subtle green glow
- HOLD → amber left border
- SKIP → red left border, slightly dimmed

**Confidence ring:**
- 74% → circular SVG progress ring, filled green to 74%
- Below 50% → ring fills red
- 50-65% → fills amber

### Portfolio Snapshot
```
┌────────────────────────────────────────────────┐
│  Portfolio Overview                      [+Add] │
├──────────┬──────────┬───────────┬──────────────┤
│  Asset   │ Invested │ Current   │  P&L         │
├──────────┼──────────┼───────────┼──────────────┤
│  ₿ BTC   │ ₹2,000  │ ₹2,340   │ +17% ▲       │
│  Ξ ETH   │ ₹1,500  │ ₹1,620   │ +8%  ▲       │
│  ◎ SOL   │ ₹1,000  │ ₹1,160   │ +16% ▲       │
├──────────┼──────────┼───────────┼──────────────┤
│  Total   │ ₹4,500  │ ₹5,120   │ +13.8% ▲     │
└──────────┴──────────┴───────────┴──────────────┘
```

---

## Page 4 — Logbook (`/logbook`)

**Purpose:** Manual portfolio tracker. User records every purchase.

### Layout
```
┌─────────────────────────────────────────────────┐
│  LOGBOOK                           [+ Add Entry] │
├─────────────────────────────────────────────────┤
│                                                  │
│  SUMMARY ROW                                     │
│  ┌──────────┬──────────┬──────────┬───────────┐ │
│  │ Total    │ Current  │ Total    │ Best       │ │
│  │ Invested │ Value    │ Return   │ Performer  │ │
│  │ ₹4,500  │ ₹5,120  │ +13.8%  │ BTC +17%  │ │
│  └──────────┴──────────┴──────────┴───────────┘ │
│                                                  │
│  ENTRIES TABLE                                   │
│  ┌────────────────────────────────────────────┐  │
│  │ Asset │ Date  │ Bought │ Qty  │ Now  │ P&L │  │
│  │ BTC   │Apr 5  │₹68.2L  │0.029 │₹72.1L│+5% │  │
│  │ ETH   │Mar 28 │₹2.8L   │0.53  │₹3.0L │+8% │  │
│  │ BTC   │Mar 1  │₹65.1L  │0.030 │₹72.1L│+10%│  │
│  └────────────────────────────────────────────┘  │
│                                                  │
│  [Export CSV]              [View Monthly Report] │
└─────────────────────────────────────────────────┘
```

### Add Entry Modal
```
┌──────────────────────────────────┐
│  Log a Purchase            [✕]   │
├──────────────────────────────────┤
│                                  │
│  Asset:        [BTC ▾]           │
│  Date bought:  [Apr 20, 2025]    │
│  Price bought: [₹ _____________] │
│  Amount (₹):   [₹ _____________] │
│  Notes:        [optional]        │
│                                  │
│  Auto-calculated:                │
│  Quantity: 0.0073 BTC            │
│                                  │
│  [Cancel]          [Save Entry]  │
└──────────────────────────────────┘
```

### Stop Loss Alert Visual
If any entry is down >8% from purchase:
```
┌────────────────────────────────────────────┐
│  ⚠️  SOL is down 9.2% from your entry     │
│  Bought: ₹12,400  |  Now: ₹11,256         │
│  Consider reviewing this position.         │
└────────────────────────────────────────────┘
```
Shown as a yellow/red banner above the table row.

---

## Page 5 — Backtest (`/backtest`)

**Purpose:** See how the strategy performed historically.

### Layout
```
┌──────────────────────────────────────────────────┐
│  BACKTEST SIMULATOR                               │
├───────────────────┬──────────────────────────────┤
│  CONFIG (left)    │  RESULTS (right)              │
│                   │                               │
│  Asset: [BTC ▾]  │  Running on: BTC              │
│                   │  Period: Jan 2022 – Dec 2023  │
│  From: [Jan 2022] │                               │
│  To:   [Dec 2023] │  ┌─────────────────────────┐ │
│                   │  │  RETURNS OVER TIME CHART │ │
│  Capital: [₹500/m]│  │  (line: strategy vs      │ │
│                   │  │   buy-and-hold)           │ │
│  Include fees: ✅ │  └─────────────────────────┘ │
│  Slippage:    ✅  │                               │
│                   │  ┌────────┬────────┬────────┐│
│  [Run Backtest]   │  │ Return │Win Rate│Max DD  ││
│                   │  │ +42.3% │ 61%    │ -18.2% ││
│                   │  └────────┴────────┴────────┘│
│                   │                               │
│                   │  TRADE LOG                    │
│                   │  Date     Signal   Result     │
│                   │  Jan 5    INVEST   +4.2%      │
│                   │  Feb 3    SKIP     (held cash)│
│                   │  Feb 28   INVEST   -2.1%      │
└───────────────────┴──────────────────────────────┘
```

**Chart details:**
- Two lines: strategy returns (green) vs buy-and-hold (grey dashed)
- X-axis: months
- Y-axis: cumulative return %
- Hover tooltip shows: date, signal, return that period

---

## Page 6 — Settings (`/settings`)

### Layout
```
┌──────────────────────────────────────────────────┐
│  SETTINGS                                         │
├──────────────────────────────────────────────────┤
│                                                   │
│  PROFILE                                          │
│  ─────────────────────────────────               │
│  [Google avatar]  Your Name                      │
│                   your@gmail.com                 │
│                                                   │
│  ASSETS & CAPITAL                                 │
│  ─────────────────────────────────               │
│  BTC    ₹500/month   Spot     [Edit] [Remove]    │
│  ETH    ₹300/month   Long(1Y) [Edit] [Remove]    │
│  [+ Add asset]                                   │
│                                                   │
│  RISK TOLERANCE                                   │
│  ─────────────────────────────────               │
│  ○ Conservative   ● Moderate   ○ Aggressive      │
│                                                   │
│  SIP MODE                                         │
│  ─────────────────────────────────               │
│  ● Best entry this month                         │
│  ○ Double next month (higher risk)               │
│                                                   │
│  NOTIFICATIONS                                    │
│  ─────────────────────────────────               │
│  Email:    your@gmail.com    [✅ Active]          │
│  Telegram: @username         [✅ Connected]       │
│  Frequency: [Every signal change ▾]              │
│                                                   │
│  [Save Changes]                                   │
└──────────────────────────────────────────────────┘
```

---

## Component Library

### Buttons
```
Primary:    bg-green-500  text-black   font-semibold  px-6 py-3
Secondary:  bg-transparent border border-slate-600 text-slate-300
Danger:     bg-red-500/10 text-red-400 border border-red-500/30
```

### Cards
```
bg-[#111827]
border border-[#1E293B]
rounded-lg
p-6
hover: border-slate-600 transition
```

### Badges
```
INVEST:  bg-green-500/15  text-green-400  border border-green-500/30
HOLD:    bg-amber-500/15  text-amber-400  border border-amber-500/30
SKIP:    bg-red-500/15    text-red-400    border border-red-500/30
```

### Typography Scale
```
Page title:      32px  IBM Plex Mono  #F1F5F9  font-bold
Section header:  20px  DM Sans        #F1F5F9  font-semibold
Card label:      13px  DM Sans        #94A3B8  uppercase tracking-wider
Data / numbers:  16px  IBM Plex Mono  #F1F5F9
Body text:       15px  DM Sans        #CBD5E1
Muted / meta:    13px  DM Sans        #475569
```

### Data Numbers (special rule)
All prices, percentages, confidence scores → always `IBM Plex Mono`. Never a sans-serif for numbers. This makes the dashboard feel trustworthy and precise.

---

## Responsive Behaviour

### Desktop (>1024px)
- Full sidebar + main content layout
- Signal cards: 2-column grid
- Backtest: side-by-side config + results

### Tablet (768–1024px)
- Sidebar collapses to icon-only
- Signal cards: 2-column still
- Backtest: stacked (config top, results below)

### Mobile (<768px)
- Sidebar becomes bottom nav bar
- Signal cards: single column
- Logbook table: horizontal scroll
- All modals: full-screen sheet from bottom

---

## Micro-interactions

- Signal card load: fade-in + slide-up with 100ms staggered delay per card
- Confidence ring: animated fill on page load (0 → actual value, 600ms ease-out)
- INVEST card: subtle green pulsing glow on hover
- Button clicks: 95% scale on press (CSS transform)
- Number changes in portfolio: count-up animation
- Page transitions: 150ms fade

---

## GitHub Pages Deploy Notes

- All routes must work with hash routing (`/#/dashboard`) OR configure `404.html` redirect trick for React Router
- `vite.config.js` → set `base: '/cryptosense/'` (your repo name)
- `gh-pages` npm package handles deploy: `npm run deploy`
- Backend URL in `.env.production` → your Railway/Render URL
- Google OAuth redirect URL must include `https://yourusername.github.io/cryptosense`

---

*Design version 1.0 — Pre-build spec lock*