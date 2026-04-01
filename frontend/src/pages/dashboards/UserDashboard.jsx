import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { translationAPI, dashboardAPI } from '../../services/api'
import { Line, Bar, Doughnut, Radar, Scatter } from 'react-chartjs-2'
import BulkTransliterator from '../../components/BulkTransliterator'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  RadarController,
  Title,
  Tooltip,
  Legend,
  Filler,
} from 'chart.js'
import './Dashboard.css'

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  RadarController,
  Title,
  Tooltip,
  Legend,
  Filler
)

const UserDashboard = () => {
  const [text, setText] = useState('')
  const [translation, setTranslation] = useState(null)
  const [loading, setLoading] = useState(false)
  const [dashboardData, setDashboardData] = useState(null)
  const [error, setError] = useState('')
  const navigate = useNavigate()

  useEffect(() => {
    loadDashboardData()
  }, [])

  const loadDashboardData = async () => {
    try {
      const response = await dashboardAPI.getUserDashboard()
      setDashboardData(response.data)
    } catch (error) {
      console.error('Error loading dashboard:', error)
    }
  }

  const handleTranslate = async () => {
    const trimmedText = text.trim()
    if (!trimmedText) {
      setError('Please enter some Tanglish text to translate')
      return
    }

    setLoading(true)
    setError('')
    setTranslation(null)
    
    try {
      console.log('[USER_DASHBOARD] Processing text:', trimmedText)
      const response = await translationAPI.translate({ text: trimmedText })
      
      const resData = response.data.translation
      const finalResults = Array.isArray(resData) ? resData : [resData]
      
      if (!finalResults || finalResults.length === 0) {
        setError('No results returned from the server.')
      } else {
        setTranslation(finalResults)
        // Refresh dashboard data to show the new translation in charts and history
        setTimeout(() => loadDashboardData(), 500)
      }
    } catch (error) {
      console.error('Translation error:', error)
      const serverError = error.response?.data?.detail || 'Server error occurred. Please try again.'
      setError(serverError)
    } finally {
      setLoading(false)
    }
  }

  const handleLogout = () => {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    localStorage.removeItem('userRole')
    navigate('/login')
  }

  const getTranslationTimelineData = () => {
    if (!dashboardData?.translation_timeline || dashboardData.translation_timeline.length === 0) {
      return null
    }

    return {
      labels: dashboardData.translation_timeline.map(t => t.date),
      datasets: [
        {
          label: 'Translations',
          data: dashboardData.translation_timeline.map(t => t.count),
          borderColor: 'rgba(102, 126, 234, 1)',
          backgroundColor: 'rgba(102, 126, 234, 0.1)',
          tension: 0.4,
          fill: true,
        },
      ],
    }
  }

  const getTopicDistributionData = () => {
    if (!dashboardData?.top_topics || dashboardData.top_topics.length === 0) {
      return null
    }

    return {
      labels: dashboardData.top_topics.map(t => t.keyword),
      datasets: [
        {
          label: 'Topic Frequency',
          data: dashboardData.top_topics.map(t => t.count),
          backgroundColor: [
            'rgba(102, 126, 234, 0.6)',
            'rgba(118, 75, 162, 0.6)',
            'rgba(255, 99, 132, 0.6)',
            'rgba(54, 162, 235, 0.6)',
            'rgba(255, 206, 86, 0.6)',
          ],
          borderColor: [
            'rgba(102, 126, 234, 1)',
            'rgba(118, 75, 162, 1)',
            'rgba(255, 99, 132, 1)',
            'rgba(54, 162, 235, 1)',
            'rgba(255, 206, 86, 1)',
          ],
          borderWidth: 1,
        },
      ],
    }
  }

  const getTopicDoughnutData = () => {
    if (!dashboardData?.top_topics || dashboardData.top_topics.length === 0) {
      return null
    }

    return {
      labels: dashboardData.top_topics.map(t => t.keyword),
      datasets: [
        {
          data: dashboardData.top_topics.map(t => t.count),
          backgroundColor: [
            '#667eea',
            '#764ba2',
            '#f093fb',
            '#4facfe',
            '#43e97b',
          ],
          borderWidth: 2,
        },
      ],
    }
  }

  const getLanguageDistributionData = () => {
    // Get language pair distribution (Tanglish to Telugu to English)
    return {
      labels: ['Tanglish Inputs', 'Telugu Outputs', 'English Outputs'],
      datasets: [
        {
          label: 'Language Processing Pipeline',
          data: [
            dashboardData?.total_translations || 0,
            dashboardData?.total_translations || 0,
            dashboardData?.total_translations || 0,
          ],
          backgroundColor: [
            'rgba(230, 124, 115, 0.7)',
            'rgba(255, 152, 0, 0.7)',
            'rgba(76, 175, 80, 0.7)',
          ],
          borderColor: [
            'rgba(230, 124, 115, 1)',
            'rgba(255, 152, 0, 1)',
            'rgba(76, 175, 80, 1)',
          ],
          borderWidth: 2,
        },
      ],
    }
  }

  const getAccuracyTrendData = () => {
    if (!dashboardData?.accuracy_trend || dashboardData.accuracy_trend.length === 0) {
      return null
    }

    return {
      labels: dashboardData.accuracy_trend.map(d => d.day),
      datasets: [
        {
          label: 'Transliteration Accuracy',
          data: dashboardData.accuracy_trend.map(d => d.transliteration),
          borderColor: 'rgba(102, 126, 234, 1)',
          backgroundColor: 'rgba(102, 126, 234, 0.1)',
          tension: 0.4,
          fill: true,
          pointRadius: 5,
          pointBackgroundColor: 'rgba(102, 126, 234, 1)',
        },
        {
          label: 'Translation Accuracy',
          data: dashboardData.accuracy_trend.map(d => d.translation),
          borderColor: 'rgba(118, 75, 162, 1)',
          backgroundColor: 'rgba(118, 75, 162, 0.1)',
          tension: 0.4,
          fill: true,
          pointRadius: 5,
          pointBackgroundColor: 'rgba(118, 75, 162, 1)',
        },
      ],
    }
  }


  return (
    <div className="dashboard user-dashboard">
      <header className="dashboard-header user-header">
        <div>
          <h1>👤 General User Dashboard</h1>
          <p className="subtitle">Your Translation & Topic Analysis Hub</p>
        </div>
        <button onClick={handleLogout} className="logout-btn">Logout</button>
      </header>

      <div className="dashboard-content">
        {/* Statistics Overview */}
        <div className="stats-row">
          <div className="stat-card stat-translations">
            <div className="stat-icon">📊</div>
            <h3>Total Translations</h3>
            <p className="stat-value">{dashboardData?.total_translations || 0}</p>
          </div>
          <div className="stat-card stat-topics">
            <div className="stat-icon">🏷️</div>
            <h3>Topics Detected</h3>
            <p className="stat-value">{dashboardData?.top_topics?.length || 0}</p>
          </div>
          <div className="stat-card stat-streak">
            <div className="stat-icon">🔥</div>
            <h3>Active Days</h3>
            <p className="stat-value">{dashboardData?.active_days || 0}</p>
          </div>
        </div>

        {/* Main Processing Area */}
        <div className="processing-grid" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '30px', marginBottom: '30px' }}>
          {/* Translation Input Card */}
          <div className="card card-primary" style={{ height: 'fit-content' }}>
            <div className="card-header">
              <h2>✨ Instant Translate & Detect</h2>
              <p className="card-subtitle">Convert Tanglish text to Telugu script and identify topics</p>
            </div>
            <div style={{ position: 'relative' }}>
              <textarea
                className="text-input"
                placeholder="Type your Tanglish here (e.g., nenu movie chustunnanu)..."
                value={text}
                onChange={(e) => setText(e.target.value)}
                rows={6}
                style={{ width: '100%', marginBottom: '15px' }}
              />
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '12px', color: '#64748b' }}>
                  {text.length} characters
                </span>
                <button 
                  onClick={handleTranslate} 
                  disabled={loading || !text.trim()} 
                  className={`btn btn-primary ${loading ? 'btn-loading' : ''}`}
                  style={{ minWidth: '180px' }}
                >
                  {loading ? '⏳ Processing...' : '🚀 Process Text'}
                </button>
              </div>
            </div>
            {error && (
              <div className="error-message" style={{ 
                marginTop: '15px', padding: '10px 15px', backgroundColor: '#fef2f2', 
                border: '1px solid #fee2e2', borderRadius: '8px', color: '#dc2626', fontSize: '14px' 
              }}>
                ⚠️ {error}
              </div>
            )}
          </div>

          {/* Results Area */}
          <div className="results-area">
            {!translation && !loading && (
              <div className="card card-empty" style={{ 
                height: '100%', display: 'flex', flexDirection: 'column', 
                alignItems: 'center', justifyContent: 'center', color: '#94a3b8',
                border: '2px dashed #e2e8f0', background: '#f8fafc'
              }}>
                <div style={{ fontSize: '48px', marginBottom: '15px' }}>📝</div>
                <p style={{ fontWeight: 500 }}>No processing results yet</p>
                <p style={{ fontSize: '13px' }}>Enter text on the left to see results here</p>
              </div>
            )}

            {loading && (
              <div className="card card-loading" style={{ 
                height: '100%', display: 'flex', flexDirection: 'column', 
                alignItems: 'center', justifyContent: 'center', background: '#f8fafc'
              }}>
                <div className="spinner" style={{ 
                  width: '40px', height: '40px', border: '4px solid #e2e8f0', 
                  borderTop: '4px solid #3b82f6', borderRadius: '50%', 
                  animation: 'spin 1s linear infinite', marginBottom: '15px' 
                }}></div>
                <p style={{ fontWeight: 500, color: '#3b82f6' }}>Analyzing your text...</p>
              </div>
            )}

            {translation && (
              <div className="results-container" style={{ maxHeight: '500px', overflowY: 'auto' }}>
                <h3 style={{ marginBottom: '15px', color: '#1e3a8a', display: 'flex', justifyContent: 'space-between' }}>
                  <span>✨ Results</span>
                  <span style={{ fontSize: '13px', fontWeight: 'normal', color: '#64748b' }}>
                    {translation.length} statement{translation.length > 1 ? 's' : ''}
                  </span>
                </h3>
                {translation.map((item, index) => (
                  <div key={index} className="result-card" style={{ 
                    marginBottom: '15px', padding: '16px', borderRadius: '12px', 
                    border: '1px solid #e2e8f0', background: '#fff', boxShadow: '0 2px 8px rgba(0,0,0,0.05)'
                  }}>
                    <div className="result-header" style={{ marginBottom: '12px', display: 'flex', justifyContent: 'space-between' }}>
                      <span className="badge" style={{ backgroundColor: '#eff6ff', color: '#1e40af' }}>Line #{index + 1}</span>
                      {item.predicted_topic && (
                        <span className="badge" style={{ backgroundColor: '#f0fdf4', color: '#166534' }}>
                          📌 {item.predicted_topic.name}
                        </span>
                      )}
                    </div>
                    
                    <div className="result-body" style={{ display: 'grid', gap: '12px' }}>
                      <div className="result-item">
                        <span style={{ fontSize: '11px', color: '#64748b', fontWeight: 600, textTransform: 'uppercase' }}>Original</span>
                        <p style={{ margin: '4px 0 0', fontFamily: 'monospace', fontSize: '14px' }}>{item.tanglish_text}</p>
                      </div>
                      <div className="result-item" style={{ padding: '10px', backgroundColor: '#f8fafc', borderRadius: '8px' }}>
                        <span style={{ fontSize: '11px', color: '#1e40af', fontWeight: 600, textTransform: 'uppercase' }}>Telugu Script</span>
                        <p style={{ margin: '4px 0 0', fontFamily: 'serif', fontSize: '18px', color: '#1e40af' }}>{item.telugu_text}</p>
                      </div>
                      <div className="result-item" style={{ padding: '10px', backgroundColor: '#f0fdf4', borderRadius: '8px' }}>
                        <span style={{ fontSize: '11px', color: '#166534', fontWeight: 600, textTransform: 'uppercase' }}>English Translation</span>
                        <p style={{ margin: '4px 0 0', fontSize: '14px', color: '#14532d' }}>{item.english_text}</p>
                      </div>
                    </div>

                    {item.predicted_topic && (
                      <div className="result-footer" style={{ marginTop: '12px', paddingTop: '12px', borderTop: '1px solid #f1f5f9' }}>
                        <p style={{ fontSize: '13px', color: '#64748b', fontStyle: 'italic' }}>
                          <strong>Keywords:</strong> {item.predicted_topic.keywords?.join(', ')}
                        </p>
                        <div style={{ marginTop: '8px', height: '4px', background: '#f1f5f9', borderRadius: '2px', overflow: 'hidden' }}>
                          <div style={{ 
                            width: `${(item.predicted_topic.probability || 0) * 100}%`, 
                            height: '100%', background: '#22c55e' 
                          }}></div>
                        </div>
                        <p style={{ fontSize: '11px', color: '#94a3b8', textAlign: 'right', marginTop: '4px' }}>
                          {Math.round((item.predicted_topic.probability || 0) * 100)}% match confidence
                        </p>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Tools Section */}
        <div className="tools-section" style={{ marginBottom: '30px' }}>
          <div className="card">
            <div className="card-header">
              <h2>🔤 Bulk Management</h2>
              <p className="card-subtitle">Manage high-volume transliteration and data uploads</p>
            </div>
            <BulkTransliterator />
          </div>
        </div>

        {/* Analytics Section */}
        <div className="analytics-section">
          <div className="section-header" style={{ marginBottom: '20px' }}>
            <h2>📈 Personal Analytics</h2>
            <p className="subtitle">Insights from your processing activity</p>
          </div>
          
          <div className="charts-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', gap: '20px' }}>
            <div className="card">
              <h3>Topic Distribution</h3>
              {getTopicDistributionData() ? (
                <Bar 
                  data={getTopicDistributionData()} 
                  options={{ 
                    responsive: true,
                    indexAxis: 'y',
                    plugins: { legend: { display: false } }
                  }} 
                />
              ) : (
                <p className="no-data">Processing data required for topics</p>
              )}
            </div>

            <div className="card">
              <h3>Translation Activity</h3>
              {getTranslationTimelineData() ? (
                <Line 
                  data={getTranslationTimelineData()} 
                  options={{ 
                    responsive: true,
                    scales: { y: { beginAtZero: true } }
                  }} 
                />
              ) : (
                <p className="no-data">Activity history not found</p>
              )}
            </div>

            <div className="card">
              <h3>Language Pipeline Distribution</h3>
              <Bar 
                data={getLanguageDistributionData()} 
                options={{ 
                  responsive: true,
                  plugins: { legend: { display: false } }
                }} 
              />
            </div>

            <div className="card">
              <h3>System Accuracy Trend (%)</h3>
              {getAccuracyTrendData() ? (
                <Line 
                  data={getAccuracyTrendData()} 
                  options={{ 
                    responsive: true,
                    scales: { y: { min: 60, max: 100 } }
                  }} 
                />
              ) : (
                <p className="no-data">Accuracy data not available</p>
              )}
            </div>
          </div>
        </div>

        {/* History Table */}
        <div className="card" style={{ marginTop: '30px' }}>
          <div className="card-header">
            <h2>📜 Recent Processing History</h2>
          </div>
          {dashboardData?.recent_translations && dashboardData.recent_translations.length > 0 ? (
            <div style={{ overflowX: 'auto' }}>
              <table className="table table-modern">
                <thead>
                  <tr>
                    <th>Original Text</th>
                    <th>Telugu</th>
                    <th>English</th>
                    <th>Detected Topic</th>
                    <th>Date</th>
                  </tr>
                </thead>
                <tbody>
                  {dashboardData.recent_translations.map((trans) => (
                    <tr key={trans._id}>
                      <td style={{ fontSize: '13px' }} title={trans.tanglish_text}>{trans.tanglish_text?.substring(0, 40)}{trans.tanglish_text?.length > 40 ? '...' : ''}</td>
                      <td style={{ fontFamily: 'serif', fontSize: '16px' }} title={trans.telugu_text}>{trans.telugu_text?.substring(0, 30)}{trans.telugu_text?.length > 30 ? '...' : ''}</td>
                      <td style={{ fontSize: '13px' }} title={trans.english_text}>{trans.english_text?.substring(0, 40)}{trans.english_text?.length > 40 ? '...' : ''}</td>
                      <td>
                        {trans.predicted_topic && (
                          <span className="badge badge-topic" style={{ background: '#eff6ff', color: '#1e40af' }}>
                            {trans.predicted_topic.name}
                          </span>
                        )}
                      </td>
                      <td style={{ fontSize: '12px', color: '#64748b' }}>
                        {new Date(trans.timestamp).toLocaleDateString()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="no-data">No history available</p>
          )}
        </div>
      </div>

      <style dangerouslySetInnerHTML={{ __html: `
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
        .user-dashboard {
          background-color: #f8fafc;
          min-height: 100vh;
        }
        .processing-grid {
          align-items: start;
        }
        .btn-loading {
          opacity: 0.7;
          cursor: not-allowed;
        }
        .no-data {
          text-align: center;
          padding: 40px 20px;
          color: #94a3b8;
          font-style: italic;
        }
        .badge {
          padding: 4px 10px;
          border-radius: 9999px;
          font-size: 11px;
          font-weight: 600;
          text-transform: uppercase;
        }
      `}} />
    </div>
  )
}

export default UserDashboard
