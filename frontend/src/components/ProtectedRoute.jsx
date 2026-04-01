import React, { useEffect, useState } from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import { authAPI } from '../services/api'

const ProtectedRoute = ({ children }) => {
  const [isAuthenticated, setIsAuthenticated] = useState(null)
  const [user, setUser] = useState(null)
  const location = useLocation()

  useEffect(() => {
    const token = localStorage.getItem('token')

    if (!token) {
      setIsAuthenticated(false)
      return
    }

    authAPI
      .getMe()
      .then((response) => {
        setUser(response.data)
        setIsAuthenticated(true)
      })
      .catch(() => {
        setIsAuthenticated(false)
        localStorage.removeItem('token')
        localStorage.removeItem('user')
      })
  }, [])

  if (isAuthenticated === null) {
    return <div>Loading...</div>
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  const userRole = user?.role || localStorage.getItem('userRole')

  const roleToRoute = {
    general: 'user',
    researcher: 'researcher',
    analyst: 'analyst'
  }

  const correctRoute = `/dashboard/${roleToRoute[userRole] || 'user'}`
  const currentPath = location.pathname

  // 🔥 FIX: only redirect if NOT already correct
  if (!currentPath.startsWith(correctRoute)) {
    return <Navigate to={correctRoute} replace />
  }

  return children
}

export default ProtectedRoute