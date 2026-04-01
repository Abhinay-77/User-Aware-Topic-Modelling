import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { topicAPI, dashboardAPI } from '../../services/api'
import { Line, Bar, Radar, Doughnut } from 'react-chartjs-2'
import {
  Chart as ChartJS, CategoryScale, LinearScale, PointElement,
  LineElement, BarElement, RadialLinearScale, ArcElement,
  Title, Tooltip, Legend, Filler,
} from 'chart.js'
import './Dashboard.css'
import LiveAnalysis from '../../components/LiveAnalysis'

ChartJS.register(
  CategoryScale, LinearScale, PointElement, LineElement,
  BarElement, RadialLinearScale, ArcElement, Title, Tooltip, Legend, Filler
)

const ResearcherDashboard = () => {
  const [selectedDataset, setSelectedDataset] = useState('')
  const [textColumn, setTextColumn] = useState('text')
  const [userColumn, setUserColumn]   = useState('user_id')   // NEW
  const [timeColumn, setTimeColumn]   = useState('timestamp') // NEW
  const [language, setLanguage] = useState('english')
  const [numTopics, setNumTopics] = useState(10)
  const [loading, setLoading] = useState(false)
  const [results, setResults] = useState(null)
  const [dashboardData, setDashboardData] = useState(null)
  const [datasets, setDatasets] = useState([])
  const [activeTab, setActiveTab] = useState('topics')  // NEW: tabs
  const [selectedUser, setSelectedUser] = useState(null) // NEW
  const navigate = useNavigate()

  useEffect(() => { loadDashboardData(); loadDatasets() }, [])

  const loadDashboardData = async () => {
    try {
      const r = await dashboardAPI.getResearcherDashboard()
      setDashboardData(r.data)
      if (r.data.latest_result) setResults(r.data.latest_result)
    } catch (e) { console.error(e) }
  }

  const loadDatasets = async () => {
    try {
      const r = await topicAPI.getDatasets()
      setDatasets(r.data.datasets)
    } catch (e) { console.error(e) }
  }

  const handleFileUpload = async (e) => {
    const f = e.target.files[0]
    if (!f) return
    setLoading(true)
    const fd = new FormData()
    fd.append('file', f)
    try {
      await topicAPI.uploadDataset(fd)
      loadDatasets()
      alert('Dataset uploaded successfully')
    } catch (e) {
      alert('Upload error: ' + (e.response?.data?.detail || e.message))
    } finally { setLoading(false) }
  }

  const handleRunModeling = async () => {
    setLoading(true)
    try {
      console.log('[RESEARCH] Starting topic modeling with:', {
        dataset_id: selectedDataset || 'default',
        num_topics: numTopics,
        text_column: textColumn,
        user_column: userColumn,
        time_column: timeColumn,
      })
      const r = await topicAPI.runModeling({
        dataset_id: selectedDataset || null,
        text_column: textColumn,
        user_column: userColumn || null,
        time_column: timeColumn || null,
        language,
        num_topics: numTopics,
      })
      console.log('[RESEARCH] Modeling complete. Results:', r.data.results)
      setResults(r.data.results)
      setActiveTab('topics')  // Reset to topics tab
      loadDashboardData()  // Refresh dashboard metrics
    } catch (e) {
      console.error('[RESEARCH_ERROR]', e)
      alert('Error: ' + (e.response?.data?.detail || e.message))
    } finally { setLoading(false) }
  }

  const handleDownload = async (format) => {
    if (!results?._id) return
    try {
      const r = await topicAPI.downloadResults(results._id, format)
      const url = window.URL.createObjectURL(new Blob([r.data]))
      const a = document.createElement('a')
      a.href = url
      a.setAttribute('download', `topic_results.${format}`)
      document.body.appendChild(a)
      a.click()
    } catch (e) { alert('Download error') }
  }

  // ── Chart data helpers ──────────────────────────────────────────────────

  const topicBarData = results?.topics ? {
    labels: results.topics.map(t => t.name.split(':')[1]?.trim() || t.name).slice(0, 12),
    datasets: [{
      label: 'Document Count',
      data: results.topics.map(t => t.count).slice(0, 12),
      backgroundColor: results.topics.slice(0,12).map((_, i) =>
        `hsl(${(i * 30) % 360}, 65%, 55%)`
      ),
    }]
  } : null

  const evolutionData = results?.topic_evolution
    ? (() => {
        const keys = Object.keys(results.topic_evolution).slice(0, 5)
        const allDates = keys.length ? results.topic_evolution[keys[0]].dates : []
        return {
          labels: allDates,
          datasets: keys.map((name, i) => ({
            label: name.split(':')[1]?.trim() || name,
            data: results.topic_evolution[name].counts,
            borderColor: `hsl(${i*60}, 70%, 50%)`,
            backgroundColor: `hsla(${i*60}, 70%, 50%, 0.1)`,
            fill: true, tension: 0.4,
          }))
        }
      })()
    : null

  // Per-user entropy data
  const userEntropyData = results?.user_entropy
    ? (() => {
        const entries = Object.entries(results.user_entropy)
          .sort((a, b) => b[1] - a[1])
          .slice(0, 15)
        return {
          labels: entries.map(([uid]) => uid),
          datasets: [{
            label: 'Topic Entropy H(u)',
            data: entries.map(([, h]) => h),
            backgroundColor: entries.map(([, h]) =>
              h > 2.5 ? 'rgba(59,130,246,0.7)' : h > 1.5 ? 'rgba(34,197,94,0.7)' : 'rgba(251,146,60,0.7)'
            ),
          }]
        }
      })()
    : null

  // Selected user's topic distribution donut
  const userDistData = selectedUser && results?.user_distributions?.[selectedUser]
    ? (() => {
        const dist = results.user_distributions[selectedUser]
        const topicLookup = Object.fromEntries((results.topics || []).map(t => [String(t.topic_id), t.keywords[0] || `Topic ${t.topic_id}`]))
        const sorted = Object.entries(dist).sort((a, b) => b[1] - a[1]).slice(0, 8)
        return {
          labels: sorted.map(([tid]) => topicLookup[tid] || `T${tid}`),
          datasets: [{
            data: sorted.map(([, p]) => p),
            backgroundColor: sorted.map((_, i) => `hsl(${i*45}, 65%, 55%)`),
          }]
        }
      })()
    : null

  // Drift timeline for selected user
  const driftData = selectedUser && results?.temporal_drift?.[selectedUser]
    ? (() => {
        const timeline = results.temporal_drift[selectedUser].drift_timeline || []
        const meanDrift = results.temporal_drift[selectedUser].mean_drift || 0
        
        return {
          labels: timeline.map(d => d.to),
          datasets: [
            {
              label: `Interest Drift (JSD) - Mean: ${meanDrift}`,
              data: timeline.map(d => d.jsd),
              borderColor: 'rgba(59, 130, 246, 1)',
              backgroundColor: 'rgba(59, 130, 246, 0.1)',
              fill: true,
              tension: 0.4,
              pointRadius: 6,
              pointHoverRadius: 8,
              pointBackgroundColor: 'rgba(59, 130, 246, 1)',
              borderWidth: 3,
            }
          ]
        }
      })()
    : null

  const chartOpts = (title) => ({
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top',
        labels: { font: { family: "'Inter', sans-serif", size: 12 }, usePointStyle: true }
      },
      title: {
        display: !!title,
        text: title,
        font: { family: "'Inter', sans-serif", size: 16, weight: '600' },
        padding: { bottom: 20 }
      },
      tooltip: {
        backgroundColor: 'rgba(15, 23, 42, 0.9)',
        padding: 12,
        titleFont: { size: 14 },
        bodyFont: { size: 13 },
        cornerRadius: 8,
      }
    },
    scales: {
      y: {
        beginAtZero: true,
        grid: { color: '#f1f5f9' },
        ticks: { font: { size: 11 } }
      },
      x: {
        grid: { display: false },
        ticks: { font: { size: 11 } }
      }
    }
  })

  const users = results?.user_entropy ? Object.keys(results.user_entropy) : []

  return (
    <div className="dashboard-container">
      {/* ── Header ──────────────────────────────────────────────────── */}
      <div className="dashboard-header">
        <h1>🔬 Researcher Dashboard</h1>
        <button className="logout-btn" onClick={() => { localStorage.clear(); navigate('/login') }}>
          Logout
        </button>
      </div>

      {/* ── Stats row ───────────────────────────────────────────────── */}
      {results && (
        <div className="stats-grid">
          <div className="stat-card">
            <div className="stat-icon">📊</div>
            <div className="stat-number">{results.topics?.length ?? 0}</div>
            <div className="stat-label">Topics Found</div>
            <div className="stat-subtext" style={{ fontSize: '12px', color: '#666' }}>
              (Requested: {results.num_topics || numTopics})
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-icon">👥</div>
            <div className="stat-number">{Object.keys(results.user_entropy || {}).length}</div>
            <div className="stat-label">Users Profiled</div>
            <div className="stat-subtext" style={{ fontSize: '12px', color: '#666' }}>
              {results.total_documents ? `Out of ${results.total_documents} docs` : ''}
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-icon">🎯</div>
            <div className="stat-number">{results.topic_diversity > 0 ? results.topic_diversity?.toFixed(3) : 'N/A'}</div>
            <div className="stat-label">Topic Diversity</div>
          </div>
          <div className="stat-card">
            <div className="stat-icon">⚠️</div>
            <div className="stat-number">{results.outlier_count ?? 0}</div>
            <div className="stat-label">Outlier Docs</div>
            <div className="stat-subtext" style={{ fontSize: '12px', color: '#666' }}>
              {results.total_documents ? `${((( results.outlier_count || 0) / results.total_documents) * 100).toFixed(1)}%` : ''}
            </div>
          </div>
        </div>
      )}

      <div className="dashboard-grid">
        {/* ── Controls panel ──────────────────────────────────────────── */}
        <div className="control-panel card">
          <h2>Run Topic Modeling</h2>

          <label>Dataset</label>
          <select value={selectedDataset} onChange={e => setSelectedDataset(e.target.value)}>
            <option value="">Default (social_media_samples.csv)</option>
            {datasets.map(d => <option key={d._id} value={d._id}>{d.filename}</option>)}
          </select>

          <label>Upload New Dataset (CSV)</label>
          <input type="file" accept=".csv" onChange={handleFileUpload} />

          <div style={{display:'grid', gridTemplateColumns:'1fr 1fr', gap:'8px'}}>
            <div>
              <label>Text Column</label>
              <input value={textColumn} onChange={e => setTextColumn(e.target.value)} placeholder="text" />
            </div>
            <div>
              <label>User ID Column</label>
              <input value={userColumn} onChange={e => setUserColumn(e.target.value)} placeholder="user_id" />
            </div>
            <div>
              <label>Timestamp Column</label>
              <input value={timeColumn} onChange={e => setTimeColumn(e.target.value)} placeholder="timestamp" />
            </div>
            <div>
              <label>Max Topics</label>
              <input type="number" value={numTopics} min={3} max={50}
                onChange={e => setNumTopics(parseInt(e.target.value))} />
            </div>
          </div>

          <button className="run-btn" onClick={handleRunModeling} disabled={loading}>
            {loading ? '⏳ Running...' : '▶ Run Topic Modeling'}
          </button>

          {results && (
            <div style={{marginTop:'12px', display:'flex', gap:'8px'}}>
              <button className="download-btn" onClick={() => handleDownload('csv')}>⬇ CSV</button>
              <button className="download-btn" onClick={() => handleDownload('json')}>⬇ JSON</button>
            </div>
          )}
        </div>

        {/* ── Results area ────────────────────────────────────────────── */}
        {results && (
          <div className="results-panel card">
            {/* Tab bar */}
            <div className="tab-bar">
              {['topics', 'evolution', 'users', 'drift'].map(tab => (
                <button key={tab}
                  className={`tab-btn ${activeTab === tab ? 'active' : ''}`}
                  onClick={() => setActiveTab(tab)}>
                  {{ topics:'📊 Topics', evolution:'📈 Evolution', users:'👥 Users', drift:'🌊 Drift' }[tab]}
                </button>
              ))}
            </div>

            {/* Topics tab */}
            {activeTab === 'topics' && topicBarData && (
              <div>
                <div style={{ height: '400px', marginBottom: '30px' }}>
                  <Bar data={topicBarData} options={chartOpts('Topic Sizes (Document Count)')} />
                </div>
                <div className="topic-chips" style={{marginTop:'16px', display: 'flex', flexWrap: 'wrap', gap: '10px'}}>
                  {results.topics.slice(0,15).map(t => (
                    <div key={t.topic_id} className="topic-chip" style={{ 
                      padding: '12px 16px', borderRadius: '10px', background: '#f8fafc', 
                      border: '1px solid #e2e8f0', minWidth: '200px', flex: '1 1 calc(33% - 10px)'
                    }}>
                      <div style={{ color: '#1e40af', fontWeight: '700', fontSize: '14px', marginBottom: '4px' }}>
                        {t.name.split(':')[1]?.trim() || t.name}
                      </div>
                      <div style={{ color: '#64748b', fontSize: '12px', lineHeight: '1.4' }}>
                        {t.keywords.slice(0,5).join(', ')}
                      </div>
                      <div style={{ marginTop: '8px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <span style={{ fontSize: '11px', color: '#94a3b8' }}>ID: {t.topic_id}</span>
                        <span className="badge" style={{ background: '#eff6ff', color: '#1e40af', fontSize: '10px' }}>
                          {t.count} docs
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Evolution tab */}
            {activeTab === 'evolution' && evolutionData && (
              <div style={{ height: '450px' }}>
                <Line data={evolutionData} options={chartOpts('Topic Evolution Over Time')} />
              </div>
            )}

            {/* Users tab */}
            {activeTab === 'users' && (
              <div>
                {userEntropyData ? (
                  <div style={{ height: '400px', marginBottom: '40px' }}>
                    <Bar data={userEntropyData} options={chartOpts('User Topic Entropy (higher = broader interests)')} />
                  </div>
                ) : (
                  <p className="empty-msg">No user_id column detected. Add a "user_id" column to your CSV and re-run.</p>
                )}

                {users.length > 0 && (
                  <div style={{ background: '#f8fafc', padding: '20px', borderRadius: '12px', border: '1px solid #e2e8f0' }}>
                    <label style={{ display: 'block', marginBottom: '10px', fontWeight: '600', color: '#1e293b' }}>
                      🔍 Detailed User Profile Analysis
                    </label>
                    <select value={selectedUser || ''} onChange={e => setSelectedUser(e.target.value)}
                      style={{width:'100%', padding:'10px', borderRadius:'8px', border:'1px solid #cbd5e1', fontSize: '14px'}}>
                      <option value="">— Select a user to inspect —</option>
                      {users.map(u => <option key={u} value={u}>{u} (Entropy: {results.user_entropy[u]})</option>)}
                    </select>
                  </div>
                )}

                {userDistData && (
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1.2fr', gap: '30px', marginTop: '30px' }}>
                    <div style={{ height: '350px', background: '#fff', padding: '20px', borderRadius: '12px', border: '1px solid #e2e8f0' }}>
                      <Doughnut data={userDistData} options={{
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: { 
                          legend: { position: 'bottom', labels: { boxWidth: 12, font: { size: 11 } } },
                          title: { display: true, text: `Topic Distribution: ${selectedUser}`, font: { size: 14, weight: '600' } } 
                        }
                      }} />
                    </div>
                    {/* Add a placeholder or additional metric for the user here */}
                    <div style={{ display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
                       <div className="card" style={{ margin: 0, border: '1px solid #e2e8f0', boxShadow: 'none' }}>
                          <h4>User Summary: {selectedUser}</h4>
                          <p style={{ fontSize: '14px', color: '#64748b' }}>
                            This user shows a preference for topics related to <strong>{userDistData.labels[0]}</strong>.
                            Their diversity score (Entropy) is <strong>{results.user_entropy[selectedUser]}</strong>.
                          </p>
                       </div>
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Drift tab */}
            {activeTab === 'drift' && (
              <div>
                {Object.keys(results.temporal_drift || {}).length > 0 ? (
                  <>
                    <div style={{ background: '#f0f9ff', padding: '20px', borderRadius: '12px', border: '1px solid #bae6fd', marginBottom: '30px' }}>
                      <label style={{ display: 'block', marginBottom: '10px', fontWeight: '600', color: '#0369a1' }}>
                        🌊 Temporal Topic Drift Analysis (User-Specific)
                      </label>
                      <select value={selectedUser || ''}
                        onChange={e => setSelectedUser(e.target.value)}
                        style={{width:'100%', padding:'10px', borderRadius:'8px', border:'1px solid #7dd3fc', fontSize: '14px'}}>
                        <option value="">— Select user to visualize interest shift —</option>
                        {Object.keys(results.temporal_drift).map(u => (
                          <option key={u} value={u}>
                            {u} (Mean Interest Shift: {results.temporal_drift[u].mean_drift})
                          </option>
                        ))}
                      </select>
                    </div>
                    {driftData ? (
                      <div style={{ height: '400px' }}>
                        <Line data={driftData} options={chartOpts('Interest Shift Over Time (Jensen-Shannon Divergence)')} />
                      </div>
                    ) : (
                      <div className="empty-state" style={{ padding: '60px' }}>
                        <p>Select a user above to visualize how their interests changed over time.</p>
                      </div>
                    )}
                  </>
                ) : (
                  <p className="empty-msg">
                    No temporal drift data. Make sure your CSV has a timestamp column and re-run with "Timestamp Column" filled in.
                  </p>
                )}
              </div>
            )}
          </div>
        )}
        {activeTab === 'live' && (
          <LiveAnalysis results={results} />
        )}

        {!results && !loading && (
          <div className="card empty-state">
            <p>📂 Upload a CSV dataset and click <strong>Run Topic Modeling</strong> to begin.</p>
            <p style={{marginTop:'8px', color:'#888', fontSize:'13px'}}>
              CSV should have columns: <code>text</code>, <code>user_id</code>, <code>timestamp</code>
            </p>
          </div>
        )}
      </div>

      {/* ── Previous results ────────────────────────────────────────── */}
      {dashboardData?.recent_results?.length > 0 && (
        <div className="card" style={{marginTop:'20px'}}>
          <h3>Recent Runs</h3>
          <table style={{width:'100%', borderCollapse:'collapse', fontSize:'13px'}}>
            <thead>
              <tr style={{background:'#f8f9fa'}}>
                {['Date','Topics','Diversity','Users Profiled','Outliers'].map(h => (
                  <th key={h} style={{padding:'8px', border:'1px solid #e5e7eb', textAlign:'left'}}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {dashboardData.recent_results.map((r, i) => (
                <tr key={i}>
                  <td style={{padding:'8px', border:'1px solid #e5e7eb'}}>{r.timestamp?.slice(0,10)}</td>
                  <td style={{padding:'8px', border:'1px solid #e5e7eb'}}>{r.topics?.length ?? '—'}</td>
                  <td style={{padding:'8px', border:'1px solid #e5e7eb'}}>{r.topic_diversity > 0 ? r.topic_diversity : '—'}</td>
                  <td style={{padding:'8px', border:'1px solid #e5e7eb'}}>{Object.keys(r.user_distributions || {}).length || '—'}</td>
                  <td style={{padding:'8px', border:'1px solid #e5e7eb'}}>{r.outlier_count ?? '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

export default ResearcherDashboard
