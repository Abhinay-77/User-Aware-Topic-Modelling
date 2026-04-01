import React, { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { authAPI } from '../services/api'
import './Auth.css'

const Signup = () => {
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    name: '',
    role: 'general',
  })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [showPassword, setShowPassword] = useState(false)
  const navigate = useNavigate()

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value })
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const response = await authAPI.signup(formData)
      const { token, user } = response.data
      localStorage.setItem('token', token)
      localStorage.setItem('user', JSON.stringify(user))
      localStorage.setItem('userRole', user.role)
      const routeMap = { 'general': 'user', 'researcher': 'researcher', 'analyst': 'analyst' }
      navigate(`/dashboard/${routeMap[user.role] || 'user'}`)
    } catch (err) {
      setError(err.response?.data?.detail || 'Signup failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-container">
      <div className="auth-wrapper">
        <div className="auth-branding">
          <div className="brand-content">
            <div className="brand-icon">🚀</div>
            <h1>Join Us Today</h1>
            <p className="brand-tagline">Get started with Advanced Topic Modeling</p>
            <div className="brand-features">
              <div className="feature-item"><span className="feature-icon">👤</span><span>User Dashboard</span></div>
              <div className="feature-item"><span className="feature-icon">🔬</span><span>Research Tools</span></div>
              <div className="feature-item"><span className="feature-icon">📊</span><span>Analyst Analytics</span></div>
            </div>
          </div>
        </div>
        <div className="auth-form-container">
          <div className="auth-card">
            <div className="auth-header">
              <h2>Create Account ✨</h2>
              <p>Sign up to start using our platform</p>
            </div>
            {error && (
              <div className="alert alert-error">
                <span className="alert-icon">⚠️</span>
                <span>{error}</span>
              </div>
            )}
            <form onSubmit={handleSubmit} className="auth-form">
              <div className="form-group">
                <label htmlFor="name">Full Name</label>
                <div className="input-wrapper">
                  <span className="input-icon">👤</span>
                  <input id="name" type="text" name="name" placeholder="Enter your full name"
                    value={formData.name} onChange={handleChange} required className="auth-input" />
                </div>
              </div>
              <div className="form-group">
                <label htmlFor="email">Email Address</label>
                <div className="input-wrapper">
                  <span className="input-icon">📧</span>
                  <input id="email" type="email" name="email" placeholder="Enter your email"
                    value={formData.email} onChange={handleChange} required className="auth-input" />
                </div>
              </div>
              <div className="form-group">
                <label htmlFor="password">Password</label>
                <div className="input-wrapper">
                  <span className="input-icon">🔒</span>
                  <input id="password" type={showPassword ? 'text' : 'password'} name="password"
                    placeholder="Create a strong password" value={formData.password}
                    onChange={handleChange} required className="auth-input" />
                  <button type="button" className="toggle-password"
                    onClick={() => setShowPassword(!showPassword)}>
                    {showPassword ? '👁️' : '👁️‍🗨️'}
                  </button>
                </div>
              </div>
              <div className="form-group">
                <label htmlFor="role">Account Type</label>
                <div className="input-wrapper">
                  <span className="input-icon">🏷️</span>
                  <select id="role" name="role" value={formData.role}
                    onChange={handleChange} className="auth-input auth-select">
                    <option value="general">👤 General User - Basic features</option>
                    <option value="researcher">🔬 Researcher - Advanced analysis</option>
                    <option value="analyst">📊 Analyst - Analytics & insights</option>
                  </select>
                </div>
              </div>
              <div className="role-description">
                {formData.role === 'general' && <p>📝 Perfect for users who want to translate and analyze text</p>}
                {formData.role === 'researcher' && <p>🔬 For researchers conducting advanced topic modeling studies</p>}
                {formData.role === 'analyst' && <p>📊 For analyst users analyzing consumer insights and trends</p>}
              </div>
              <button type="submit" disabled={loading} className="auth-button btn-primary btn-large">
                {loading ? <><span className="spinner"></span>Creating Account...</> : <>Create My Account</>}
              </button>
            </form>
            <div className="auth-divider">or</div>
            <div className="auth-footer">
              <p>Already have an account? <Link to="/login" className="link-primary">Sign in</Link></p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Signup
