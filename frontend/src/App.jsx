import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider } from './context/AuthContext'
import ProtectedRoute from './components/ProtectedRoute'
import LoginPage from './components/auth/LoginPage'
import SignupPage from './components/auth/SignupPage'
import Dashboard from './components/dashboard/Dashboard'
import GmailConnect from './components/gmail/GmailConnect'
import TosAnalyzer from './components/tos/TosAnalyzer'
import CostIntelligencePage from './components/intelligence/CostIntelligencePage'

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/signup" element={<SignupPage />} />
          <Route path="/dashboard" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
          <Route path="/gmail" element={<ProtectedRoute><GmailConnect /></ProtectedRoute>} />
          <Route path="/tos" element={<ProtectedRoute><TosAnalyzer /></ProtectedRoute>} />
          <Route path="/intelligence" element={<ProtectedRoute><CostIntelligencePage /></ProtectedRoute>} />
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  )
}
