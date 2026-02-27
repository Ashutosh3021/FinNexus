# FinNexus - Developer Guide & Best Practices

## Overview

This guide documents the architectural decisions, patterns, and best practices implemented in FinNexus after resolving critical rendering and responsiveness issues.

---

## Architecture Overview

```
app/
├── (auth)/                 # Authentication pages (login, onboarding)
├── dashboard/             # Main app layout with providers
│   ├── layout.jsx        # Wraps all pages with contexts
│   ├── page.jsx          # Dashboard home
│   ├── portfolio/        # Portfolio management
│   ├── news/             # Financial news feed
│   ├── playground/       # Prediction trading
│   ├── advisor/          # AI advisor chat
│   ├── learn/            # Learning lessons
│   └── [id]/             # Lesson details
├── layout.tsx            # Root layout
├── page.jsx              # Home page
└── globals.css           # Global styles

context/
├── UserContext.jsx       # User profile, balance, XP
├── PortfolioContext.jsx  # Holdings, P&L calculations
├── PlaygroundContext.jsx # Predictions, win rate
└── NewsContext.jsx       # News feed filtering

lib/
├── mockData.js           # Mock data for all contexts
└── utils.js              # Utility functions
```

---

## Data Flow & State Management

### Context Architecture
Each feature area has its own context with localStorage persistence:

```jsx
// Pattern used in all contexts
export const [FeatureContext] = createContext();

export const FeatureProvider = ({ children }) => {
  const [state, dispatch] = useReducer(reducer, initialState);
  
  // Load from localStorage on mount
  useEffect(() => {
    const saved = localStorage.getItem('finnexus_feature');
    if (saved) dispatch({ type: 'SET_DATA', payload: JSON.parse(saved) });
  }, []);
  
  // Save to localStorage on every state change
  useEffect(() => {
    localStorage.setItem('finnexus_feature', JSON.stringify(state));
  }, [state]);
  
  return <FeatureContext.Provider value={value}>{children}</FeatureContext.Provider>;
};

export const useFeature = () => {
  const context = useContext(FeatureContext);
  if (!context) throw new Error('useFeature must be used within FeatureProvider');
  return context;
};
```

### Hydration Safety Pattern
All pages using context data implement this pattern:

```jsx
'use client';

export default function Page() {
  const [isHydrated, setIsHydrated] = useState(false);
  
  useEffect(() => {
    setIsHydrated(true);
  }, []);
  
  if (!isHydrated) return <LoadingSkeleton />;
  return <PageContent />;
}
```

**Why**: Context data loads from localStorage after component mounts. Without hydration guard, SSR renders before data loads, causing mismatch.

---

## Responsive Design System

### Breakpoints (Tailwind v4)
```
Mobile (default):   < 640px   (phones)
Tablet (sm):        640px+    (small tablets)
Desktop (md):       768px+    (tablets, small laptops)
Large (lg):         1024px+   (desktops)
X-Large (xl):       1280px+   (large monitors)
```

### Mobile-First Approach

```jsx
// ❌ Desktop-first (avoid)
<div className="grid grid-cols-4 md:grid-cols-2 sm:grid-cols-1">

// ✅ Mobile-first (correct)
<div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4">
```

### Common Responsive Patterns

#### Grids
```jsx
// 1 column on mobile, 2 on tablet, 4 on desktop
<div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">

// Auto-fit responsive grid
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
```

#### Flexbox
```jsx
// Stack vertically on mobile, horizontal on desktop
<div className="flex flex-col sm:flex-row items-start sm:items-center gap-4">

// Space items on mobile, justify between on desktop
<div className="flex flex-wrap justify-between gap-4">
```

#### Typography
```jsx
// Scale text size for readability
<h1 className="text-2xl sm:text-3xl lg:text-4xl font-bold">

// Responsive paragraph text
<p className="text-xs sm:text-sm lg:text-base">
```

#### Spacing
```jsx
// Responsive padding
<div className="p-4 sm:p-6 lg:p-8">

// Responsive margins
<div className="mb-4 sm:mb-6 lg:mb-8">

// Responsive gap
<div className="flex gap-2 sm:gap-4 lg:gap-6">
```

#### Table Responsiveness
```jsx
// Hide columns on smaller screens
<th className="hidden sm:table-cell px-6 py-3">Column Header</th>

// Show minimal info on mobile
<td className="px-3 sm:px-6 py-4">
  <p className="text-xs sm:text-base">{data}</p>
</td>
```

---

## Common Patterns

### Safe Data Access
Always use optional chaining and nullish coalescing:

```jsx
// ❌ Crashes if undefined
<p>{portfolio.totalValue.toLocaleString()}</p>

// ✅ Safe with fallback
<p>{portfolio.totalValue?.toLocaleString(...) || '0.00'}</p>

// ✅ Safe with default value
<p>{(portfolio.totalPnL || 0).toFixed(2)}</p>
```

### Loading States
```jsx
// Show skeleton during hydration
if (!isHydrated) {
  return (
    <div className="animate-pulse">
      <div className="h-10 bg-slate-700 rounded w-1/3 mb-2"></div>
      <div className="h-4 bg-slate-700 rounded w-1/2"></div>
    </div>
  );
}
```

### Empty States
```jsx
{data && data.length > 0 ? (
  <DataContent />
) : (
  <div className="text-center py-8">
    <p className="text-slate-400">No data available</p>
  </div>
)}
```

### Form Responsiveness
```jsx
<div className="flex flex-col sm:flex-row gap-2 sm:gap-4">
  <input
    type="text"
    className="flex-1 bg-slate-700 border border-slate-600 rounded-lg px-3 sm:px-4 py-2 sm:py-3 text-xs sm:text-base"
  />
  <button className="px-4 py-2 sm:px-6 sm:py-3 text-sm sm:text-base">
    Submit
  </button>
</div>
```

---

## Testing Guidelines

### Responsive Testing Checklist
- [ ] Test at 320px (mobile)
- [ ] Test at 640px (tablet)
- [ ] Test at 1024px (desktop)
- [ ] Test with Chrome DevTools device emulation
- [ ] Test on actual mobile device
- [ ] Verify touch interactions work on mobile
- [ ] Check text is readable (minimum 14px on mobile)

### Functionality Testing
- [ ] Data loads correctly
- [ ] No console errors
- [ ] Hydration completes successfully
- [ ] Interactions work smoothly
- [ ] Loading states display properly
- [ ] Empty states show appropriately

### Cross-Browser Testing
- [ ] Chrome (latest)
- [ ] Firefox (latest)
- [ ] Safari (latest)
- [ ] Edge (latest)
- [ ] Mobile Safari (iOS)
- [ ] Chrome Mobile (Android)

---

## Performance Best Practices

### 1. Avoid Unnecessary Renders
```jsx
// ❌ Causes re-render on every parent render
const [data] = useState(useContext(DataContext));

// ✅ Get data once from context
const data = useContext(DataContext);
```

### 2. Memoize Expensive Calculations
```jsx
// ❌ Recalculates on every render
const total = portfolio.holdings.reduce((sum, h) => sum + h.value, 0);

// ✅ Memoize the calculation
const total = useMemo(() => 
  portfolio.holdings.reduce((sum, h) => sum + h.value, 0),
  [portfolio.holdings]
);
```

### 3. Lazy Load Heavy Components
```jsx
const HeavyChart = dynamic(() => import('./HeavyChart'), { 
  loading: () => <Skeleton /> 
});
```

### 4. Optimize Images
```jsx
// Use responsive images
<img 
  src={imagePath} 
  alt="Description"
  className="w-full sm:max-w-md lg:max-w-lg"
/>
```

---

## Debugging Common Issues

### Issue: "Cannot read property of undefined"
**Cause**: Accessing data before hydration or context initialization
**Solution**: Add hydration guard and use optional chaining

```jsx
// Add to page
const [isHydrated, setIsHydrated] = useState(false);
useEffect(() => setIsHydrated(true), []);
if (!isHydrated) return <Loading />;

// Use optional chaining
${data?.property || 'fallback'}
```

### Issue: Layout broken on mobile
**Cause**: Using desktop breakpoints without mobile-first approach
**Solution**: Start with mobile, add larger screen styles

```jsx
// ❌ Wrong
className="md:grid-cols-2 sm:grid-cols-1 grid-cols-4"

// ✅ Correct (mobile-first)
className="grid-cols-1 sm:grid-cols-2 lg:grid-cols-4"
```

### Issue: Content overflow on mobile
**Cause**: Fixed widths or no responsive padding/margins
**Solution**: Use responsive spacing

```jsx
// ❌ Fixed padding
<div className="px-6 py-4">

// ✅ Responsive padding
<div className="px-3 sm:px-6 py-2 sm:py-4">
```

### Issue: Hydration mismatch in console
**Cause**: Server and client render different content
**Solution**: Add hydration guard

```jsx
const [mounted, setMounted] = useState(false);
useEffect(() => setMounted(true), []);
if (!mounted) return null;
return <Content />;
```

---

## Adding New Pages

### Step 1: Create Page File
```jsx
// app/dashboard/newfeature/page.jsx
'use client';

import { useContext, useState, useEffect } from 'react';
import { FeatureContext } from '@/context/FeatureContext';

export default function NewFeaturePage() {
  const [isHydrated, setIsHydrated] = useState(false);
  const data = useContext(FeatureContext);
  
  useEffect(() => setIsHydrated(true), []);
  
  if (!isHydrated) return <LoadingSkeletonUI />;
  
  return (
    <div className="p-6 space-y-6">
      {/* Page content */}
    </div>
  );
}
```

### Step 2: Make Responsive
- Use mobile-first breakpoints
- Hide non-essential columns on mobile
- Scale typography appropriately
- Use responsive spacing

### Step 3: Test
- Test on all breakpoints
- Check for console errors
- Verify data loads correctly
- Test on mobile devices

---

## Code Style Guide

### Naming Conventions
```jsx
// Components: PascalCase
function PortfolioCard() {}

// Variables/Functions: camelCase
const handleClick = () => {}
const isLoading = false;

// Constants: UPPER_SNAKE_CASE
const MAX_HOLDINGS = 50;

// Context: [Feature]Context
PortfolioContext
UserContext
PlaygroundContext
```

### File Organization
```jsx
// Order of imports
import React, { useState, useEffect, useContext } from 'react';
import { lucide-react icons } from 'lucide-react';
import { customContexts } from '@/context';

// Order in component
1. useState declarations
2. useContext declarations
3. useEffect hooks
4. Helper functions
5. JSX return
```

### Comment Style
```jsx
// Use for sections
// Portfolio Summary

// Use for complex logic
// Calculate total value excluding reserves
const totalValue = holdings.reduce((sum, h) => sum + (h.qty * h.price), 0);

// Avoid obvious comments
// ❌ Set isLoading to true
setIsLoading(true);

// ✅ Fetch data when component mounts
useEffect(() => {}, []);
```

---

## Accessibility Considerations

### Always Include
- `alt` text for images
- ARIA labels for icons
- `aria-label` for button tooltips
- Semantic HTML elements

### Example
```jsx
<button 
  aria-label="Close dialog"
  className="p-2 hover:bg-slate-700"
>
  <X size={20} />
</button>

<img 
  src="/chart.png" 
  alt="Portfolio performance chart"
/>

<main className="p-6">
  {/* Main content */}
</main>
```

---

## Deployment Checklist

- [ ] All pages load without errors
- [ ] Responsive design tested on mobile
- [ ] No console warnings or errors
- [ ] Hydration properly implemented
- [ ] Loading states display correctly
- [ ] Empty states handled
- [ ] Data loads from correct sources
- [ ] All links working
- [ ] Forms submit properly
- [ ] Mobile navigation works
- [ ] Touch targets 44px+ on mobile
- [ ] Lighthouse score 80+

---

## Resources

- [Next.js Documentation](https://nextjs.org/docs)
- [React Documentation](https://react.dev)
- [Tailwind CSS Documentation](https://tailwindcss.com)
- [Responsive Design Patterns](https://web.dev/responsive-web-design-basics/)
- [Web Accessibility (WCAG)](https://www.w3.org/WAI/WCAG21/quickref/)

---

**Last Updated**: 2024-03-21
**Maintainer**: FinNexus Dev Team
