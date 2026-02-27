# Data Visualization & Charts Documentation

## Overview

FinNexus now includes beautiful, responsive data visualization components built with Recharts and shadcn/ui. All charts gracefully handle empty states and update seamlessly when data becomes available.

## Chart Components

### 1. PortfolioChart
**Location:** `components/charts/PortfolioChart.jsx`

**Features:**
- Pie chart showing asset allocation by type (stocks, crypto, commodities, ETFs)
- Color-coded visualization with interactive tooltips
- Graceful empty state when no holdings exist
- Responsive design that adapts to mobile, tablet, and desktop

**Usage:**
```jsx
<PortfolioChart holdings={portfolio?.holdings} />
```

**Data Requirements:**
```javascript
{
  id: string,
  asset: string,
  symbol: string,
  type: 'stock' | 'crypto' | 'commodity' | 'etf',
  qty: number,
  buyPrice: number,
  currentPrice: number,
  buyDate: string
}
```

**Empty State:**
- Shows informative message when no holdings exist
- Prompts user to add their first investment
- Maintains visual consistency with the design

---

### 2. PerformanceChart
**Location:** `components/charts/PerformanceChart.jsx`

**Features:**
- Line chart displaying portfolio P&L over 30 days
- Simulated historical data based on current holdings
- Interactive tooltip showing daily performance
- Smooth animations and transitions

**Usage:**
```jsx
<PerformanceChart holdings={portfolio?.holdings} />
```

**Empty State:**
- Displays placeholder when no holdings exist
- Explains that performance data requires holdings
- Clean, non-intrusive design

**Generated Data:**
- Automatically calculates simulated P&L for past 30 days
- Uses current holding prices as baseline
- Adds variance to simulate realistic price movements

---

### 3. PredictionStatsChart
**Location:** `components/charts/PredictionStatsChart.jsx`

**Features:**
- Stacked bar chart showing wins vs. losses by asset
- Displays up to 6 assets with highest prediction activity
- Color-coded: green for wins, red for losses
- Real-time calculation of win rates

**Usage:**
```jsx
<PredictionStatsChart predictionHistory={playground?.predictionHistory} />
```

**Data Requirements:**
```javascript
{
  id: string,
  asset: string,
  type: 'win' | 'loss',
  prediction: 'up' | 'down',
  actual: 'up' | 'down',
  pnl: number,
  pnlPercent: number,
  date: string
}
```

**Empty State:**
- Shows message prompting user to make predictions
- Explains purpose of the chart
- Maintains visual hierarchy

---

## Empty State Component

**Location:** `components/ui/EmptyState.jsx`

A reusable component for consistent empty state visualization across all charts.

**Features:**
- Customizable icon (default: AlertCircle)
- Customizable title and description
- Optional action button
- Multiple variants: default, success, warning, error

**Usage:**
```jsx
<EmptyState
  icon={TrendingUp}
  title="No holdings yet"
  description="Add your first investment to see your portfolio allocation"
  variant="success"
  action={<button>Add Holding</button>}
/>
```

---

## Loading State

**DataLoadingState Component** provides a consistent loading animation for data loading periods.

**Features:**
- Spinning animation
- Friendly loading message
- Non-blocking UI

**Usage:**
```jsx
<Suspense fallback={<DataLoadingState />}>
  <YourContent />
</Suspense>
```

---

## Integration Points

### Dashboard Page
**File:** `app/dashboard/page.jsx`

The main dashboard now includes:
1. Portfolio metrics cards (4 cards showing key KPIs)
2. Portfolio allocation pie chart
3. Performance trend line chart
4. Prediction statistics bar chart
5. Top holdings table
6. Recent predictions sidebar

All components use the Suspense boundary for proper loading handling.

### Unified Dashboard
**File:** `app/dashboard/unified/page.jsx`

A comprehensive view combining:
- Portfolio, playground, and news data
- All three chart types
- Recent financial news feed
- Data summary cards
- Responsive grid layout

---

## Responsive Design

All charts follow mobile-first responsive design:

- **Mobile (< 640px):** Single column, stacked layout
- **Tablet (640px - 1024px):** Two-column grid where appropriate
- **Desktop (> 1024px):** Full multi-column layout with optimal spacing

Charts automatically adjust container sizes and use ResponsiveContainer from Recharts.

---

## Color Scheme

### Asset Types (Pie Chart)
- **Stocks:** Blue (#3b82f6)
- **Crypto:** Amber (#fbbf24)
- **Commodities:** Orange (#f97316)
- **ETFs:** Purple (#a78bfa)

### Performance (Line Chart)
- **P&L Line:** Green (#10b981)
- **Grid:** Slate (#475569)
- **Axes:** Slate (#94a3b8)

### Prediction Stats (Bar Chart)
- **Wins:** Green (#10b981)
- **Losses:** Red (#ef4444)
- **Grid:** Slate (#475569)

---

## Data Flow & Updates

### Real-time Updates
Charts update automatically when:
1. Holdings are added/removed
2. Prices change
3. New predictions are recorded
4. Context data changes

### Caching Strategy
- Charts recalculate only when source data changes
- React.useMemo can be used for expensive calculations
- Context providers manage data persistence

---

## Accessibility Features

- **Alt text:** Chart titles and descriptions
- **Keyboard navigation:** Full keyboard support through Recharts
- **Screen reader support:** Descriptions for empty states
- **Color contrast:** All colors meet WCAG AA standards

---

## Performance Optimization

### Best Practices Implemented
1. Lazy loading with React.Suspense
2. Memoization of chart components
3. Efficient data transformation
4. No unnecessary re-renders

### Bundle Size
- Recharts: ~45KB (gzipped)
- Chart components: ~3KB each
- Total overhead: minimal impact on page load

---

## Testing Empty States

To test empty state visualization:

1. **Remove holdings:** Clear portfolio data in context
2. **No predictions:** Fresh user without prediction history
3. **Empty news:** Filter news to show no results

All states should display informative messages and maintain design consistency.

---

## Future Enhancements

Potential improvements:
1. **Interactive legends:** Click to toggle series visibility
2. **Date range filters:** Customize performance chart timeframe
3. **Comparison mode:** Compare multiple portfolios
4. **Export charts:** Download as PNG/PDF
5. **Advanced metrics:** Add Sharpe ratio, standard deviation, etc.
6. **Real-time data:** WebSocket updates for live prices

---

## Troubleshooting

### Charts Not Rendering
- Check if data is properly passed through context
- Verify Recharts imports are correct
- Check browser console for errors

### Empty States Not Showing
- Ensure component receives `undefined` or empty array
- Check EmptyState component is imported
- Verify fallback UI is in Suspense boundary

### Mobile Layout Issues
- Check ResponsiveContainer width/height props
- Verify parent container has defined dimensions
- Test with various device sizes in DevTools

### Data Not Updating
- Check context provider is wrapping component
- Verify state updates trigger re-renders
- Check React DevTools for state changes

---

## API Reference

### PortfolioChart Props
```typescript
interface PortfolioChartProps {
  holdings?: Array<{
    id: string;
    asset: string;
    type: 'stock' | 'crypto' | 'commodity' | 'etf';
    qty: number;
    currentPrice: number;
  }>;
}
```

### PerformanceChart Props
```typescript
interface PerformanceChartProps {
  holdings?: Array<{
    qty: number;
    currentPrice: number;
    buyPrice: number;
  }>;
}
```

### PredictionStatsChart Props
```typescript
interface PredictionStatsChartProps {
  predictionHistory?: Array<{
    id: string;
    asset: string;
    type: 'win' | 'loss';
    pnl: number;
  }>;
}
```

### EmptyState Props
```typescript
interface EmptyStateProps {
  icon?: React.ComponentType<{size: number}>;
  title?: string;
  description?: string;
  action?: React.ReactNode;
  variant?: 'default' | 'success' | 'warning' | 'error';
}
```

---

## Links

- Dashboard Page: `/dashboard`
- Unified Dashboard: `/dashboard/unified`
- Portfolio Page: `/portfolio`
- Playground Page: `/playground`

---

*Last Updated: 2024*
*Version: 1.0.0*
