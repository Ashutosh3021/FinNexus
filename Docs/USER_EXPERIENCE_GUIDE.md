# User Experience Guide: Candlestick Charts & Analysis

## What Users Will See

### Dashboard Experience

When users navigate to `/dashboard`, they'll see a new section titled **"Market Trends (Candlestick)"** with:

#### Visual Layout:
```
┌──────────────────────────────────────────────────────┐
│  Market Trends (Candlestick)                         │
│                                                       │
│  [AAPL] [BTC] [SPY]  ← Interactive symbol buttons   │
│                                                       │
│  Price Chart Area:                                   │
│  ▒▓▓▓▒  ▒▒▒▒▒  ▒▓▓▓▒  ▒▒▒▒▒  ▒▓▓▓▒                 │
│  ▒▓▓▓▒  ▒▒▒▒▒  ▒▓▓▓▒  ▒▒▒▒▒  ▒▓▓▓▒  ← Candlesticks │
│  ▒▓▓▓▒  ▒▒▒▒▒  ▒▓▓▓▒  ▒▒▒▒▒  ▒▓▓▓▒                 │
│                                                       │
│  Volume: ████████░░░  ← Volume bars                 │
└──────────────────────────────────────────────────────┘
```

#### User Interactions:
1. **Click Symbol Buttons** - Switch between AAPL, BTC, SPY
2. **Hover Over Candlesticks** - See price details (Open, High, Low, Close, Volume)
3. **Responsive** - Works perfectly on mobile, tablet, and desktop

#### What Each Color Means:
- 🟢 **Green Candle** = Bullish day (price went up)
- 🔴 **Red Candle** = Bearish day (price went down)

---

### Playground Experience - Asset Not Selected

When users first enter the Playground at `/playground`, they see:

```
┌──────────────────────────────────────────────────────┐
│  Prediction Playground                               │
│                                                       │
│  [Asset Selection]              [Make Prediction]    │
│  ┌─────────────────┐            (Empty when no      │
│  │ [AAPL]          │             asset selected)    │
│  │ [BTC]           │                                 │
│  │ [SPY]           │                                 │
│  │ [MSFT]          │                                 │
│  └─────────────────┘                                 │
└──────────────────────────────────────────────────────┘
```

#### User Action:
- **Click an asset button** (e.g., AAPL)

---

### Playground Experience - Asset Selected 🎯 THE TRANSFORMATION

**Everything changes when an asset is selected!**

#### Before (Asset Selection Only):
```
Asset Selection | Make Prediction Form
```

#### After (Full Analysis Appears):
```
Asset Selection | Make Prediction Form
      ↓
CANDLESTICK CHART (30-Day)
      ↓
TECHNICAL ANALYSIS | HISTORICAL EVENTS
      ↓
HOW NEWS IMPACTS PRICE EXPLANATION
```

---

## What Appears When Asset Is Selected

### 1. Candlestick Chart Section

**Visual:**
```
┌─────────────────────────────────────────────────────┐
│ AAPL Price Action (30-Day)                          │
│                                                     │
│ ▒▓▓▓▒  ▒▒▒▒▒  ▒▓▓▓▒  ▒▒▒▒▒  ▒▓▓▓▒  ▒▒▒▒▒          │
│ ▒▓▓▓▒  ▒▒▒▒▒  ▒▓▓▓▒  ▒▒▒▒▒  ▒▓▓▓▒  ▒▒▒▒▒          │
│ ▒▓▓▓▒  ▒▒▒▒▒  ▒▓▓▓▒  ▒▒▒▒▒  ▒▓▓▓▒  ▒▒▒▒▒          │
│                                                     │
│ Feb 20  Feb 21  Feb 22  ...  Mar 01                │
│                                                     │
│ Volume: ████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░       │
└─────────────────────────────────────────────────────┘
```

**Interactive Tooltip (on hover):**
```
┌─────────────────────┐
│ 2024-03-01         │ ← Date
│ Open: $185.40       │
│ High: $187.30       │
│ Low: $185.50        │
│ Close: $186.80      │
│ Vol: 52.1M          │
└─────────────────────┘
```

**What the User Learns:**
- How prices moved over 30 days
- Which days were bullish (green) vs bearish (red)
- The strength of moves (wick length)
- Trading volume

---

### 2. Technical Analysis Panel (Left Side on Desktop)

```
┌──────────────────────────────────────────────────┐
│ 📈 Technical Analysis                            │
├──────────────────────────────────────────────────┤
│                                                   │
│ [Resistance: $190.50]  [Support: $182.00]       │
│ [50-Day MA: $181.25]   [200-Day MA: $175.80]    │
│ [RSI: 72]              [MACD: Bullish]          │
│                                                   │
│ [Uptrend] [Strong] [Moderate Volatility]        │
│                                                   │
│ 💡 Recommendation: Buy on dips                   │
│                                                   │
│ Analysis:                                         │
│ "Apple is in a strong uptrend with price above  │
│  both key moving averages. RSI indicates         │
│  overbought conditions, suggesting pullback..."  │
│                                                   │
└──────────────────────────────────────────────────┘
```

**Color Coding:**
- 🟢 **Green** = Bullish signal
- 🔴 **Red** = Bearish signal
- 🔵 **Blue** = Technical levels

**What the User Learns:**
- Key price zones (support/resistance)
- Trend direction
- Momentum indicators
- What to expect next

---

### 3. Historical Events Timeline (Right Side on Desktop)

```
┌──────────────────────────────────────────────────┐
│ 📅 Historical Events & News                      │
├──────────────────────────────────────────────────┤
│                                                   │
│ ✅ Apple Q1 Earnings Report                      │
│    Positive Impact (Green Border)                │
│    2024-02-28 | Earnings (Yellow Badge)         │
│    "Apple exceeded earnings expectations        │
│     with strong iPhone 15 demand in Asian       │
│     markets, driving stock price up 1.8%"       │
│                                                   │
│ 📊 Market Rally on Soft CPI Data                 │
│    Positive Impact (Green Border)                │
│    2024-02-25 | Macro (Blue Badge)              │
│    "Inflation comes in lower than expected,     │
│     supporting tech sector rally..."            │
│                                                   │
│ 🔔 Fed Signals Stable Rates                      │
│    Neutral Impact (Gray Border)                  │
│    2024-02-20 | Macro (Blue Badge)              │
│    "Federal Reserve officials indicate no       │
│     immediate changes to monetary policy..."    │
│                                                   │
└──────────────────────────────────────────────────┘
```

**Event Categories:**
- 🟡 **Yellow Badge** = Earnings news
- 🔵 **Blue Badge** = Macro economic
- 🟣 **Purple Badge** = Regulatory
- 🟠 **Orange Badge** = Crypto news

**Impact Colors:**
- 🟢 **Green** = Positive (bullish catalyst)
- 🔴 **Red** = Negative (bearish catalyst)
- ⚪ **Gray** = Neutral (mixed signals)

**What the User Learns:**
- What news events occurred
- How they impacted the price
- Connection between events and chart
- Market context

---

### 4. Correlation Explanation Section

```
┌──────────────────────────────────────────────────┐
│ How News Impacts Price Movement                  │
│                                                   │
│ The chart above shows how AAPL price movements   │
│ correlate with historical news events and       │
│ market catalysts. Each price spike or dip often │
│ coincides with significant announcements,       │
│ earnings releases, or macro economic data.      │
│                                                   │
│ Key Takeaways:                                   │
│ • Positive earnings trigger bullish moves       │
│ • Fed policy affects sector trends              │
│ • Regulatory news can cause sharp reversals     │
│ • Macro indicators influence long-term trends  │
│                                                   │
└──────────────────────────────────────────────────┘
```

**What the User Learns:**
- Why prices moved
- Market drivers and catalysts
- How to connect events to trends
- Decision-making factors

---

## User Workflows

### Workflow 1: Dashboard Explorer

```
1. User Opens Dashboard
   ↓
2. Scrolls to "Market Trends" Section
   ↓
3. Sees AAPL Candlestick Chart
   ↓
4. Hovers Over Candles
   ↓
5. Sees Detailed Price Info in Tooltip
   ↓
6. Clicks [BTC] Button
   ↓
7. Chart Updates to Show Bitcoin
   ↓
8. Explores Different Symbols
   ↓
9. Learns About Price Patterns
```

**Time:** 3-5 minutes per symbol

---

### Workflow 2: Informed Prediction Maker

```
1. User Enters Playground
   ↓
2. Clicks Asset (e.g., AAPL)
   ↓
3. Scrolls Through Analysis Sections:
   - Views 30-day candlestick chart
   - Reads technical metrics
   - Sees historical events
   - Reads how news impacts price
   ↓
4. Makes Decision Based on Data:
   "RSI is high, but trend is bullish,
    last event was positive...
    I'll predict PRICE UP"
   ↓
5. Sets Prediction Amount
   ↓
6. Submits Prediction
   ↓
7. Tracks Result
   ↓
8. Learns From Outcome
```

**Time:** 5-10 minutes per prediction

---

### Workflow 3: Technical Analyst

```
1. User Opens Playground
   ↓
2. Selects Multiple Assets
   ↓
3. For Each Asset:
   - Studies Candlestick Patterns
   - Analyzes Technical Metrics
   - Identifies Support/Resistance
   - Checks RSI Levels
   - Confirms MACD Signal
   ↓
4. Cross-References Events
   ↓
5. Forms Trading Thesis
   ↓
6. Makes High-Confidence Prediction
   ↓
7. Documents Strategy
```

**Time:** 15-20 minutes for thorough analysis

---

## Mobile Experience

### What It Looks Like

**Dashboard (Mobile):**
```
┌─────────────────────────┐
│ Market Trends          │
│                         │
│ [AAPL][BTC][SPY]       │ ← Wrapped buttons
│                         │
│ ▒▓▓▓▒  ▒▒▒▒▒           │
│ ▒▓▓▓▒  ▒▒▒▒▒           │ ← Stacked vertically
│ ▒▓▓▓▒  ▒▒▒▒▒           │
│                         │
│ Volume: ████░░░░       │
│                         │
└─────────────────────────┘
```

**Playground (Mobile):**
```
┌─────────────────────────┐
│ Candlestick Chart      │
│ [AAPL]                 │
│ ▒▓▓▓▒  ▒▒▒▒▒           │
│ ▒▓▓▓▒  ▒▒▒▒▒           │
│                         │
├─────────────────────────┤
│ Technical Analysis      │
│ Resistance: $190       │
│ Support: $182          │
│ RSI: 72 (Overbought)   │
│                         │
├─────────────────────────┤
│ Historical Events      │
│ ✅ Apple Earnings      │
│    Positive Impact     │
│    Details...          │
│                         │
├─────────────────────────┤
│ How News Impacts...    │
│ Explanation text       │
│                         │
└─────────────────────────┘
```

**Key Mobile Features:**
- Single-column layout
- Scrollable sections
- Touch-friendly buttons
- Readable font sizes
- Full functionality

---

## Tablet Experience

**Playground (Tablet):**
```
┌─────────────────────────────────────────┐
│ Candlestick Chart (Full Width)          │
│ ▒▓▓▓▒  ▒▒▒▒▒  ▒▓▓▓▒  ▒▒▒▒▒  ▒▓▓▓▒      │
│                                          │
├──────────────────┬──────────────────────┤
│ Technical        │ Historical Events    │
│ Analysis         │                      │
│ Resistance: $190 │ ✅ Apple Earnings   │
│ Support: $182    │    Positive Impact  │
│ RSI: 72          │ 📊 Soft CPI Data    │
│ MACD: Bullish    │    Positive Impact  │
│                  │                      │
└──────────────────┴──────────────────────┘
```

**Key Tablet Features:**
- Two-column balanced layout
- Readable chart size
- Side-by-side panels
- Good use of space

---

## Desktop Experience

**Playground (Desktop):**
```
┌──────────────────────────────────────────────────────────────┐
│ Asset | Make Prediction | (Previous sections above)          │
├──────────────────────────────────────────────────────────────┤
│                                                                │
│ AAPL Price Action (30-Day) - Full Width                      │
│ ▒▓▓▓▒  ▒▒▒▒▒  ▒▓▓▓▒  ▒▒▒▒▒  ▒▓▓▓▒  ▒▒▒▒▒  ▒▓▓▓▒  ▒▒▒▒▒    │
│ ▒▓▓▓▒  ▒▒▒▒▒  ▒▓▓▓▒  ▒▒▒▒▒  ▒▓▓▓▒  ▒▒▒▒▒  ▒▓▓▓▒  ▒▒▒▒▒    │
│                                                                │
├──────────────────────────┬──────────────────────────────────┤
│                          │                                   │
│  Technical Analysis      │  Historical Events Timeline      │
│                          │                                   │
│ Resistance: $190.50      │ ✅ Apple Q1 Earnings            │
│ Support: $182.00         │    Positive Impact               │
│ 50-Day MA: $181.25       │    2024-02-28 | Earnings        │
│ 200-Day MA: $175.80      │                                   │
│ RSI: 72 (Overbought)     │ 📊 Market Rally CPI Data        │
│ MACD: Bullish            │    Positive Impact               │
│ Trend: Uptrend           │    2024-02-25 | Macro           │
│ Strength: Strong         │                                   │
│ Volatility: Moderate     │ 🔔 Fed Rate Decision            │
│                          │    Neutral Impact                │
│ 💡 Buy on dips           │    2024-02-20 | Macro           │
│                          │                                   │
├──────────────────────────┴──────────────────────────────────┤
│ How News Impacts Price Movement                              │
│ [Full explanation text visible]                              │
└─────────────────────────────────────────────────────────────┘
```

**Key Desktop Features:**
- Optimal information density
- Side-by-side comparison
- Full detail visibility
- Professional appearance

---

## Interactive Elements

### Candlestick Hover Tooltip
- **Appears on:** Hover over any candlestick
- **Shows:** Date, Open, High, Low, Close, Volume
- **Disappears:** When mouse leaves candlestick
- **Purpose:** Detailed price information

### Symbol Selector Buttons
- **Dashboard:** [AAPL] [BTC] [SPY]
- **Style:** Highlighted when active, subtle when inactive
- **Action:** Click to switch charts
- **Feedback:** Instant chart update

### Event Timeline
- **Scrollable:** If more than 5 events
- **Colored borders:** Based on impact
- **Badges:** Category identification
- **Descriptive text:** Full context

---

## Visual Feedback

### State Indicators

**Chart States:**
- ✓ Data loaded: Chart displays
- ⏳ Loading: Skeleton screen shown
- ✗ No data: "No data available" message

**Button States:**
- **Active:** Highlighted with blue background
- **Inactive:** Subtle gray background
- **Hover:** Slightly darker
- **Disabled:** Grayed out

**Metric States:**
- 🟢 **Bullish:** Green color
- 🔴 **Bearish:** Red color
- 🔵 **Neutral:** Blue color
- 🟠 **Warning:** Orange color

---

## Educational Elements

### Callout Boxes

**Blue Box (Information):**
```
💡 How News Impacts Price Movement
Explanation of correlation...
```

**Yellow Box (Warning):**
```
⚠️ Overbought Condition
When RSI > 70, potential pullback...
```

**Green Box (Success):**
```
✅ Positive Signal
Price above both MAs indicates uptrend...
```

---

## Accessibility Features

### Keyboard Navigation
- Tab through buttons
- Arrow keys to scroll
- Enter to select
- Escape to close tooltips

### Screen Reader
- Clear heading hierarchy
- ARIA labels on interactive elements
- Image alt text
- Semantic structure

### Color Alternatives
- Not just green/red, but also icons
- Text labels for all indicators
- Symbols and shapes for additional cues

---

## Summary

Users will experience:
- ✅ Beautiful, interactive charts
- ✅ Clear market insights
- ✅ Educational context
- ✅ Intuitive controls
- ✅ Responsive design
- ✅ Accessible features
- ✅ Professional appearance
- ✅ Smooth interactions

The feature set transforms the Playground from a simple prediction tool into a **comprehensive market analysis platform** where users can make informed, data-driven decisions.
