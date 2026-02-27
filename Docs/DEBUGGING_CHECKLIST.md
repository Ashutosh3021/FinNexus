# Debugging Checklist - Context Provider Issues

## Immediate Verification Steps

### Step 1: Verify Application Loads
- [ ] Open browser DevTools (F12)
- [ ] Navigate to `/playground`
- [ ] **Expected:** Page loads without errors
- [ ] **Bad:** Error about "usePlayground must be used within PlaygroundProvider"

### Step 2: Check Console for Errors
```
Browser Console Checklist:
[ ] No red error messages
[ ] No yellow warnings about hydration
[ ] No "[v0]" debug logs remaining
[ ] No "Provider" mentioned in any error
```

### Step 3: Verify Each Page Loads
```
Testing Pages:
[ ] /playground - loads and shows prediction interface
[ ] /news - loads and shows news feed
[ ] /portfolio - loads and shows holdings
[ ] /advisor - loads and shows chat interface
[ ] /dashboard - loads and shows overview
[ ] /learn - loads and shows lessons
```

### Step 4: Test Data Persistence
```
Testing localStorage:
[ ] Refresh page - data persists
[ ] Add item to portfolio - appears after refresh
[ ] Make prediction - appears in history after refresh
[ ] Clear localStorage - data resets properly
```

### Step 5: Check Network Issues
```
Network Tab:
[ ] All JS bundles load (green)
[ ] No 404 errors for chunks
[ ] No failed imports of context files
[ ] No CORS errors
```

## If You See Errors

### Error: "usePlayground must be used within PlaygroundProvider"

**Diagnostics:**
1. Check if `providers.jsx` exists at `/app/providers.jsx`
   ```bash
   ls -la app/providers.jsx
   ```

2. Verify root layout imports providers:
   ```jsx
   // Should see in app/layout.tsx:
   import { Providers } from './providers'
   <Providers>
     {children}
   </Providers>
   ```

3. Check context exports:
   ```bash
   grep -n "export const PlaygroundProvider" context/PlaygroundContext.jsx
   grep -n "export const usePlayground" context/PlaygroundContext.jsx
   ```

**Quick Fix:**
```jsx
// app/layout.tsx should have:
import { Providers } from './providers'

export default function RootLayout({ children }) {
  return (
    <html>
      <body>
        <Providers>
          {children}
        </Providers>
      </body>
    </html>
  )
}
```

---

### Error: "ReferenceError: localStorage is not defined"

**Cause:** Code running on server instead of client
**Solution:** Already fixed with `useEffect` guards:
```jsx
useEffect(() => {
  // This only runs on client
  localStorage.setItem('key', data);
}, [data]);
```

**Check:**
- [ ] All contexts have `'use client'` directive
- [ ] localStorage access is inside `useEffect`
- [ ] Not accessing localStorage in component render

---

### Error: "Hydration Mismatch"

**Appearance:** 
- Text content differs between server and client
- Styling doesn't match after load

**Solution:** Already implemented with isHydrated:
```jsx
const [isHydrated, setIsHydrated] = useState(false);
useEffect(() => setIsHydrated(true), []);
if (!isHydrated) return <LoadingUI />;
```

**Verification:**
- [ ] All pages have hydration guard
- [ ] LoadingUI matches actual UI dimensions
- [ ] No useEffect runs before hydration check

---

### Error: "Maximum call stack size exceeded"

**Cause:** Infinite loop in context updates
**Solution:** Check reducer logic doesn't create cycles
```jsx
// Check these don't dispatch themselves:
case 'ACTION':
  dispatch({ type: 'ACTION' }); // ❌ INFINITE LOOP
  return state;
```

---

## Performance Debugging

### Check If Context Updates Cause Re-renders

Add debug logging:
```jsx
export const PlaygroundProvider = ({ children }) => {
  const [state, dispatch] = useReducer(playgroundReducer, initialState);
  
  console.log('[v0] PlaygroundProvider state updated:', state); // Debug only
  
  // ... rest of code
};
```

Then check console:
- [ ] Log appears only when state actually changes
- [ ] Not logging excessively (no infinite loops)
- [ ] All needed data is in the log

### Check Re-render Frequency

Use React DevTools Profiler:
1. Open DevTools → Profiler tab
2. Click record
3. Interact with page
4. Stop recording
5. Look for excessive re-renders

**Expected:** 
- [ ] Pages re-render 1-2 times on load
- [ ] State changes cause related pages to re-render
- [ ] No re-renders on every frame

---

## Provider Chain Verification

### Verify Provider Order

Run in browser console:
```javascript
// Check if contexts are accessible
console.log('[v0] Testing context access...');

// This will work if providers are properly set up:
// (You'd need to manually test since contexts are not exported)
```

### Check Context Value Structure

Add to each context hook:
```jsx
export const usePlayground = () => {
  const context = React.useContext(PlaygroundContext);
  if (!context) {
    console.error('[v0] PlaygroundContext not found in tree');
    throw new Error('usePlayground must be used within PlaygroundProvider');
  }
  console.log('[v0] PlaygroundContext available:', context);
  return context;
};
```

Check console for:
- [ ] `[v0] PlaygroundContext available: {...}`
- [ ] All expected properties in the object
- [ ] No undefined values

---

## Routing Verification

### Check Route-to-Layout Mapping

```
Expected Layout Chain:
/playground → RootLayout → <Providers> → PlaygroundProvider ✓
/news       → RootLayout → <Providers> → NewsProvider ✓
/portfolio  → RootLayout → <Providers> → PortfolioProvider ✓
```

Verify with:
1. Navigate to `/playground`
2. Open DevTools
3. React tab → Components tree
4. Look for: Providers → PlaygroundProvider → PlaygroundPage ✓

---

## localStorage Debugging

### Check What's Stored

```javascript
// In browser console:
console.log('[v0] localStorage contents:');
console.log('User:', JSON.parse(localStorage.getItem('finnexus_user')));
console.log('Portfolio:', JSON.parse(localStorage.getItem('finnexus_portfolio')));
console.log('Playground:', JSON.parse(localStorage.getItem('finnexus_playground')));
console.log('News:', JSON.parse(localStorage.getItem('finnexus_news')));
```

**Expected:** All should return objects with valid data

### Clear localStorage Manually

If data is corrupted:
```javascript
localStorage.clear();
location.reload();
```

---

## Build Verification

### Check TypeScript Compilation

```bash
# In project directory
npm run build
```

Look for:
- [ ] No TypeScript errors
- [ ] No import errors for contexts
- [ ] Successful build completion

### Check Runtime Errors

```bash
npm run dev
```

In console:
- [ ] No "Cannot find module" errors
- [ ] No syntax errors
- [ ] No unresolved imports

---

## Network Verification

### Check Component Bundles Load

Open DevTools → Network tab:
1. Clear filters
2. Reload page
3. Search for ".js" files
4. Look for:
   - [ ] `_next/static/chunks/*` files load (green)
   - [ ] Chunk sizes reasonable (not > 500KB)
   - [ ] No 404 errors

### Check API Calls (if any)

- [ ] No API errors in Network tab
- [ ] All requests complete
- [ ] No timeouts

---

## File System Verification

### Check All Files Exist

```bash
# Check key files exist:
[ ] app/providers.jsx - Root provider component
[ ] app/layout.tsx - Updated with Providers
[ ] app/dashboard/layout.jsx - Cleaned version
[ ] app/playground/page.jsx - Updated
[ ] app/news/page.jsx - Updated
[ ] app/portfolio/page.jsx - Updated
[ ] app/advisor/page.jsx - Updated
[ ] context/PlaygroundContext.jsx - Has provider & hook
[ ] context/NewsContext.jsx - Has provider & hook
[ ] context/PortfolioContext.jsx - Has provider & hook
[ ] context/UserContext.jsx - Has provider & hook
```

### Check File Contents

```bash
# Verify providers.jsx has all 4 context providers:
grep -c "Provider" app/providers.jsx  # Should return 4

# Verify layout.tsx imports Providers:
grep "import.*Providers" app/layout.tsx

# Verify Suspense added to pages:
grep -c "Suspense" app/playground/page.jsx  # Should return 1+
```

---

## Common Issues and Quick Fixes

| Issue | Location | Fix |
|-------|----------|-----|
| usePlayground error | playground/page.jsx | Check root layout has Providers |
| useNews error | news/page.jsx | Check root layout has Providers |
| usePortfolio error | portfolio/page.jsx | Check root layout has Providers |
| Data not persisting | Any page | Check localStorage keys match |
| Page flashes | Any page | Check Suspense fallback exists |
| Wrong data after refresh | Any page | Check localStorage parsing in context |

---

## Testing Checklist Summary

```
Quick Test (2 minutes):
[ ] Navigate to /playground
[ ] Should load without context error
[ ] Refresh page
[ ] Data should persist

Thorough Test (10 minutes):
[ ] Test all 5 pages: playground, news, portfolio, advisor, learn
[ ] Add data on each page
[ ] Refresh browser
[ ] Verify data persists
[ ] Check console for errors
[ ] Verify localStorage contents
[ ] Test localStorage clear

Full Test (30 minutes):
[ ] All above
[ ] Test on mobile via DevTools
[ ] Test on slow network (DevTools throttling)
[ ] Test with localStorage disabled
[ ] Build and test production version
```

---

## Rollback Instructions

If issues persist after all checks:

1. **Revert providers.jsx:**
   ```bash
   rm app/providers.jsx
   ```

2. **Revert layout.tsx:**
   - Remove: `import { Providers } from './providers'`
   - Remove: `<Providers>...</Providers>` wrapper
   - Return to original `{children}`

3. **Revert dashboard/layout.jsx:**
   - Add back original provider imports
   - Wrap children with all 4 providers

---

## Support Resources

If all else fails:
1. Check CONTEXT_PROVIDER_FIX.md for detailed explanation
2. Check ARCHITECTURE_DIAGRAM.md for visual structure
3. Review BEFORE_AFTER.md for code changes
4. Examine error stack trace line by line
5. Check Next.js documentation on layouts: https://nextjs.org/docs/app/building-your-application/routing/layouts-and-templates
6. Check React Context documentation: https://react.dev/reference/react/useContext
