import React, { useState, useRef } from 'react'
import { translationAPI } from '../services/api'

// ── Single result card ────────────────────────────────────────────────────────
const ResultCard = ({ result, index }) => (
  <div style={{
    borderRadius: '10px', border: '1px solid #E2E8F0',
    overflow: 'hidden', marginBottom: '12px',
    boxShadow: '0 1px 4px rgba(0,0,0,0.05)'
  }}>
    <div style={{ background: '#1E3A8A', padding: '6px 14px', display: 'flex', justifyContent: 'space-between' }}>
      <span style={{ color: '#BFDBFE', fontSize: '12px', fontWeight: 600 }}>#{index + 1}</span>
      <span style={{ color: '#93C5FD', fontSize: '11px' }}>
        {result.detected_language || 'tanglish'} · {Math.round((result.confidence || 0) * 100)}% confidence
      </span>
    </div>
    <div style={{ padding: '10px 14px', background: '#F8FAFC', borderBottom: '1px solid #E2E8F0' }}>
      <span style={{ fontSize: '11px', color: '#6B7280', fontWeight: 600 }}>📝 ORIGINAL</span>
      <p style={{ margin: '3px 0 0', fontSize: '13px', color: '#0F172A' }}>{result.original}</p>
    </div>
    <div style={{ padding: '10px 14px', background: '#EFF6FF', borderBottom: '1px solid #E2E8F0' }}>
      <span style={{ fontSize: '11px', color: '#1D4ED8', fontWeight: 600 }}>🔤 TELUGU SCRIPT</span>
      <p style={{ margin: '4px 0 0', fontSize: '16px', color: '#1E3A8A', fontFamily: 'serif' }}>
        {result.telugu_script || result.telugu || result.telugu_text}
      </p>
    </div>
    <div style={{ padding: '10px 14px', background: '#F0FDF4', borderBottom: '1px solid #E2E8F0' }}>
      <span style={{ fontSize: '11px', color: '#166534', fontWeight: 600 }}>🌐 ENGLISH</span>
      <p style={{ margin: '4px 0 0', fontSize: '14px', color: '#14532D' }}>
        {result.english_translation || result.english || result.english_text}
      </p>
    </div>
    <div style={{ padding: '10px 14px', background: '#FFF7ED' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <span style={{ fontSize: '11px', color: '#9A3412', fontWeight: 600 }}>📌 TOPIC: {result.topic_name || 'General'}</span>
        <span style={{ fontSize: '11px', color: '#C2410C' }}>{Math.round((result.probability || 0) * 100)}% match</span>
      </div>
      {result.topic_keywords && (
        <p style={{ margin: '4px 0 0', fontSize: '12px', color: '#7C2D12', fontStyle: 'italic' }}>
          Keywords: {result.topic_keywords}
        </p>
      )}
    </div>
  </div>
)

// ── Main BulkTransliterator ───────────────────────────────────────────────────
const BulkTransliterator = () => {
  // Single mode
  const [singleText, setSingleText]       = useState('')
  const [singleResult, setSingleResult]   = useState(null)
  const [singleLoading, setSingleLoading] = useState(false)

  // Bulk mode
  const [bulkResults, setBulkResults]     = useState([])
  const [bulkLoading, setBulkLoading]     = useState(false)
  const [bulkProgress, setBulkProgress]   = useState(0)
  const [bulkTotal, setBulkTotal]         = useState(0)
  const [pasteText, setPasteText]         = useState('')

  const [activeMode, setActiveMode]       = useState('single') // 'single' | 'paste' | 'csv'
  const [error, setError]                 = useState('')
  const fileRef                           = useRef(null)

  // Debug log to verify component is rendering
  console.log('[BulkTransliterator] Rendering with activeMode:', activeMode)

  // ── Single analysis ─────────────────────────────────────────────────────────
  const handleSingle = async () => {
    if (!singleText.trim()) return
    setSingleLoading(true)
    setError('')
    setSingleResult(null)
    try {
      console.log('[SINGLE] Starting single text transliteration')
      const res = await translationAPI.transliterate({ text: singleText.trim() })
      console.log('[SINGLE] Response:', res.data)
      setSingleResult(res.data)
    } catch (e) {
      console.error('[SINGLE_ERROR]', e.response?.data || e.message)
      setError('Error: ' + (e.response?.data?.detail || e.message))
    } finally {
      setSingleLoading(false)
    }
  }

  // ── Paste bulk (multiple lines) ─────────────────────────────────────────────
  const handlePasteBulk = async () => {
    const lines = pasteText.split('\n').map(l => l.trim()).filter(Boolean)
    if (lines.length === 0) return
    setBulkLoading(true)
    setBulkResults([])
    setBulkTotal(lines.length)
    setBulkProgress(0)
    setError('')
    const results = []
    
    console.log('[PASTE_BULK] Starting bulk paste transliteration')
    console.log('[PASTE_BULK] Total lines:', lines.length)
    
    for (let i = 0; i < lines.length; i++) {
      try {
        console.log(`[PASTE_BULK] Processing line ${i + 1}/${lines.length}`)
        const res = await translationAPI.transliterate({ text: lines[i] })
        console.log(`[PASTE_BULK] Line ${i + 1} success:`, res.data)
        results.push({
          original: res.data.original_text || lines[i],
          telugu_script: res.data.telugu_text,
          english_translation: res.data.english_text,
          topic_name: res.data.topic_name,
          topic_keywords: res.data.topic_keywords?.join(', '),
          probability: res.data.probability,
          detected_language: res.data.detected_language,
          confidence: res.data.confidence_score,
        })
      } catch (err) {
        console.error(`[PASTE_BULK] Line ${i + 1} error:`, err.response?.data || err.message)
        results.push({
          original: lines[i],
          telugu_script: lines[i],
          english_translation: lines[i],
          detected_language: 'error',
          confidence: 0,
        })
      }
      setBulkProgress(i + 1)
    }
    console.log('[PASTE_BULK] Completed:', results.length, 'results')
    setBulkResults(results)
    setBulkLoading(false)
  }

  // ── CSV upload ──────────────────────────────────────────────────────────────
  const handleCSVUpload = async (e) => {
    const file = e.target.files[0]
    if (!file) return
    setBulkLoading(true)
    setBulkResults([])
    setError('')
    try {
      console.log('[CSV_UPLOAD] Starting CSV bulk transliteration')
      console.log('[CSV_UPLOAD] File:', { name: file.name, size: file.size })
      const res = await translationAPI.transliterateBulk(file)
      
      console.log('[CSV_UPLOAD] Response type:', typeof res.data)
      console.log('[CSV_UPLOAD] Response length:', res.data?.length)
      
      // Parse CSV response - handle quoted fields (fields may contain commas)
      const text = res.data
      const parseCSVLine = (line) => {
        const result = []
        let current = ''
        let inQuotes = false
        for (let i = 0; i < line.length; i++) {
          if (line[i] === '"') {
            inQuotes = !inQuotes
          } else if (line[i] === ',' && !inQuotes) {
            result.push(current.trim().replace(/^"|"$/g, ''))
            current = ''
          } else {
            current += line[i]
          }
        }
        result.push(current.trim().replace(/^"|"$/g, ''))
        return result
      }
      const allLines = text.trim().split('\n').filter(l => l.trim())
      console.log('[CSV_UPLOAD] CSV lines:', allLines.length)
      
      const headers = parseCSVLine(allLines[0])
      console.log('[CSV_UPLOAD] Headers:', headers)
      
      const rows = allLines.slice(1).map((line, idx) => {
        const vals = parseCSVLine(line)
        const obj = {}
        headers.forEach((h, i) => { obj[h.trim()] = (vals[i] || '').trim() })
        return {
          original: obj.original || '',
          telugu_script: obj.telugu_script || '',
          english_translation: obj.english_translation || '',
          topic_name: obj.topic_name || '',
          topic_keywords: obj.topic_keywords || '',
          probability: parseFloat(obj.probability) || 0,
          detected_language: obj.detected_language || 'unknown',
          confidence: parseFloat(obj.confidence) || 0,
        }
      }).filter(r => r.original)
      
      console.log('[CSV_UPLOAD] Parsed rows:', rows.length)
      console.log('[CSV_UPLOAD] First row:', rows[0])
      
      setBulkResults(rows)
    } catch (e) {
      console.error('[CSV_UPLOAD_ERROR] Full error:', e)
      setError('CSV processing failed: ' + (e.response?.data?.detail || e.message))
    } finally {
      setBulkLoading(false)
      e.target.value = ''
    }
  }

  // ── Download results as CSV ─────────────────────────────────────────────────
  const downloadCSV = () => {
    if (bulkResults.length === 0) return
    const headers = ['original', 'telugu_script', 'english_translation', 'cleaned_text', 'topic_id', 'topic_name', 'topic_keywords', 'probability', 'detected_language', 'confidence']
    const rows = bulkResults.map(r =>
      headers.map(h => `"${(r[h] || '').toString().replace(/"/g, '""')}"`).join(',')
    )
    const csv = [headers.join(','), ...rows].join('\n')
    const blob = new Blob([csv], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'transliteration_results.csv'
    a.click()
    URL.revokeObjectURL(url)
  }

  const tabStyle = (mode) => ({
    padding: '8px 20px', borderRadius: '6px', fontWeight: 600,
    fontSize: '13px', cursor: 'pointer', border: 'none',
    background: activeMode === mode ? '#1D4ED8' : '#EFF6FF',
    color: activeMode === mode ? '#fff' : '#1D4ED8',
    transition: 'all 0.2s',
  })

  return (
    <div style={{ marginTop: '8px' }}>

      {/* Header */}
      <div style={{ background: 'linear-gradient(135deg, #1E3A8A, #1D4ED8)',
        borderRadius: '12px', padding: '20px 24px', marginBottom: '20px', color: '#fff' }}>
        <h2 style={{ margin: 0, fontSize: '20px', fontWeight: 700 }}>🔤 Tanglish Transliterator</h2>
        <p style={{ margin: '6px 0 0', fontSize: '14px', color: '#BFDBFE' }}>
          Convert Tanglish text to Telugu script and English — one at a time or in bulk
        </p>
      </div>

      {/* Mode tabs */}
      <div style={{ display: 'flex', gap: '10px', marginBottom: '20px' }}>
        <button style={tabStyle('single')} onClick={() => setActiveMode('single')}>
          ✏️ One by One
        </button>
        <button style={tabStyle('paste')} onClick={() => setActiveMode('paste')}>
          📋 Paste Multiple
        </button>
        <button style={tabStyle('csv')} onClick={() => setActiveMode('csv')}>
          📁 Upload CSV
        </button>
      </div>

      {error && (
        <div style={{ background: '#FEF2F2', border: '1px solid #FECACA',
          borderRadius: '8px', padding: '10px 14px', marginBottom: '16px',
          color: '#DC2626', fontSize: '13px' }}>
          ⚠️ {error}
        </div>
      )}

      {/* ── SINGLE MODE ── */}
      {activeMode === 'single' && (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
          <div style={{ background: '#fff', borderRadius: '12px', padding: '20px',
            boxShadow: '0 2px 8px rgba(0,0,0,0.06)', border: '1px solid #E2E8F0' }}>
            <h3 style={{ margin: '0 0 14px', color: '#1E3A8A', fontSize: '15px' }}>
              Enter Tanglish Text
            </h3>
            <textarea
              value={singleText}
              onChange={e => setSingleText(e.target.value)}
              onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSingle() }}}
              placeholder="e.g. nenu movie chustunnanu&#10;ee tech ela undhi&#10;amma cheppindi bagundi"
              rows={5}
              style={{ width: '100%', padding: '10px 12px', borderRadius: '8px',
                border: '1.5px solid #BFDBFE', fontSize: '14px', resize: 'vertical',
                fontFamily: 'inherit', boxSizing: 'border-box', outline: 'none' }}
            />
            <button onClick={handleSingle} disabled={singleLoading || !singleText.trim()}
              style={{ marginTop: '12px', width: '100%', padding: '10px',
                background: singleLoading ? '#93C5FD' : '#1D4ED8',
                color: '#fff', border: 'none', borderRadius: '8px',
                fontWeight: 600, fontSize: '14px',
                cursor: singleLoading ? 'not-allowed' : 'pointer' }}>
              {singleLoading ? '⏳ Processing...' : '▶ Transliterate'}
            </button>
          </div>

          <div>
            {singleResult ? (
              singleResult.results ? (
                // Multi-line response from single input
                <div style={{ maxHeight: '600px', overflowY: 'auto', padding: '4px', borderRadius: '8px', background: '#F1F5F9' }}>
                  {singleResult.results.map((r, i) => (
                    <ResultCard 
                      key={i} 
                      index={i}
                      result={{
                        original: r.original_text || r.original,
                        telugu_script: r.telugu_text || r.telugu_script,
                        english_translation: r.english_text || r.english_translation,
                        topic_name: r.topic_name,
                        topic_keywords: Array.isArray(r.topic_keywords) ? r.topic_keywords.join(', ') : r.topic_keywords,
                        probability: r.probability,
                        detected_language: r.detected_language,
                        confidence: r.confidence_score || r.confidence
                      }} 
                    />
                  ))}
                </div>
              ) : (
                // True single result
                <div style={{ background: '#F8FAFC', borderRadius: '10px', padding: '16px', border: '1px solid #E2E8F0' }}>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '15px' }}>
                    <div>
                      <span style={{ fontSize: '11px', color: '#6B7280', fontWeight: 600 }}>🔤 TELUGU SCRIPT</span>
                      <p style={{ margin: '4px 0 0', fontSize: '16px', color: '#1E3A8A', fontFamily: 'serif' }}>
                        {singleResult.telugu_text || singleResult.telugu}
                      </p>
                    </div>
                    <div>
                      <span style={{ fontSize: '11px', color: '#166534', fontWeight: 600 }}>🌐 ENGLISH</span>
                      <p style={{ margin: '4px 0 0', fontSize: '14px', color: '#14532D' }}>
                        {singleResult.english_text || singleResult.english}
                      </p>
                    </div>
                  </div>
                  
                  {singleResult.topic_name && (
                    <div style={{ marginTop: '15px', padding: '12px', background: '#FFF7ED', borderRadius: '8px', border: '1px solid #FFEDD5' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <span style={{ fontSize: '12px', color: '#9A3412', fontWeight: 600 }}>📌 DETECTED TOPIC: {singleResult.topic_name}</span>
                        <span style={{ fontSize: '11px', color: '#C2410C' }}>{Math.round((singleResult.probability || 0) * 100)}% match</span>
                      </div>
                      {singleResult.topic_keywords && (
                        <p style={{ margin: '4px 0 0', fontSize: '12px', color: '#7C2D12' }}>
                          Keywords: {Array.isArray(singleResult.topic_keywords) ? singleResult.topic_keywords.join(', ') : singleResult.topic_keywords}
                        </p>
                      )}
                    </div>
                  )}
                </div>
              )
            ) : (
              <div style={{ background: '#F8FAFC', borderRadius: '12px',
                border: '2px dashed #BFDBFE', padding: '60px 20px', textAlign: 'center',
                color: '#9CA3AF' }}>
                <div style={{ fontSize: '40px', marginBottom: '10px' }}>🔤</div>
                <p style={{ fontSize: '14px' }}>Result will appear here</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* ── PASTE MODE ── */}
      {activeMode === 'paste' && (
        <div style={{ background: '#fff', borderRadius: '12px', padding: '20px',
          boxShadow: '0 2px 8px rgba(0,0,0,0.06)', border: '1px solid #E2E8F0' }}>
          <h3 style={{ margin: '0 0 6px', color: '#1E3A8A', fontSize: '15px' }}>
            Paste Multiple Statements
          </h3>
          <p style={{ margin: '0 0 14px', fontSize: '13px', color: '#6B7280' }}>
            One statement per line — up to 100 lines
          </p>
          <textarea
            value={pasteText}
            onChange={e => setPasteText(e.target.value)}
            placeholder={`nenu movie chustunnanu\nee tech ela undhi\namma cheppindi bagundi\nbiryani chala tasty ga undi\nee match super hit`}
            rows={8}
            style={{ width: '100%', padding: '10px 12px', borderRadius: '8px',
              border: '1.5px solid #BFDBFE', fontSize: '14px', resize: 'vertical',
              fontFamily: 'inherit', boxSizing: 'border-box', outline: 'none' }}
          />
          <div style={{ display: 'flex', gap: '10px', marginTop: '12px', alignItems: 'center' }}>
            <button onClick={handlePasteBulk}
              disabled={bulkLoading || !pasteText.trim()}
              style={{ padding: '10px 24px', background: bulkLoading ? '#93C5FD' : '#1D4ED8',
                color: '#fff', border: 'none', borderRadius: '8px',
                fontWeight: 600, fontSize: '14px',
                cursor: bulkLoading ? 'not-allowed' : 'pointer' }}>
              {bulkLoading ? `⏳ Processing ${bulkProgress}/${bulkTotal}...` : '▶ Transliterate All'}
            </button>
            {bulkResults.length > 0 && (
              <button onClick={downloadCSV}
                style={{ padding: '10px 20px', background: '#059669',
                  color: '#fff', border: 'none', borderRadius: '8px',
                  fontWeight: 600, fontSize: '14px', cursor: 'pointer' }}>
                ⬇ Download CSV ({bulkResults.length} rows)
              </button>
            )}
          </div>

          {bulkLoading && (
            <div style={{ marginTop: '16px' }}>
              <div style={{ background: '#E2E8F0', borderRadius: '4px', height: '8px' }}>
                <div style={{ width: `${(bulkProgress / bulkTotal) * 100}%`,
                  background: '#1D4ED8', height: '8px', borderRadius: '4px',
                  transition: 'width 0.3s' }} />
              </div>
              <p style={{ fontSize: '12px', color: '#6B7280', marginTop: '4px' }}>
                {bulkProgress} of {bulkTotal} processed
              </p>
            </div>
          )}

          {bulkResults.length > 0 && (
            <div style={{ marginTop: '20px' }}>
              <p style={{ fontSize: '13px', fontWeight: 600, color: '#1E3A8A', marginBottom: '12px' }}>
                ✅ {bulkResults.length} statements processed
              </p>
              {bulkResults.map((r, i) => <ResultCard key={i} result={r} index={i} />)}
            </div>
          )}
        </div>
      )}

      {/* ── CSV MODE ── */}
      {activeMode === 'csv' && (
        <div style={{ background: '#fff', borderRadius: '12px', padding: '20px',
          boxShadow: '0 2px 8px rgba(0,0,0,0.06)', border: '1px solid #E2E8F0' }}>
          <h3 style={{ margin: '0 0 6px', color: '#1E3A8A', fontSize: '15px' }}>
            Upload CSV File
          </h3>
          <p style={{ margin: '0 0 14px', fontSize: '13px', color: '#6B7280' }}>
            CSV must have a column named <strong>text</strong>, <strong>statement</strong>, or <strong>sentence</strong>
          </p>

          {/* CSV format example */}
          <div style={{ background: '#F0FDF4', borderRadius: '8px', padding: '12px 16px',
            marginBottom: '16px', border: '1px solid #BBF7D0' }}>
            <p style={{ margin: '0 0 6px', fontSize: '12px', fontWeight: 600, color: '#166534' }}>
              📋 Example CSV format:
            </p>
            <code style={{ fontSize: '12px', color: '#14532D' }}>
              text<br />
              nenu movie chustunnanu<br />
              ee tech ela undhi<br />
              amma cheppindi bagundi
            </code>
          </div>

          <div
            onClick={() => fileRef.current?.click()}
            style={{ border: '2px dashed #BFDBFE', borderRadius: '10px',
              padding: '40px', textAlign: 'center', cursor: 'pointer',
              background: '#F8FAFC', transition: 'all 0.2s' }}
            onMouseEnter={e => e.target.style.background = '#EFF6FF'}
            onMouseLeave={e => e.target.style.background = '#F8FAFC'}
          >
            <div style={{ fontSize: '36px', marginBottom: '8px' }}>📁</div>
            <p style={{ margin: 0, color: '#1D4ED8', fontWeight: 600, fontSize: '14px' }}>
              Click to upload CSV
            </p>
            <p style={{ margin: '4px 0 0', color: '#9CA3AF', fontSize: '12px' }}>
              Supports up to 100 rows
            </p>
            <input ref={fileRef} type="file" accept=".csv"
              onChange={handleCSVUpload} style={{ display: 'none' }} />
          </div>

          {bulkLoading && (
            <div style={{ marginTop: '16px', textAlign: 'center', color: '#1D4ED8' }}>
              <p style={{ fontSize: '14px' }}>⏳ Processing your CSV...</p>
            </div>
          )}

          {bulkResults.length > 0 && (
            <div style={{ marginTop: '20px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between',
                alignItems: 'center', marginBottom: '12px' }}>
                <p style={{ margin: 0, fontSize: '13px', fontWeight: 600, color: '#1E3A8A' }}>
                  ✅ {bulkResults.length} rows processed
                </p>
                <button onClick={downloadCSV}
                  style={{ padding: '8px 18px', background: '#059669',
                    color: '#fff', border: 'none', borderRadius: '8px',
                    fontWeight: 600, fontSize: '13px', cursor: 'pointer' }}>
                  ⬇ Download Results CSV
                </button>
              </div>
              
              <div style={{ 
                maxHeight: '600px', 
                overflowY: 'auto', 
                padding: '4px',
                borderRadius: '8px',
                background: '#F1F5F9'
              }}>
                {bulkResults.map((r, i) => <ResultCard key={i} result={r} index={i} />)}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default BulkTransliterator
