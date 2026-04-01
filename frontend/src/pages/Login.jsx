import React, { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { authAPI } from '../services/api'
import './Auth.css'

const Login = () => {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [showPassword, setShowPassword] = useState(false)
  const navigate = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      const response = await authAPI.login({ email, password })
      const { token, user } = response.data

      localStorage.setItem('token', token)
      localStorage.setItem('user', JSON.stringify(user))
      localStorage.setItem('userRole', user.role)

      // Map backend role to frontend route
      const role = user.role
      const routeMap = {
        'general': 'user',
        'researcher': 'researcher',
        'analyst': 'analyst',
        'business': 'analyst'
      }
      navigate(`/dashboard/${routeMap[role] || 'user'}`)
    } catch (err) {
      setError(err.response?.data?.detail || 'Login failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-container">
      <div className="auth-wrapper">
        {/* Left Side - Branding */}
        <div className="auth-branding">
          <div className="brand-content">
            <div className="brand-icon">🔍</div>
            <h1>User-Aware BERTopic</h1>
            <p className="brand-tagline">Advanced Topic Modeling & Analysis</p>
            <div className="brand-features">
              <div className="feature-item">
                <span className="feature-icon">✨</span>
                <span>Smart Translation</span>
              </div>
              <div className="feature-item">
                <span className="feature-icon">🎯</span>
                <span>Topic Detection</span>
              </div>
              <div className="feature-item">
                <span className="feature-icon">📊</span>
                <span>Analytics Dashboard</span>
              </div>
            </div>
          </div>
        </div>

        {/* Right Side - Login Form */}
        <div className="auth-form-container">
          <div className="auth-card">
            <div className="auth-header">
              <h2>Welcome Back 👋</h2>
              <p>Login to your account to continue</p>
            </div>

            {error && (
              <div className="alert alert-error">
                <span className="alert-icon">⚠️</span>
                <span>{error}</span>
              </div>
            )}

            <form onSubmit={handleSubmit} className="auth-form">
              <div className="form-group">
                <label htmlFor="email">Email Address</label>
                <div className="input-wrapper">
                  <span className="input-icon">📧</span>
                  <input
                    id="email"
                    type="email"
                    placeholder="Enter your email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                    className="auth-input"
                  />
                </div>
              </div>

              <div className="form-group">
                <label htmlFor="password">Password</label>
                <div className="input-wrapper">
                  <span className="input-icon">🔒</span>
                  <input
                    id="password"
                    type={showPassword ? 'text' : 'password'}
                    placeholder="Enter your password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                    className="auth-input"
                  />
                  <button
                    type="button"
                    className="toggle-password"
                    onClick={() => setShowPassword(!showPassword)}
                  >
                    {showPassword ? '👁️' : '👁️‍🗨️'}
                  </button>
                </div>
              </div>

              <button 
                type="submit" 
                disabled={loading} 
                className="auth-button btn-primary"
              >
                {loading ? (
                  <>
                    <span className="spinner"></span>
                    Logging in...
                  </>
                ) : (
                  <>Login to Dashboard</>
                )}
              </button>
            </form>

            <div className="auth-divider">or</div>

            <div className="auth-footer">
              <p>Don't have an account? <Link to="/signup" className="link-primary">Create one</Link></p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Login
