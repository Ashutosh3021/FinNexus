# Context Provider Fix - Complete Troubleshooting Guide

## Problem Identified

**Error:** `usePlayground must be used within PlaygroundProvider`

### Root Cause Analysis

The application had a **critical architectural issue** where React Context providers were only defined in `/app/dashboard/layout.jsx`, but pages attempting to use those contexts were located outside the dashboard folder structure:

```
❌ BROKEN STRUCTURE:
├── app/
│   ├── layout.tsx (ROOT - NO PROVIDERS)
│   ├── dashboard/
│   │   ├── layout.jsx (PlaygroundProvider, UserProvider, etc.)
│   │   └── page.jsx
│   ├── playground/page.jsx (❌ NOT under /dashboard - NO ACCESS to PlaygroundProvider)
│   ├── news/page.jsx (❌ NOT under /dashboard - NO ACCESS to NewsProvider)
│   ├── portfolio/page.jsx (❌ NOT under /dashboard - NO ACCESS to PortfolioProvider)
│   ├── advisor/page.jsx (❌ NOT under /dashboard - NO ACCESS to any provider)
│   └── (auth)/
│       └── pages...
```

## How Next.js Layout System Works

In Next.js, **layouts only apply to routes within their directory and subdirectories**:

```
/app/dashboard/layout.jsx applies to:
  ✓ /dashboard
  ✓ /dashboard/page
  ✓ /dashboard/[id]/page
  ✗ /playground (NOT COVERED - outside dashboard directory)
  ✗ /news (NOT COVERED - outside dashboard directory)
```

When a component tries to use `usePlayground()`, React searches UP the component tree for `PlaygroundProvider`. Since the pages weren't under the dashboard layout, the provider was never found.

## Solution Implemented

### Option 1: Move Pages Under Dashboard (Not Chosen)
Would require changing URL structure, breaking existing routes.

### Option 2: Create Root-Level Providers (CHOSEN - Best Practice)
Creates a new `app/providers.jsx` component that wraps ALL contexts at the root level, making them available to the entire application.

**Advantages:**
- All pages have access to contexts regardless of location
- Single source of truth for provider configuration
- Follows Next.js best practices
- No breaking changes to routing

## Implementation Details

### 1. Created `/app/providers.jsx`

```jsx
'use client';

import React from 'react';
import { UserProvider } from '@/context/UserContext';
import { PortfolioProvider } from '@/context/PortfolioContext';
import { PlaygroundProvider } from '@/context/PlaygroundContext';
import { NewsProvider } from '@/context/NewsContext';

export function Providers({ children }) {
  return (
    <UserProvider>
      <PortfolioProvider>
        <PlaygroundProvider>
          <NewsProvider>
            {children}
          </NewsProvider>
        </PlaygroundProvider>
      </PortfolioProvider>
    </UserProvider>
  );
}
```

### 2. Updated `/app/layout.tsx`

```tsx
import { Providers } from './providers'

export default function RootLayout({ children }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={`${geist.className} bg-slate-900 text-slate-100 antialiased`}>
        <Providers>
          {children}
        </Providers>
        <Analytics />
      </body>
    </html>
  )
}
```

### 3. Cleaned Up `/app/dashboard/layout.jsx`

Removed duplicate providers since they're now at root level:

```jsx
'use client';

import React from 'react';
import Layout from '@/components/layout/Layout';

export default function DashboardLayout({ children }) {
  return (
    <Layout>{children}</Layout>
  );
}
```

### 4. Added Suspense Boundaries to Pages

All context-dependent pages now use `React.Suspense` for proper fallback handling:

**Pattern applied to:** `playground/page.jsx`, `news/page.jsx`, `portfolio/page.jsx`

```jsx
'use client';

import { Suspense } from 'react';

function PageContent() {
  const contextData = useContextHook();
  // Component logic
}

export default function Page() {
  return (
    <Suspense fallback={<LoadingUI />}>
      <PageContent />
    </Suspense>
  );
}
```

## Common Next.js Context Errors and Solutions

### Error 1: "X must be used within XProvider"
**Cause:** Component/page not wrapped by provider layout
**Solution:** Move to correct directory OR add provider at root level

### Error 2: SSR Hydration Mismatch
**Cause:** Context state differs between server and client render
**Solution:** Use `useEffect` with `useState` flag to defer rendering:
```jsx
const [isHydrated, setIsHydrated] = useState(false);
useEffect(() => setIsHydrated(true), []);
if (!isHydrated) return <LoadingUI />;
```

### Error 3: Context is Undefined
**Cause:** No provider in component tree
**Solution:** Check layout hierarchy and provider placement

## Testing the Fix

After applying changes, verify each page:

1. **Playground Page** (`/playground`)
   - Should load without "usePlayground must be used within PlaygroundProvider" error
   - Should display prediction interface
   - Should show recent predictions

2. **News Page** (`/news`)
   - Should load without "useNews must be used within NewsProvider" error
   - Should display financial news feed
   - Should filter by category

3. **Portfolio Page** (`/portfolio`)
   - Should load without "usePortfolio must be used within PortfolioProvider" error
   - Should display holdings and calculations
   - Should show asset distribution

4. **Advisor Page** (`/advisor`)
   - Should load without errors
   - Should display chat interface

## Browser Console Checklist

After deploying, check browser console for:
- ✓ No React context errors
- ✓ No hydration warnings
- ✓ localStorage data persisting correctly
- ✓ No "Provider" in error messages

## File Structure After Fix

```
✅ FIXED STRUCTURE:
├── app/
│   ├── layout.tsx (✅ ROOT - INCLUDES <Providers>)
│   ├── providers.jsx (✅ ROOT PROVIDER - all contexts)
│   ├── dashboard/
│   │   ├── layout.jsx (✅ Clean - no duplicate providers)
│   │   └── page.jsx
│   ├── playground/page.jsx (✅ Has access to all contexts)
│   ├── news/page.jsx (✅ Has access to all contexts)
│   ├── portfolio/page.jsx (✅ Has access to all contexts)
│   ├── advisor/page.jsx (✅ No context needed - standalone)
│   └── (auth)/
│       └── pages...
```

## Provider Nesting Order

The order of provider nesting matters for performance:

```jsx
<UserProvider>           // 1. User data (needed by others)
  <PortfolioProvider>    // 2. Portfolio (uses user data)
    <PlaygroundProvider> // 3. Playground (independent)
      <NewsProvider>     // 4. News (independent)
        {children}
      </NewsProvider>
    </PlaygroundProvider>
  </PortfolioProvider>
</UserProvider>
```

This hierarchy ensures data flows correctly without circular dependencies.

## Performance Considerations

- Context providers re-render when state changes
- All consumers below that provider re-render
- Use `useCallback` and `useMemo` to optimize if needed
- Consider splitting large contexts if they change frequently

## Prevention Tips

1. **Always place providers at appropriate level:**
   - Global state → Root layout
   - Feature-specific state → Feature layout
   - Component state → useContext + useReducer

2. **Use TypeScript for context hooks:**
   ```jsx
   export const usePlayground = (): PlaygroundContextType => {
     const context = React.useContext(PlaygroundContext);
     if (!context) {
       throw new Error('usePlayground must be used within PlaygroundProvider');
     }
     return context;
   };
   ```

3. **Document context dependencies:**
   ```jsx
   /**
    * @requires PlaygroundProvider - Must be wrapped by Playground provider
    * @throws {Error} If used outside PlaygroundProvider
    */
   export function PlaygroundPage() { ... }
   ```

## Summary

This fix resolves the context provider issue by:
1. Moving all providers to application root
2. Ensuring all pages have access to required contexts
3. Adding proper Suspense boundaries for loading states
4. Following Next.js best practices for context usage
5. Maintaining clean, scalable architecture
