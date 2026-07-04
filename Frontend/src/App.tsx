import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { useAppStore } from './store/useAppStore'
import { LandingPage } from './pages/LandingPage'
import { Onboarding } from './pages/Onboarding'
import { AppLayout } from './components/layout/AppLayout'
import { PricesPage } from './pages/PricesPage'
import { TrendsPage } from './pages/TrendsPage'
import { PredictionsPage } from './pages/PredictionsPage'
import { ConfidencePage } from './pages/ConfidencePage'
import { PaperTradingPage } from './pages/PaperTradingPage'
import { NewsPage } from './pages/NewsPage'
import { ContributePage } from './pages/ContributePage'
import { ToastContainer } from './components/ui/ToastContainer'

// Protected route wrapper
function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const isAuthenticated = useAppStore((s) => s.isAuthenticated)
  if (!isAuthenticated) return <Navigate to="/" replace />
  return <>{children}</>
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/onboarding" element={<Onboarding />} />
        <Route
          path="/app"
          element={
            <ProtectedRoute>
              <AppLayout />
            </ProtectedRoute>
          }
        >
          <Route index element={<Navigate to="/app/prices" replace />} />
          <Route path="prices" element={<PricesPage />} />
          <Route path="trends" element={<TrendsPage />} />
          <Route path="predictions" element={<PredictionsPage />} />
          <Route path="confidence" element={<ConfidencePage />} />
          <Route path="trading" element={<PaperTradingPage />} />
          <Route path="news" element={<NewsPage />} />
          <Route path="contribute" element={<ContributePage />} />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
      {/* Global toast notifications — outside router so they survive transitions */}
      <ToastContainer />
    </BrowserRouter>
  )
}

export default App
