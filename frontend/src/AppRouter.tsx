import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from '@store/index'
import MainLayout from '@layouts/MainLayout'
import AuthLayout from '@layouts/AuthLayout'

// Lazy load pages for code splitting
import { lazy, Suspense } from 'react'
import { CircularProgress, Box } from '@mui/material'

const Dashboard = lazy(() => import('@pages/Dashboard'))
const ActiveCalls = lazy(() => import('@pages/calls/ActiveCalls'))
const CallHistory = lazy(() => import('@pages/calls/CallHistory'))
const CallDetail = lazy(() => import('@pages/calls/CallDetail'))
const Agents = lazy(() => import('@pages/agents/Agents'))
const AgentConfig = lazy(() => import('@pages/agents/AgentConfig'))
const Customers = lazy(() => import('@pages/customers/Customers'))
const CustomerDetail = lazy(() => import('@pages/customers/CustomerDetail'))
const Reports = lazy(() => import('@pages/reports/Reports'))
const Settings = lazy(() => import('@pages/settings/Settings'))
const Login = lazy(() => import('@pages/auth/LoginSimple'))
const NotFound = lazy(() => import('@pages/NotFound'))

// Loading component
const PageLoader = () => (
  <Box
    display="flex"
    alignItems="center"
    justifyContent="center"
    minHeight="100vh"
  >
    <CircularProgress />
  </Box>
)

// Protected route wrapper
const ProtectedRoute = ({ children }: { children: React.ReactNode }) => {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated)
  
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }
  
  return <>{children}</>
}

export default function AppRouter() {
  return (
    <Suspense fallback={<PageLoader />}>
      <Routes>
        {/* Auth routes */}
        <Route element={<AuthLayout />}>
          <Route path="/login" element={<Login />} />
        </Route>

        {/* Protected routes */}
        <Route
          element={
            <ProtectedRoute>
              <MainLayout />
            </ProtectedRoute>
          }
        >
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="/dashboard" element={<Dashboard />} />
          
          {/* Call routes */}
          <Route path="/calls">
            <Route index element={<Navigate to="active" replace />} />
            <Route path="active" element={<ActiveCalls />} />
            <Route path="history" element={<CallHistory />} />
            <Route path=":id" element={<CallDetail />} />
          </Route>
          
          {/* Agent routes */}
          <Route path="/agents">
            <Route index element={<Agents />} />
            <Route path=":agentType" element={<AgentConfig />} />
          </Route>
          
          {/* Customer routes */}
          <Route path="/customers">
            <Route index element={<Customers />} />
            <Route path=":id" element={<CustomerDetail />} />
          </Route>
          
          {/* Report routes */}
          <Route path="/reports" element={<Reports />} />
          
          {/* Settings routes */}
          <Route path="/settings" element={<Settings />} />
        </Route>

        {/* 404 route */}
        <Route path="*" element={<NotFound />} />
      </Routes>
    </Suspense>
  )
}