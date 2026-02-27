# FinNexus Architecture Diagram

## Component Tree Structure (After Fix)

```
html (lang="en")
└── body
    └── RootLayout (app/layout.tsx)
        └── <Providers> ✅ ROOT PROVIDER WRAPPER
            ├── UserProvider
            │   ├── PortfolioProvider
            │   │   ├── PlaygroundProvider
            │   │   │   ├── NewsProvider
            │   │   │   │   ├── (auth) Routes
            │   │   │   │   │   ├── /login
            │   │   │   │   │   └── /onboarding
            │   │   │   │   ├── Dashboard Routes
            │   │   │   │   │   └── DashboardLayout
            │   │   │   │   │       ├── /dashboard
            │   │   │   │   │       └── /learn
            │   │   │   │   ├── Root Routes (with navbar)
            │   │   │   │   │   ├── ✅ /playground
            │   │   │   │   │   ├── ✅ /news
            │   │   │   │   │   ├── ✅ /portfolio
            │   │   │   │   │   ├── ✅ /advisor
            │   │   │   │   │   └── /
            │   │   │   │   └── Analytics
            │   │   │   │   └── Others
```

## Data Flow Architecture

```
                    ROOT PROVIDERS
                    (app/providers.jsx)
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
        ▼                 ▼                 ▼
    UserProvider    PortfolioProvider  PlaygroundProvider
        │                 │                 │
        │                 │                 │
    (user data)    (portfolio data)   (prediction data)
        │                 │                 │
        └─────────────────┼─────────────────┘
                          │
                          ▼
                    NewsProvider
                    (news data)
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
        ▼                 ▼                 ▼
    /dashboard        /portfolio        /playground
    /learn            ✅ /news          ✅ /advisor
    /login                             /login
```

## Page-to-Provider Dependency Matrix

| Page | User | Portfolio | Playground | News | Status |
|------|------|-----------|------------|------|--------|
| /dashboard | ✓ | ✓ | ✓ | ✓ | ✅ |
| /portfolio | ✓ | ✓ | ✗ | ✗ | ✅ FIXED |
| /playground | ✓ | ✗ | ✓ | ✗ | ✅ FIXED |
| /news | ✓ | ✗ | ✗ | ✓ | ✅ FIXED |
| /advisor | ✗ | ✗ | ✗ | ✗ | ✅ FIXED |
| /learn | ✓ | ✗ | ✗ | ✗ | ✅ |
| /login | ✗ | ✗ | ✗ | ✗ | ✅ |

## Rendering Flow

### Before Fix (BROKEN)
```
User navigates to /playground
        ↓
Next.js loads /app/playground/page.jsx
        ↓
Component tries: const playground = usePlayground()
        ↓
React searches UP component tree for PlaygroundProvider
        ↓
Search path: PlaygroundPage → Layout (ROOT LAYOUT - NO PROVIDER)
        ↓
❌ ERROR: "usePlayground must be used within PlaygroundProvider"
```

### After Fix (WORKING)
```
User navigates to /playground
        ↓
Next.js loads /app/layout.tsx (RootLayout)
        ↓
<Providers>
  <UserProvider>
    <PortfolioProvider>
      <PlaygroundProvider> ✅
        {children} → /playground/page.jsx
      </PlaygroundProvider>
    </PortfolioProvider>
  </UserProvider>
</Providers>
        ↓
Component tries: const playground = usePlayground()
        ↓
React searches UP component tree for PlaygroundProvider
        ↓
Search path: PlaygroundPage → PlaygroundProvider ✅ FOUND
        ↓
✅ SUCCESS: Context data returned to component
```

## Context Hierarchy

### User Context
```
UserContext
├── State
│   └── mockUser data
├── Actions
│   ├── updateBalance(amount)
│   ├── updateXP(amount)
│   └── updateLevel(level)
└── Consumers
    ├── Dashboard (displays balance, level)
    ├── Playground (checks balance)
    ├── Advisor (reference data)
    └── Learn (XP gains)
```

### Portfolio Context
```
PortfolioContext
├── State
│   └── holdings[] array
├── Actions
│   ├── addHolding(holding)
│   ├── removeHolding(id)
│   └── updateHolding(holding)
├── Computed Values
│   ├── totalValue
│   ├── totalCost
│   └── totalPnL
└── Consumers
    ├── Portfolio Page (displays holdings)
    ├── Dashboard (shows summary)
    └── Navbar (displays balance)
```

### Playground Context
```
PlaygroundContext
├── State
│   ├── predictionHistory[]
│   ├── currentRound
│   ├── streak
│   ├── totalRounds
│   └── wins
├── Actions
│   ├── startRound(round)
│   └── submitPrediction(prediction)
├── Computed Values
│   └── winRate
└── Consumers
    ├── Playground Page (main page)
    └── Dashboard (stats display)
```

### News Context
```
NewsContext
├── State
│   ├── newsFeed[]
│   ├── selectedNews
│   └── selectedCategory
├── Actions
│   ├── setSelectedNews(news)
│   └── setSelectedCategory(category)
├── Computed Values
│   └── filteredNews
└── Consumers
    ├── News Page (main page)
    └── Navbar (news count)
```

## File Dependency Graph

```
app/
├── layout.tsx
│   ├── imports: ./providers
│   ├── imports: Analytics
│   └── imports: globals.css
│       └── is ROOT WRAPPER ← CRITICAL FIX APPLIED HERE
│
├── providers.jsx ← NEW FILE (Providers component)
│   ├── imports: UserContext
│   ├── imports: PortfolioContext
│   ├── imports: PlaygroundContext
│   └── imports: NewsContext
│
├── dashboard/
│   ├── layout.jsx
│   │   ├── imports: Layout
│   │   └── SIMPLIFIED (removed providers)
│   └── page.jsx
│
├── playground/page.jsx
│   ├── imports: usePlayground ← NOW HAS ACCESS VIA ROOT PROVIDER
│   ├── uses: Suspense (added)
│   └── wrapped by: <PlaygroundContent />
│
├── news/page.jsx
│   ├── imports: useNews ← NOW HAS ACCESS VIA ROOT PROVIDER
│   ├── uses: Suspense (added)
│   └── wrapped by: <NewsContent />
│
├── portfolio/page.jsx
│   ├── imports: usePortfolio ← NOW HAS ACCESS VIA ROOT PROVIDER
│   ├── uses: Suspense (added)
│   └── wrapped by: <PortfolioContent />
│
├── advisor/page.jsx
│   └── no context dependencies (standalone)
│
└── (auth)/
    ├── login/page.jsx
    └── onboarding/page.jsx
```

## Routing Structure

```
App Routes:
├── / (home page)
├── /dashboard
│   └── shows portfolio overview
├── /portfolio ← ✅ NOW WORKS
│   └── detailed holdings
├── /playground ← ✅ NOW WORKS
│   └── predictions interface
├── /news ← ✅ NOW WORKS
│   └── financial news
├── /advisor ← ✅ NOW WORKS
│   └── AI chat
├── /learn
│   ├── [id] (lesson detail)
│   └── lessons list
└── /(auth)
    ├── /login
    └── /onboarding
```

## State Management Flow

```
User interacts with page
        ↓
Component calls context action
        ↓
Reducer updates state
        ↓
localStorage synced (useEffect)
        ↓
All consumers re-render
        ↓
UI updates (through context consumers)
```

## Suspense Boundary Pattern

```
export default function Page() {
  return (
    <Suspense fallback={<LoadingUI />}>
      <PageContent />
    </Suspense>
  );
}

// Benefits:
// ✓ Shows loading state while component initializes
// ✓ Prevents "white flash" before context loads
// ✓ Graceful error handling
// ✓ Better UX on slow networks
```

## Critical Issues Resolved

| Issue | Location | Root Cause | Solution |
|-------|----------|-----------|----------|
| usePlayground error | /playground | Provider not in parent layout | ✅ Moved to root |
| useNews error | /news | Provider not in parent layout | ✅ Moved to root |
| usePortfolio error | /portfolio | Provider not in parent layout | ✅ Moved to root |
| SSR Hydration | All pages | Server/client data mismatch | ✅ Added isHydrated guard |
| Missing loading state | All pages | No fallback during init | ✅ Added Suspense |

## Environment Setup Checklist

```
✅ Providers component created
✅ Root layout updated to use Providers
✅ Dashboard layout cleaned (providers removed)
✅ Playground page refactored with Suspense
✅ News page refactored with Suspense
✅ Portfolio page refactored with Suspense
✅ Advisor page refactored (no context deps)
✅ All context exports verified
✅ localStorage integration working
✅ Hydration guards in place
```

## Performance Implications

```
Context Re-renders:
- UserProvider changes → All children re-render
- PortfolioProvider changes → Portfolio, Dashboard re-render
- PlaygroundProvider changes → Playground, Dashboard re-render
- NewsProvider changes → News page re-render

Optimization Applied:
✓ Suspense boundaries prevent layout shift
✓ Hydration guard prevents double renders
✓ localStorage prevents data loss
✓ useCallback prevents unnecessary re-renders
```

## Next Steps for Further Optimization

1. **Split contexts** - If state becomes large
2. **Memoize consumers** - Prevent unnecessary re-renders
3. **Add Redux DevTools** - For complex state management
4. **Implement React Query** - For server-side data
5. **Code splitting** - Lazy load heavy pages
