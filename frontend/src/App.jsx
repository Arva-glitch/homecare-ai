import { Navigate, Route, Routes, useLocation } from 'react-router-dom'
import Layout from './components/Layout'
import { PageLoader } from './components/ui'
import { useAuth } from './context/AuthContext'
import { OptionsProvider } from './context/OptionsContext'
import { ForgotPassword, Login, Register, ResetPassword } from './pages/Auth'
import Dashboard from './pages/Dashboard'
import Appliances from './pages/Appliances'
import ApplianceDetail from './pages/ApplianceDetail'
import Predictions from './pages/Predictions'
import Scheduler from './pages/Scheduler'
import Issues from './pages/Issues'
import Expenses from './pages/Expenses'
import Assistant from './pages/Assistant'
import Notifications from './pages/Notifications'
import Profile from './pages/Profile'

function Protected({ children }) {
  const { user, loading } = useAuth()
  const location = useLocation()
  if (loading) return <PageLoader label="Loading your household…" />
  if (!user) return <Navigate to="/login" replace state={{ from: location }} />
  return <OptionsProvider>{children}</OptionsProvider>
}

function PublicOnly({ children }) {
  const { user, loading } = useAuth()
  if (loading) return <PageLoader />
  return user ? <Navigate to="/" replace /> : children
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<PublicOnly><Login /></PublicOnly>} />
      <Route path="/register" element={<PublicOnly><Register /></PublicOnly>} />
      <Route path="/forgot-password" element={<ForgotPassword />} />
      <Route path="/reset-password" element={<ResetPassword />} />
      <Route element={<Protected><Layout /></Protected>}>
        <Route index element={<Dashboard />} />
        <Route path="appliances" element={<Appliances />} />
        <Route path="appliances/:id" element={<ApplianceDetail />} />
        <Route path="predictions" element={<Predictions />} />
        <Route path="scheduler" element={<Scheduler />} />
        <Route path="issues" element={<Issues />} />
        <Route path="expenses" element={<Expenses />} />
        <Route path="assistant" element={<Assistant />} />
        <Route path="notifications" element={<Notifications />} />
        <Route path="profile" element={<Profile />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
