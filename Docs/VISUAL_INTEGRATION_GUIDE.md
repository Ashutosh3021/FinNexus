# Visual Integration Guide: Candlestick Charts & Analysis

## Dashboard View

```
┌─────────────────────────────────────────────────────────┐
│ FINNEXUS DASHBOARD                                      │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  [Stats Grid: Win Rate | Predictions | Streak | Wins]   │
│                                                           │
│  ┌──────────────────────┬──────────────────────┐         │
│  │ Portfolio Chart      │ Performance Chart    │         │
│  │ (Pie)               │ (Line)                │         │
│  └──────────────────────┴──────────────────────┘         │
│                                                           │
│  ┌──────────────────────────────────────────────┐        │
│  │ Market Trends (Candlestick)                 │        │
│  │                                              │        │
│  │ [AAPL] [BTC] [SPY] [MSFT]  <- Symbol Selector        │
│  │                                              │        │
│  │    ▒▓▓▓▒  ▒▒▒▒▒  ▒▓▓▓▒  ▒▒▒▒▒  <- Candlesticks     │
│  │    ▒▓▓▓▒  ▒▒▒▒▒  ▒▓▓▓▒  ▒▒▒▒▒                        │
│  │    ▒▓▓▓▒  ▒▒▒▒▒  ▒▓▓▓▒  ▒▒▒▒▒                        │
│  │                                              │        │
│  │    Volume Data Below Chart                   │        │
│  └──────────────────────────────────────────────┘        │
│                                                           │
│  [Prediction Stats Chart] [Holdings Table]              │
│                                                           │
└─────────────────────────────────────────────────────────┘
```

## Playground View - Asset Not Selected

```
┌─────────────────────────────────────────────────────────┐
│ PREDICTION PLAYGROUND                                   │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  [Stats: Win Rate | Total | Streak | Wins]             │
│                                                           │
│  ┌──────────────────┬──────────────────┐               │
│  │ Asset Selection  │ Make Prediction  │               │
│  │ [AAPL]          │ (Select asset)   │               │
│  │ [BTC]           │                  │               │
│  │ [SPY]           │                  │               │
│  │ [MSFT]          │                  │               │
│  └──────────────────┴──────────────────┘               │
│                                                           │
│  [Prediction History Table]                             │
│                                                           │
└─────────────────────────────────────────────────────────┘
```

## Playground View - Asset Selected

```
┌──────────────────────────────────────────────────────────┐
│ PREDICTION PLAYGROUND                                    │
├──────────────────────────────────────────────────────────┤
│                                                            │
│  [Stats: Win Rate | Total | Streak | Wins]              │
│                                                            │
│  ┌────────────────────┬──────────────────────┐           │
│  │ Asset Selection    │ Make Prediction      │           │
│  │ [AAPL] ← SELECTED  │ [Amount Input]       │           │
│  │ [BTC]              │ [Price UP] [Price DOWN]          │
│  │ [SPY]              │                      │           │
│  │ [MSFT]             │                      │           │
│  └────────────────────┴──────────────────────┘           │
│                                                            │
│  ╔════════════════════════════════════════════════════╗  │
│  ║ AAPL PRICE ACTION (30-Day) <- CANDLESTICK CHART  ║  │
│  ║                                                    ║  │
│  ║  ▓▓▓▓  ░░░░  ▓▓▓▓  ░░░░  ▓▓▓▓    (Green=Up)     ║  │
│  ║  ▓▓▓▓  ░░░░  ▓▓▓▓  ░░░░  ▓▓▓▓    (Red=Down)      ║  │
│  ║                                                    ║  │
│  ║  Volume: MMMMM (millions)                          ║  │
│  ╚════════════════════════════════════════════════════╝  │
│                                                            │
│  ╔─────────────────────┬─────────────────────────────╗   │
│  ║ Technical Analysis  │ Historical Events Timeline │   │
│  ║                     │                             ║   │
│  ║ Resistance: $190.5  │ 📰 Apple Q1 Earnings      ║   │
│  ║ Support: $182.0     │    ✅ Positive Impact     ║   │
│  ║ 50-Day MA: $181.25  │    Price up 1.8%          ║   │
│  ║ 200-Day MA: $175.80 │                             ║   │
│  ║ RSI: 72 (Overbought)│ 📊 CPI Data Release       ║   │
│  ║ MACD: Bullish       │    ⚫ Neutral Impact       ║   │
│  ║                     │    Mixed signals           ║   │
│  ║ Trend: Uptrend      │                             ║   │
│  ║ Strength: Strong    │ 🔔 Fed Rate Decision      ║   │
│  ║ Volatility: Moderate│    ⚠️ Negative Impact      ║   │
│  ║                     │    Rate hikes concern      ║   │
│  ║ 💡 BUY on dips      │                             ║   │
│  ║                     │ [Show More Events ▼]      ║   │
│  ╚─────────────────────┴─────────────────────────────╝   │
│                                                            │
│  ╔════════════════════════════════════════════════════╗  │
│  ║ How News Impacts Price Movement                    ║  │
│  ║ The chart shows how AAPL price correlates with   ║  │
│  ║ historical events. Key takeaways:                 ║  │
│  ║ • Positive earnings trigger bullish moves         ║  │
│  ║ • Fed policy affects sector trends               ║  │
│  ║ • Regulatory news causes sharp reversals          ║  │
│  ║ • Macro data influences long-term direction       ║  │
│  ╚════════════════════════════════════════════════════╝  │
│                                                            │
│  [Prediction History Table]                              │
│                                                            │
└──────────────────────────────────────────────────────────┘
```

## Component Interaction Flow

```
User Navigates to Playground
           ↓
Renders PlaygroundContent Component
           ↓
User Clicks Asset Button (e.g., AAPL)
           ↓
setSelectedPrediction(asset) triggered
           ↓
Component Re-renders with New State
           ├─→ selectedPrediction = AAPL object
           ├─→ Shows Prediction Input Form
           └─→ Renders Additional Analysis Sections
                     ↓
        Three New Sections Appear Conditionally:
        ┌─────────────────────────────┐
        │                             │
        ├─→ CandlestickChart         ├─→ Fetches mockCandleData['AAPL']
        │   Renders 30-day price      │   Shows green/red candles
        │   action with interactive   │   Interactive tooltip on hover
        │   tooltips                  │
        │                             │
        ├─→ AssetAnalysisPanel       ├─→ Fetches mockAssetInsights['AAPL']
        │   Shows technical metrics   │   Support/Resistance levels
        │   RSI, MACD, trend info     │   Moving averages
        │                             │
        └─→ HistoricalEventsTimeline ├─→ Fetches mockHistoricalEvents['AAPL']
            Lists past events         │   Earnings, macro, regulatory news
            with impact colors        │   Timeline format with descriptions
            
           ↓
User Hovers Over Candlestick
           ↓
CustomTooltip Component Shows:
├─ Date
├─ Open Price
├─ High Price
├─ Low Price
├─ Close Price
└─ Volume

           ↓
User Switches to Different Asset (e.g., BTC)
           ↓
All Three Sections Update:
├─ CandlestickChart → mockCandleData['BTC']
├─ AssetAnalysisPanel → mockAssetInsights['BTC']
└─ HistoricalEventsTimeline → mockHistoricalEvents['BTC']
```

## Responsive Design Breakdown

### Mobile (< 640px)

```
┌──────────────────────────┐
│ PREDICTION PLAYGROUND    │
├──────────────────────────┤
│ [Asset Buttons Wrap]     │
│ [AAPL] [BTC]             │
│ [SPY] [MSFT]             │
│                          │
│ ┌────────────────────┐   │
│ │ Candlestick Chart  │   │
│ │ (Stacked vertically)   │
│ │ (Smaller font)     │   │
│ └────────────────────┘   │
│                          │
│ ┌────────────────────┐   │
│ │ Tech Analysis      │   │
│ │ (Single Column)    │   │
│ │ Resistance: $190.5 │   │
│ │ Support: $182.0    │   │
│ └────────────────────┘   │
│                          │
│ ┌────────────────────┐   │
│ │ Historical Events  │   │
│ │ (Compact list)     │   │
│ │ 📰 Earnings        │   │
│ │ 📊 CPI Data        │   │
│ │ 🔔 Fed Decision    │   │
│ └────────────────────┘   │
└──────────────────────────┘
```

### Tablet (640px - 1024px)

```
┌─────────────────────────────────┐
│ PREDICTION PLAYGROUND           │
├─────────────────────────────────┤
│ [Asset Selector]                │
│ [AAPL] [BTC] [SPY] [MSFT]       │
│                                 │
│ ┌──────────────────────────┐    │
│ │ Candlestick Chart        │    │
│ │ (Medium size)            │    │
│ └──────────────────────────┘    │
│                                 │
│ ┌────────────┬──────────────┐   │
│ │ Technical  │ Historical   │   │
│ │ Analysis   │ Events       │   │
│ │ 2-col grid │              │   │
│ └────────────┴──────────────┘   │
└─────────────────────────────────┘
```

### Desktop (> 1024px)

```
┌────────────────────────────────────────────────────────┐
│ PREDICTION PLAYGROUND                                  │
├────────────────────────────────────────────────────────┤
│                                                          │
│ ┌──────────────┬──────────────┐                        │
│ │ Asset Select │ Make Pred    │ ← Side by Side         │
│ │ [Buttons]    │ [Form]       │                        │
│ └──────────────┴──────────────┘                        │
│                                                          │
│ ┌────────────────────────────────────────────────────┐ │
│ │ Candlestick Chart (Full Width)                    │ │
│ │ (Optimal size for detailed analysis)              │ │
│ └────────────────────────────────────────────────────┘ │
│                                                          │
│ ┌─────────────────────┬──────────────────────────────┐ │
│ │ Technical Analysis  │ Historical Events Timeline  │ │
│ │ (Detailed metrics)  │ (Rich descriptions)         │ │
│ │ 2-column layout     │ Categorized events          │ │
│ └─────────────────────┴──────────────────────────────┘ │
│                                                          │
└────────────────────────────────────────────────────────┘
```

## Color Coding System

### Candlestick Colors
```
🟢 Green Candle  = Close > Open (Bullish day)
🔴 Red Candle    = Close < Open (Bearish day)
```

### Event Impact Colors
```
🟢 Green Border  = Positive Impact (Bullish catalyst)
🔴 Red Border    = Negative Impact (Bearish catalyst)
⚪ Gray Border   = Neutral Impact (Mixed signals)
```

### Technical Analysis Colors
```
🟢 Green Text    = Bullish signals
🔴 Red Text      = Bearish signals
🔵 Blue Text     = Neutral/technical levels
🟠 Orange Text   = Warning/caution conditions
```

## Information Hierarchy

### Dashboard Priority
1. **Candlestick Chart** - Main visual focus
2. Symbol Selector - Secondary navigation
3. Tooltip Information - Tertiary detail

### Playground Priority
1. **Asset Selection** - User action required
2. **Candlestick Chart** - Primary analysis visual
3. **Technical Metrics** - Secondary analysis
4. **Historical Events** - Contextual information
5. Correlation Explanation - Educational content

## Data Display Examples

### Candlestick Tooltip
```
┌─────────────────────┐
│ 2024-03-01         │ ← Date
│ Open: $185.40       │ ← Green text
│ High: $187.30       │ ← Blue text
│ Low: $185.50        │ ← Orange text
│ Close: $186.80      │ ← Green text
│ Vol: 52.1M          │ ← Gray text
└─────────────────────┘
```

### Technical Metrics Grid
```
┌─────────────────┬──────────────────┐
│ Resistance      │ Support          │
│ $190.50         │ $182.00          │
├─────────────────┼──────────────────┤
│ 50-Day MA       │ 200-Day MA       │
│ $181.25         │ $175.80          │
├─────────────────┼──────────────────┤
│ RSI: 72 ⚠️       │ MACD: Bullish ✓  │
└─────────────────┴──────────────────┘

│ Trend: Uptrend │ Strength: Strong │ Volatility: Moderate │
```

### Historical Event Card
```
┌──────────────────────────────────────────┐
│ 📰 Apple Reports Record Q1 iPhone Sales  │
│ ✅ Positive Impact                       │
│ 2024-02-28 | Earnings                    │
│                                          │
│ Apple exceeded earnings expectations     │
│ with strong iPhone 15 demand in Asian    │
│ markets, driving stock price up 1.8%.    │
└──────────────────────────────────────────┘
```

## Summary of Sections

| Section | Location | Purpose | Key Data |
|---------|----------|---------|----------|
| Candlestick Chart | Dashboard + Playground | Price action visualization | OHLC, Volume |
| Technical Analysis | Playground (conditional) | Metric-based signals | Support, Resistance, MA, RSI, MACD |
| Historical Events | Playground (conditional) | Contextual information | Events, impact, description |
| Correlation Info | Playground (conditional) | Educational context | How news affects prices |

## Next Steps for Users

1. **Explore Dashboard** - View candlestick charts for all assets
2. **Enter Playground** - Select an asset
3. **Analyze Charts** - Understand price patterns
4. **Study Events** - See what moved the price
5. **Read Metrics** - Learn technical analysis
6. **Make Prediction** - Apply knowledge to predictions
7. **Track Results** - See prediction outcomes
8. **Improve** - Refine strategy based on data
