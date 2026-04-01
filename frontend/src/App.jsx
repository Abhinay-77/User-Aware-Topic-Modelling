import React from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import Login from './pages/Login'
import Signup from './pages/Signup'
import UserDashboard from './pages/dashboards/UserDashboard'
import ResearcherDashboard from './pages/dashboards/ResearcherDashboard'
import AnalystDashboard from './pages/dashboards/AnalystDashboard'
import ProtectedRoute from './components/ProtectedRoute'
import './App.css'

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/signup" element={<Signup />} />
        <Route
          path="/dashboard/user"
          element={
            <ProtectedRoute>
              <UserDashboard />
            </ProtectedRoute>
          }
        />
        <Route
          path="/dashboard/researcher"
          element={
            <ProtectedRoute>
              <ResearcherDashboard />
            </ProtectedRoute>
          }
        />
        <Route
          path="/dashboard/analyst"
          element={
            <ProtectedRoute>
              <AnalystDashboard />
            </ProtectedRoute>
          }
        />
        {/* Redirect /dashboard/general to /dashboard/user for compatibility */}
        <Route path="/dashboard/general" element={<Navigate to="/dashboard/user" replace />} />
        {/* Redirect /dashboard/business to /dashboard/analyst for compatibility */}
        <Route path="/dashboard/business" element={<Navigate to="/dashboard/analyst" replace />} />
        <Route path="/" element={<Navigate to="/login" replace />} />
      </Routes>
    </Router>
  )
}

export default App