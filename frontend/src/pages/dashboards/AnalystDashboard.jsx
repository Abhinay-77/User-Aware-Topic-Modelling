import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { dashboardAPI } from '../../services/api'
import { Bar, Line, Doughnut, Pie, Radar } from 'react-chartjs-2'
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

const BusinessDashboard = () => {
  const [dashboardData, setDashboardData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [loadingData, setLoadingData] = useState(true)
  const [csvFile, setCsvFile] = useState(null)
  const [uploadStatus, setUploadStatus] = useState('')
  const [modelingLoading, setModelingLoading] = useState(false)
  const [modelingStatus, setModelingStatus] = useState('')
  const [lastUploadedTopics, setLastUploadedTopics] = useState(0)
  const navigate = useNavigate()

  useEffect(() => {
    loadDashboardData()
  }, [])

  const loadDashboardData = async () => {
    try {
      setLoadingData(true)
      console.log('[DASHBOARD_LOAD] ========== LOADING DASHBOARD DATA ==========')
      const response = await dashboardAPI.getBusinessDashboard()
      console.log('[DASHBOARD_LOAD] Raw response:', response.data)
      console.log('[DASHBOARD_LOAD] Trending topics:', response.data.trending_topics)
      console.log('[DASHBOARD_LOAD] Topics count:', response.data.trending_topics?.length)
      console.log('[DASHBOARD_LOAD] Sentiment data:', response.data.sentiment_data)
      console.log('[DASHBOARD_LOAD] Total users:', response.data.total_users)
      console.log('[DASHBOARD_LOAD] Total translations:', response.data.total_translations)
      console.log('[DASHBOARD_LOAD] Avg engagement:', response.data.avg_engagement)
      console.log('[DASHBOARD_LOAD] Time trends:', response.data.time_based_trends)
      console.log('[DASHBOARD_LOAD] ========== DASHBOARD DATA LOADED SUCCESSFULLY ==========')
      setDashboardData(response.data)
    } catch (error) {
      console.error('[DASHBOARD_LOAD_ERROR] ========== ERROR LOADING DASHBOARD ==========')
      console.error('[DASHBOARD_LOAD_ERROR] Status:', error.response?.status)
      console.error('[DASHBOARD_LOAD_ERROR] Detail:', error.response?.data?.detail)
      console.error('[DASHBOARD_LOAD_ERROR] Full error:', error.response?.data)
      console.error('[DASHBOARD_LOAD_ERROR] Message:', error.message)
      console.error('[DASHBOARD_LOAD_ERROR] ================================================')
    } finally {
      setLoadingData(false)
    }
  }

  const handleLogout = () => {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    localStorage.removeItem('userRole')
    navigate('/login')
  }

  const handleSocialMediaUpload = async (e) => {
    const file = e.target.files[0]
    if (!file) return

    // Basic client-side validation
    if (!file.name.toLowerCase().endsWith('.csv')) {
      setUploadStatus('❌ Error: Only CSV files are supported')
      return
    }

    setLoading(true)
    setUploadStatus('⏳ Uploading and processing data...')
    
    const formData = new FormData()
    formData.append('file', file)

    try {
      console.log('[UPLOAD] ========== SOCIAL MEDIA DATA UPLOAD STARTED ==========')
      console.log('[UPLOAD] File:', file.name, 'Size:', file.size)
      
      const response = await dashboardAPI.analyzeSocialMedia(formData)
      console.log('[UPLOAD] Success:', response.data)
      
      const summary = response.data.summary || {}
      setUploadStatus(`✅ Success: Processed ${summary.total_records} records. Found ${summary.topics_found} topics.`)
      
      // Reset file input
      e.target.value = null
      
      // Reload dashboard data to show new charts
      await loadDashboardData()
    } catch (error) {
      console.error('[UPLOAD_ERROR]', error)
      const errorMsg = error.response?.data?.detail || error.message || 'Unknown server error'
      setUploadStatus(`❌ Error: ${errorMsg}`)
    } finally {
      setLoading(false)
    }
  }

  const handleTopicsCsvUpload = async (e) => {
    const file = e.target.files[0]
    if (!file) return

    setLoading(true)
    setUploadStatus('')
    const formData = new FormData()
    formData.append('file', file)

    try {
      console.log('[UPLOAD] ========== MARKET TOPICS CSV UPLOAD STARTED ==========')
      const response = await dashboardAPI.uploadTopicsCSV(formData)
      setUploadStatus(`✅ Success: ${response.data.message}`)
      await loadDashboardData()
    } catch (error) {
      console.error('[UPLOAD_ERROR]', error)
      const errorMsg = error.response?.data?.detail || error.message || 'Unknown error'
      setUploadStatus(`❌ Error: ${errorMsg}`)
    } finally {
      setLoading(false)
    }
  }

  const handleRunTopicModeling = async () => {
    setModelingLoading(true)
    setModelingStatus('⟳ Processing topic data...')
    try {
      console.log('[MODELING] ========== PROCESSING TOPICS ==========')
      console.log('[MODELING] Last uploaded topics:', lastUploadedTopics)
      
      // For analysts, we aggregate and process the uploaded topics
      console.log('[MODELING] Waiting 1.5 seconds for data aggregation...')
      await new Promise(resolve => setTimeout(resolve, 1500))
      
      console.log('[MODELING] Reloading dashboard with processed topics...')
      await loadDashboardData()
      
      console.log('[MODELING] ========== PROCESSING COMPLETE ==========')
      setModelingStatus('✅ Topics processed and dashboard updated!')
      
      // Clear status after 3 seconds
      setTimeout(() => setModelingStatus(''), 3000)
    } catch (error) {
      console.error('[MODELING_ERROR] Processing failed:', error)
      const errorMsg = error.response?.data?.detail || error.message || 'Unknown error'
      setModelingStatus(`❌ Error: ${errorMsg}`)
    } finally {
      setModelingLoading(false)
    }
  }

  const getTopicFrequencyData = () => {
    if (!dashboardData?.trending_topics || dashboardData.trending_topics.length === 0) {
      return null
    }

    const topics = dashboardData.trending_topics.slice(0, 10)

    return {
      labels: topics.map((t) => t.topic),
      datasets: [
        {
          label: 'Frequency',
          data: topics.map((t) => t.frequency),
          backgroundColor: 'rgba(102, 126, 234, 0.6)',
          borderColor: 'rgba(102, 126, 234, 1)',
          borderWidth: 1,
        },
      ],
    }
  }

  const getSentimentData = () => {
    if (!dashboardData?.sentiment_data) return null

    const sentiment = dashboardData.sentiment_data

    return {
      labels: ['Positive', 'Neutral', 'Negative'],
      datasets: [
        {
          data: [sentiment.positive, sentiment.neutral, sentiment.negative],
          backgroundColor: ['#4caf50', '#ff9800', '#f44336'],
          borderWidth: 2,
        },
      ],
    }
  }

  const getTimeTrendsData = () => {
    if (!dashboardData?.time_based_trends) return null

    const trends = dashboardData.time_based_trends

    return {
      labels: trends.map((t) => t.date),
      datasets: [
        {
          label: 'Topic Activity',
          data: trends.map((t) => t.count),
          borderColor: 'rgba(153, 102, 255, 1)',
          backgroundColor: 'rgba(153, 102, 255, 0.1)',
          tension: 0.4,
        },
      ],
    }
  }

  const getUserActivityData = () => {
    if (!dashboardData?.activity_trends) return null

    return {
      labels: dashboardData.activity_trends.map(d => d.date),
      datasets: [
        {
          label: 'Topic Uploads',
          data: dashboardData.activity_trends.map(d => d.uploads),
          borderColor: '#667eea',
          backgroundColor: 'rgba(102, 126, 234, 0.1)',
          tension: 0.4,
          fill: true,
        },
        {
          label: 'User Conversions',
          data: dashboardData.activity_trends.map(d => d.conversions),
          borderColor: '#764ba2',
          backgroundColor: 'rgba(118, 75, 162, 0.1)',
          tension: 0.4,
          fill: true,
        },
      ],
    }
  }

  const getRoleDistributionData = () => {
    if (!dashboardData?.users_data) return null

    const roleCounts = {}
    dashboardData.users_data.forEach(user => {
      const role = user.role || 'general'
      roleCounts[role] = (roleCounts[role] || 0) + 1
    })

    return {
      labels: Object.keys(roleCounts),
      datasets: [
        {
          data: Object.values(roleCounts),
          backgroundColor: ['#667eea', '#764ba2', '#f093fb'],
          borderWidth: 2,
        },
      ],
    }
  }

  const getMarketInsightData = () => {
    // Simulated market segment analysis
    return {
      labels: ['Tech', 'Healthcare', 'Finance', 'E-commerce', 'Social'],
      datasets: [
        {
          label: 'Market Mention Volume',
          data: [45, 38, 52, 41, 35],
          backgroundColor: [
            'rgba(102, 126, 234, 0.6)',
            'rgba(118, 75, 162, 0.6)',
            'rgba(240, 147, 251, 0.6)',
            'rgba(79, 172, 254, 0.6)',
            'rgba(67, 233, 123, 0.6)',
          ],
          borderColor: [
            'rgba(102, 126, 234, 1)',
            'rgba(118, 75, 162, 1)',
            'rgba(240, 147, 251, 1)',
            'rgba(79, 172, 254, 1)',
            'rgba(67, 233, 123, 1)',
          ],
          borderWidth: 2,
        },
      ],
    }
  }

  const getCompetitorAnalysisData = () => {
    // Simulated competitor topic share
    return {
      labels: ['Competitor A', 'Competitor B', 'Our Brand', 'Competitor C', 'Competitor D'],
      datasets: [
        {
          label: 'Topic Dominance %',
          data: [22, 19, 28, 18, 13],
          backgroundColor: [
            'rgba(255, 99, 132, 0.6)',
            'rgba(54, 162, 235, 0.6)',
            'rgba(75, 192, 192, 0.6)',
            'rgba(255, 206, 86, 0.6)',
            'rgba(153, 102, 255, 0.6)',
          ],
          borderWidth: 2,
        },
      ],
    }
  }

  const getConsumerSentimentTrendData = () => {
    // Weekly sentiment trend for business decisions
    const weeks = ['Week 1', 'Week 2', 'Week 3', 'Week 4']
    return {
      labels: weeks,
      datasets: [
        {
          label: 'Positive Sentiment %',
          data: [65, 68, 72, 75],
          borderColor: 'rgba(76, 175, 80, 1)',
          backgroundColor: 'rgba(76, 175, 80, 0.1)',
          tension: 0.4,
          fill: true,
          pointRadius: 5,
          pointBackgroundColor: 'rgba(76, 175, 80, 1)',
        },
        {
          label: 'Negative Sentiment %',
          data: [20, 18, 15, 12],
          borderColor: 'rgba(244, 67, 54, 1)',
          backgroundColor: 'rgba(244, 67, 54, 0.1)',
          tension: 0.4,
          fill: true,
          pointRadius: 5,
          pointBackgroundColor: 'rgba(244, 67, 54, 1)',
        },
      ],
    }
  }


  return (
    <div className="dashboard analyst-dashboard">
      <header className="dashboard-header analyst-header">
        <div>
          <h1>� Business Analytics Dashboard</h1>
          <p className="subtitle">Advanced Topic Modeling & Market Insights Platform</p>
        </div>
        <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
          <button 
            onClick={loadDashboardData} 
            disabled={loadingData}
            className="refresh-btn"
            title="Refresh dashboard data"
            style={{ 
              padding: '10px 18px', 
              fontSize: '14px', 
              cursor: loadingData ? 'not-allowed' : 'pointer',
              backgroundColor: 'rgba(255, 255, 255, 0.15)',
              color: 'white',
              border: '1px solid rgba(255, 255, 255, 0.3)',
              borderRadius: '6px',
              fontWeight: 'bold',
              transition: 'all 0.3s'
            }}
            onMouseEnter={(e) => e.target.style.backgroundColor = 'rgba(255, 255, 255, 0.25)'}
            onMouseLeave={(e) => e.target.style.backgroundColor = 'rgba(255, 255, 255, 0.15)'}
          >
            {loadingData ? '⟳ Refreshing...' : '🔄 Refresh'}
          </button>
          <button 
            onClick={handleLogout} 
            className="logout-btn"
            style={{ 
              padding: '10px 18px',
              backgroundColor: 'rgba(255, 59, 48, 0.2)',
              color: 'white',
              border: '1px solid rgba(255, 59, 48, 0.5)',
              fontWeight: 'bold',
              transition: 'all 0.3s'
            }}
            onMouseEnter={(e) => e.target.style.backgroundColor = 'rgba(255, 59, 48, 0.3)'}
            onMouseLeave={(e) => e.target.style.backgroundColor = 'rgba(255, 59, 48, 0.2)'}
          >
            🚪 Logout
          </button>
        </div>
      </header>

      <div className="dashboard-content">
        {loadingData && (
          <div style={{ 
            textAlign: 'center', 
            padding: '40px 20px', 
            fontSize: '18px',
            color: '#666'
          }}>
            ⟳ Loading dashboard data...
          </div>
        )}
        
        {!loadingData && (
          <>
        {/* KPI Cards */}
        <div className="stats-row kpi-row">
          <div className="stat-card stat-users">
            <div className="stat-icon">👥</div>
            <h3>Total Users</h3>
            <p className="stat-value">{dashboardData?.total_users || 0}</p>
            <p className="stat-change">Active Platform Members</p>
          </div>
          <div className="stat-card stat-translations">
            <div className="stat-icon">📝</div>
            <h3>Total Content</h3>
            <p className="stat-value">{dashboardData?.total_translations || 0}</p>
            <p className="stat-change">Items Analyzed</p>
          </div>
          <div className="stat-card stat-topics">
            <div className="stat-icon">🏆</div>
            <h3>Trending Topics</h3>
            <p className="stat-value">{dashboardData?.trending_topics?.length || 0}</p>
            <p className="stat-change">Market Trends</p>
          </div>
          <div className="stat-card stat-engagement">
            <div className="stat-icon">💯</div>
            <h3>Engagement Score</h3>
            <p className="stat-value">{dashboardData?.avg_engagement || 0}%</p>
            <p className="stat-change">Market Activity Level</p>
          </div>
        </div>

        {/* CSV Upload Section */}
        <div className="card-row" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px', marginBottom: '30px' }}>
          {/* Social Media Analysis Upload */}
          <div className="card card-upload">
            <div className="card-header">
              <h2>📤 Upload Social Media Data</h2>
              <p className="card-subtitle">Upload raw data for automated BERTopic analysis</p>
            </div>
            <div style={{ display: 'grid', gap: '16px' }}>
              <div style={{ padding: '16px', backgroundColor: '#f0fdf4', borderRadius: '8px', borderLeft: '4px solid #22c55e' }}>
                <p style={{ margin: '0 0 8px 0', color: '#166534', fontWeight: '600', fontSize: '13px' }}>📋 CSV Format Required:</p>
                <p style={{ margin: '4px 0', color: '#14532d', fontSize: '13px', fontFamily: 'monospace' }}>user_id, text, timestamp (optional)</p>
                <p style={{ margin: '4px 0', color: '#15803d', fontSize: '12px' }}>Example: "user123", "nenu movie chustunnanu", "2026-03-27"</p>
              </div>
              <input 
                type="file" 
                accept=".csv" 
                onChange={handleSocialMediaUpload} 
                disabled={loading}
                className="input input-file"
                style={{ width: '100%', cursor: loading ? 'not-allowed' : 'pointer' }}
              />
            </div>
          </div>

          {/* Pre-analyzed Topics Upload */}
          <div className="card card-upload">
            <div className="card-header">
              <h2>📊 Upload Pre-analyzed Topics</h2>
              <p className="card-subtitle">Import CSV with existing topic frequencies</p>
            </div>
            <div style={{ display: 'grid', gap: '16px' }}>
              <div style={{ padding: '16px', backgroundColor: '#f0f2ff', borderRadius: '8px', borderLeft: '4px solid #667eea' }}>
                <p style={{ margin: '0 0 8px 0', color: '#333', fontWeight: '600', fontSize: '13px' }}>📋 CSV Format Required:</p>
                <p style={{ margin: '4px 0', color: '#666', fontSize: '13px', fontFamily: 'monospace' }}>topic_id, name, keywords, count</p>
                <p style={{ margin: '4px 0', color: '#999', fontSize: '12px' }}>Example: 1, "Technology", "AI, ML, Tech", 45</p>
              </div>
              <input 
                type="file" 
                accept=".csv" 
                onChange={handleTopicsCsvUpload} 
                disabled={loading}
                className="input input-file"
                style={{ width: '100%', cursor: loading ? 'not-allowed' : 'pointer' }}
              />
            </div>
          </div>
        </div>

        {uploadStatus && (
          <div style={{ marginBottom: '24px' }} className={uploadStatus.startsWith('✅') ? 'success-message alert-success' : 'error-message alert-error'}>
            {uploadStatus}
          </div>
        )}

        {/* Trending Topics Quick View */}
        <div className="card">
          <h2>🔥 Top Trending Topics</h2>
          {dashboardData?.trending_topics && dashboardData.trending_topics.length > 0 ? (
            <div className="topics-grid">
              {dashboardData.trending_topics.slice(0, 6).map((topic, idx) => (
                <div key={idx} className="insight-card trend-card">
                  <div className="trend-rank">#{idx + 1}</div>
                  <h3>{topic.topic}</h3>
                  <p className="insight-value">{topic.frequency} mentions</p>
                  <div className="trend-bar">
                    <div className="trend-bar-fill" style={{width: `${(topic.frequency / Math.max(...dashboardData.trending_topics.map(t => t.frequency))) * 100}%`}}></div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p>No trending topics available</p>
          )}
        </div>

        {/* Charts Grid - First Row */}
        <div className="charts-grid">
          <div className="card">
            <h2>📊 Topic Frequency Analysis</h2>
            {getTopicFrequencyData() ? (
              <Bar 
                data={getTopicFrequencyData()} 
                options={{ 
                  responsive: true,
                  indexAxis: 'y',
                  plugins: {
                    legend: { display: false }
                  },
                  scales: {
                    x: { beginAtZero: true }
                  }
                }} 
              />
            ) : (
              <p>No data available</p>
            )}
          </div>

          <div className="card">
            <h2>😊 Sentiment Breakdown</h2>
            {getSentimentData() ? (
              <div className="chart-container">
                <Doughnut 
                  data={getSentimentData()} 
                  options={{ 
                    responsive: true,
                    plugins: {
                      legend: {
                        position: 'bottom'
                      }
                    }
                  }} 
                />
              </div>
            ) : (
              <p>No data available</p>
            )}
          </div>
        </div>

        {/* Charts Grid - Second Row */}
        <div className="charts-grid">
          <div className="card">
            <h2>📈 Activity Timeline</h2>
            {getTimeTrendsData() ? (
              <Line 
                data={getTimeTrendsData()} 
                options={{ 
                  responsive: true,
                  plugins: {
                    legend: { display: true }
                  }
                }} 
              />
            ) : (
              <p>No data available</p>
            )}
          </div>

          <div className="card">
            <h2>🎯 User Activity Trends</h2>
            {getUserActivityData() ? (
              <Line 
                data={getUserActivityData()} 
                options={{ 
                  responsive: true,
                  plugins: {
                    legend: { display: true }
                  }
                }} 
              />
            ) : (
              <p>No data available</p>
            )}
          </div>
        </div>

        {/* Market Insights Row */}
        <div className="charts-grid">
          <div className="card">
            <h2>🎯 Market Segment Analysis</h2>
            <Bar 
              data={getMarketInsightData()} 
              options={{ 
                responsive: true,
                plugins: {
                  title: {
                    display: true,
                    text: 'Topic Volume by Market Segment',
                    font: { size: 12 }
                  },
                  legend: { display: false }
                },
                scales: {
                  y: { beginAtZero: true }
                }
              }} 
            />
          </div>

          <div className="card">
            <h2>🏆 Competitor Landscape</h2>
            <Bar 
              data={getCompetitorAnalysisData()} 
              options={{ 
                responsive: true,
                indexAxis: 'y',
                plugins: {
                  title: {
                    display: true,
                    text: 'Brand Topic Dominance Comparison',
                    font: { size: 12 }
                  },
                  legend: { display: false }
                },
                scales: {
                  x: { beginAtZero: true, max: 100 }
                }
              }} 
            />
          </div>
        </div>

        {/* Sentiment Trends */}
        <div className="card">
          <h2>💭 Consumer Sentiment Evolution</h2>
          <Line 
            data={getConsumerSentimentTrendData()} 
            options={{ 
              responsive: true,
              plugins: {
                title: {
                  display: true,
                  text: 'Weekly Sentiment Trend Analysis for Decision Making',
                  font: { size: 12 }
                },
                legend: { display: true, position: 'top' }
              },
              scales: {
                y: {
                  beginAtZero: true,
                  max: 100,
                  ticks: {
                    callback: function(value) {
                      return value + '%'
                    }
                  }
                }
              }
            }} 
          />
        </div>

        {/* User Role Distribution */}
        <div className="card">
          <h2>👤 User Role Distribution</h2>
          {getRoleDistributionData() ? (
            <div className="chart-container">
              <Pie 
                data={getRoleDistributionData()} 
                options={{ 
                  responsive: true,
                  plugins: {
                    legend: {
                      position: 'right'
                    },
                    title: {
                      display: true,
                      text: 'Distribution of User Types'
                    }
                  }
                }} 
              />
            </div>
          ) : (
            <p>No data available</p>
          )}
        </div>

        {/* Users Overview Table */}
        <div className="card">
          <h2>📋 User Management</h2>
          {dashboardData?.users_data && dashboardData.users_data.length > 0 ? (
            <div style={{ overflowX: 'auto' }}>
              <table className="table table-modern">
                <thead>
                  <tr>
                    <th>👤 Name</th>
                    <th>📧 Email</th>
                    <th>🏷️ Role</th>
                    <th>📝 Translations</th>
                    <th>🏆 Topics</th>
                    <th>📅 Joined</th>
                  </tr>
                </thead>
                <tbody>
                  {dashboardData.users_data.slice(0, 20).map((user) => (
                    <tr key={user.id}>
                      <td><strong>{user.name || 'N/A'}</strong></td>
                      <td>{user.email}</td>
                      <td>
                        <span className={`role-badge role-${user.role}`}>
                          {user.role}
                        </span>
                      </td>
                      <td><span className="count-badge">{user.translations_count}</span></td>
                      <td><span className="count-badge">{user.topics_count}</span></td>
                      <td>{user.created_at ? new Date(user.created_at).toLocaleDateString() : 'N/A'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p>No users data available</p>
          )}
        </div>

        {/* Consolidated Customer Insights & Feedback at the bottom */}
        <div className="dashboard-row">
          <div className="card">
            <h2>💡 Customer Insights & Feedback</h2>
            <div className="insights-list">
              {dashboardData?.customer_insights && dashboardData.customer_insights.length > 0 ? (
                dashboardData.customer_insights.map((insight, idx) => (
                  <div key={idx} className="insight-item" style={{ 
                    padding: '15px', borderBottom: '1px solid #eee', 
                    display: 'flex', justifyContent: 'space-between', alignItems: 'center' 
                  }}>
                    <div>
                      <h4 style={{ margin: '0 0 5px 0', color: '#1e3a8a' }}>{insight.topic}</h4>
                      <p style={{ margin: 0, fontSize: '14px', color: '#64748b' }}>{insight.insight || insight.text}</p>
                    </div>
                    <div className={`badge badge-${insight.sentiment.toLowerCase()}`} style={{
                      padding: '4px 12px', borderRadius: '20px', fontSize: '12px', fontWeight: '600',
                      backgroundColor: insight.sentiment === 'Positive' ? '#dcfce7' : (insight.sentiment === 'Negative' ? '#fee2e2' : '#fef3c7'),
                      color: insight.sentiment === 'Positive' ? '#166534' : (insight.sentiment === 'Negative' ? '#991b1b' : '#92400e')
                    }}>
                      {insight.sentiment}
                    </div>
                  </div>
                ))
              ) : (
                <p className="no-data">No specific insights detected yet</p>
              )}
            </div>
          </div>
        </div>
          </>
        )}
      </div>
    </div>
  )
}

export default BusinessDashboard
