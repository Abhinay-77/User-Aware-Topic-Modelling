import React, { useState, useEffect, useRef } from 'react'
import { topicAPI } from '../services/api'

// ── Simple Word Cloud renderer using Canvas ───────────────────────────────────
const WordCloud = ({ keywords }) => {
  const canvasRef = useRef(null)

  useEffect(() => {
    if (!keywords || keywords.length === 0) return
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    ctx.clearRect(0, 0, canvas.width, canvas.height)

    const colors = ['#1E3A8A','#1D4ED8','#2563EB','#3B82F6','#60A5FA','#93C5FD','#0F172A','#1E40AF']
    const maxCount = keywords[0]?.count || 100
    const cx = canvas.width / 2
    const cy = canvas.height / 2

    keywords.forEach((kw, i) => {
      const word = typeof kw === 'string' ? kw : kw.word || kw
      const count = kw.count || (100 - i * 8)
      const size = Math.max(12, Math.min(42, 12 + (count / maxCount) * 30))
      const angle = (i / keywords.length) * Math.PI * 2
      const radius = 20 + (i % 3) * 55
      const x = cx + Math.cos(angle) * radius
      const y = cy + Math.sin(angle) * radius

      ctx.font = `${size}px Calibri, sans-serif`
      ctx.fillStyle = colors[i % colors.length]
      ctx.textAlign = 'center'
      ctx.textBaseline = 'middle'
      ctx.fillText(word, x, y)
    })
  }, [keywords])

  return (
    <canvas
      ref={canvasRef}
      width={480}
      height={240}
      style={{ width: '100%', borderRadius: '8px', background: '#F0F9FF' }}
    />
  )
}

// ── Main LiveAnalysis Component ───────────────────────────────────────────────
const LiveAnalysis = ({ results }) => {
  const [inputText, setInputText]     = useState('')
  const [analysis, setAnalysis]       = useState(null)
  const [loading, setLoading]         = useState(false)
  const [error, setError]             = useState('')
  const [history, setHistory]         = useState([])

  const handleAnalyze = async () => {
    if (!inputText.trim()) return
    setLoading(true)
    setError('')
    try {
      const res = await topicAPI.analyzeText({ text: inputText.trim() })
      const data = res.data
      setAnalysis(data)
      setHistory(prev => [{ text: inputText, result: data, id: Date.now() }, ...prev.slice(0, 4)])
    } catch (e) {
      setError('Analysis failed: ' + (e.response?.data?.detail || e.message))
    } finally {
      setLoading(false)
    }
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleAnalyze()
    }
  }

  // Get word cloud data from results or from current analysis
  const wordCloudData = (() => {
    if (analysis?.topic?.keywords) {
      return analysis.topic.keywords.map((w, i) => ({ word: w, count: 100 - i * 8 }))
    }
    if (results?.topics?.length > 0) {
      return results.topics.slice(0, 12).map(t => ({
        word: t.keywords?.[0] || t.name, count: t.count
      }))
    }
    return []
  })()

  const topicColor = (name) => {
    const map = {
      technology: '#1D4ED8', cricket: '#15803D', movies: '#7C3AED',
      food: '#B45309', politics: '#DC2626', education: '#0891B2',
      health: '#059669', travel: '#D97706', general: '#6B7280',
    }
    const lower = (name || '').toLowerCase()
    for (const [k, v] of Object.entries(map)) {
      if (lower.includes(k)) return v
    }
    return '#1E3A8A'
  }

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px', marginTop: '8px' }}>

      {/* ── LEFT: Real-time analysis box ── */}
      <div style={{ background: '#fff', borderRadius: '12px', padding: '24px',
        boxShadow: '0 2px 12px rgba(0,0,0,0.08)', border: '1px solid #E2E8F0' }}>

        <h3 style={{ margin: '0 0 16px', color: '#1E3A8A', fontSize: '16px', fontWeight: 700 }}>
          🔍 Real-Time Post Analysis
        </h3>

        <div style={{ marginBottom: '12px' }}>
          <textarea
            value={inputText}
            onChange={e => setInputText(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Type any Tanglish post here... (e.g. ee tech ela undhi, nenu movie chustunnanu)"
            rows={3}
            style={{
              width: '100%', padding: '10px 12px', borderRadius: '8px',
              border: '1.5px solid #BFDBFE', fontSize: '14px', resize: 'vertical',
              fontFamily: 'inherit', boxSizing: 'border-box', outline: 'none',
            }}
          />
        </div>

        <button
          onClick={handleAnalyze}
          disabled={loading || !inputText.trim()}
          style={{
            background: loading ? '#93C5FD' : '#1D4ED8',
            color: '#fff', border: 'none', borderRadius: '8px',
            padding: '10px 24px', fontWeight: 600, fontSize: '14px',
            cursor: loading ? 'not-allowed' : 'pointer', width: '100%',
          }}
        >
          {loading ? '⏳ Analyzing...' : '▶ Analyze Post'}
        </button>

        {error && (
          <p style={{ color: '#DC2626', fontSize: '13px', marginTop: '8px' }}>{error}</p>
        )}

        {/* Result card */}
        {analysis && (
          <div style={{ marginTop: '16px', borderRadius: '10px', overflow: 'hidden',
            border: '1px solid #E2E8F0' }}>

            {/* Original */}
            <div style={{ background: '#F8FAFC', padding: '10px 14px', borderBottom: '1px solid #E2E8F0' }}>
              <span style={{ fontSize: '11px', color: '#6B7280', fontWeight: 600 }}>📝 ORIGINAL</span>
              <p style={{ margin: '4px 0 0', fontSize: '14px', color: '#0F172A' }}>{analysis.original}</p>
            </div>

            {/* Telugu */}
            <div style={{ background: '#EFF6FF', padding: '10px 14px', borderBottom: '1px solid #E2E8F0' }}>
              <span style={{ fontSize: '11px', color: '#1D4ED8', fontWeight: 600 }}>🔤 TELUGU SCRIPT</span>
              <p style={{ margin: '4px 0 0', fontSize: '16px', color: '#1E3A8A', fontFamily: 'serif' }}>
                {analysis.telugu}
              </p>
            </div>

            {/* English */}
            <div style={{ background: '#F0FDF4', padding: '10px 14px', borderBottom: '1px solid #E2E8F0' }}>
              <span style={{ fontSize: '11px', color: '#166534', fontWeight: 600 }}>🌐 ENGLISH</span>
              <p style={{ margin: '4px 0 0', fontSize: '14px', color: '#14532D' }}>{analysis.english}</p>
            </div>

            {/* Topic */}
            <div style={{ padding: '10px 14px', background: '#fff' }}>
              <span style={{ fontSize: '11px', color: '#6B7280', fontWeight: 600 }}>🏷️ PREDICTED TOPIC</span>
              <div style={{ marginTop: '6px', display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
                <span style={{
                  background: topicColor(analysis.topic?.name),
                  color: '#fff', borderRadius: '20px', padding: '4px 14px',
                  fontSize: '13px', fontWeight: 600,
                }}>
                  {analysis.topic?.name || 'General'}
                </span>
                <span style={{ fontSize: '12px', color: '#6B7280' }}>
                  Confidence: {Math.round((analysis.topic?.probability || 0) * 100)}%
                </span>
              </div>
              {analysis.topic?.keywords?.length > 0 && (
                <div style={{ marginTop: '8px', display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
                  {analysis.topic.keywords.slice(0, 5).map((kw, i) => (
                    <span key={i} style={{
                      background: '#EFF6FF', color: '#1D4ED8',
                      borderRadius: '4px', padding: '2px 8px', fontSize: '12px',
                    }}>{kw}</span>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {/* History */}
        {history.length > 1 && (
          <div style={{ marginTop: '16px' }}>
            <p style={{ fontSize: '12px', color: '#6B7280', fontWeight: 600, marginBottom: '8px' }}>
              RECENT ANALYSES
            </p>
            {history.slice(1).map(h => (
              <div key={h.id} onClick={() => { setInputText(h.text); setAnalysis(h.result) }}
                style={{ padding: '8px 12px', borderRadius: '6px', background: '#F8FAFC',
                  border: '1px solid #E2E8F0', marginBottom: '6px', cursor: 'pointer',
                  fontSize: '13px', color: '#374151' }}>
                <span style={{ color: '#6B7280' }}>"{h.text.slice(0, 40)}{h.text.length > 40 ? '...' : ''}"</span>
                {' → '}
                <span style={{ color: topicColor(h.result?.topic?.name), fontWeight: 600 }}>
                  {h.result?.topic?.name || 'General'}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* ── RIGHT: Word Cloud ── */}
      <div style={{ background: '#fff', borderRadius: '12px', padding: '24px',
        boxShadow: '0 2px 12px rgba(0,0,0,0.08)', border: '1px solid #E2E8F0' }}>

        <h3 style={{ margin: '0 0 16px', color: '#1E3A8A', fontSize: '16px', fontWeight: 700 }}>
          ☁️ Topic Word Cloud
        </h3>

        {wordCloudData.length > 0 ? (
          <>
            <WordCloud keywords={wordCloudData} />
            <div style={{ marginTop: '16px' }}>
              <p style={{ fontSize: '12px', color: '#6B7280', fontWeight: 600, marginBottom: '8px' }}>
                TOP KEYWORDS
              </p>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                {wordCloudData.slice(0, 15).map((kw, i) => (
                  <span key={i} style={{
                    background: i < 3 ? '#1E3A8A' : i < 7 ? '#1D4ED8' : '#EFF6FF',
                    color: i < 7 ? '#fff' : '#1D4ED8',
                    borderRadius: '20px', padding: '4px 12px',
                    fontSize: i < 3 ? '14px' : i < 7 ? '13px' : '12px',
                    fontWeight: i < 3 ? 700 : 400,
                  }}>
                    {typeof kw === 'string' ? kw : kw.word}
                  </span>
                ))}
              </div>
            </div>
          </>
        ) : (
          <div style={{ textAlign: 'center', padding: '60px 20px', color: '#9CA3AF' }}>
            <div style={{ fontSize: '48px', marginBottom: '12px' }}>☁️</div>
            <p style={{ fontSize: '14px' }}>
              Run topic modeling first to see the word cloud,<br />
              or analyze a post on the left to see its keywords.
            </p>
          </div>
        )}

        {/* Topic summary if results exist */}
        {results?.topics?.length > 0 && (
          <div style={{ marginTop: '20px' }}>
            <p style={{ fontSize: '12px', color: '#6B7280', fontWeight: 600, marginBottom: '8px' }}>
              TOP 5 TOPICS BY SIZE
            </p>
            {results.topics.slice(0, 5).map((t, i) => (
              <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '10px',
                marginBottom: '8px' }}>
                <span style={{ fontSize: '12px', color: '#374151', width: '140px',
                  overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {t.name}
                </span>
                <div style={{ flex: 1, background: '#E2E8F0', borderRadius: '4px', height: '8px' }}>
                  <div style={{
                    width: `${Math.min(100, (t.count / (results.topics[0]?.count || 1)) * 100)}%`,
                    background: topicColor(t.name), height: '8px', borderRadius: '4px',
                  }} />
                </div>
                <span style={{ fontSize: '12px', color: '#6B7280', width: '30px', textAlign: 'right' }}>
                  {t.count}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

export default LiveAnalysis
