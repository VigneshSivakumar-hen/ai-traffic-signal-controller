import { useEffect, useRef, useState } from 'react'
import SignalLight from './components/SignalLight.jsx'
import DensityBadge from './components/DensityBadge.jsx'
import VehicleChart from './components/VehicleChart.jsx'
import GreenTimeChart from './components/GreenTimeChart.jsx'
import { getHealth, getStatus, getMetrics, getFrameBlob, startPipeline, stopPipeline } from './api.js'

const REFRESH_OPTIONS = [0.5, 1, 2, 3, 5]

export default function App() {
  const [health, setHealth] = useState(false)
  const [status, setStatus] = useState(null)
  const [history, setHistory] = useState([])
  const [frameUrl, setFrameUrl] = useState(null)
  const [source, setSource] = useState('0')
  const [laneId, setLaneId] = useState('north')
  const [refreshRate, setRefreshRate] = useState(1)
  const [actionError, setActionError] = useState('')
  const frameUrlRef = useRef(null)

  // Backend health check, independent of the main poll loop so it still
  // shows "unreachable" even before/after a pipeline is running.
  useEffect(() => {
    let cancelled = false
    const check = async () => {
      const ok = await getHealth()
      if (!cancelled) setHealth(ok)
    }
    check()
    const id = setInterval(check, 5000)
    return () => {
      cancelled = true
      clearInterval(id)
    }
  }, [])

  // Main poll loop: status always, frame+metrics only while running.
  useEffect(() => {
    let cancelled = false
    let timeoutId

    const poll = async () => {
      try {
        const data = await getStatus()
        if (cancelled) return
        setStatus(data)

        if (data.running) {
          const [blob, metrics] = await Promise.all([getFrameBlob(), getMetrics()])
          if (cancelled) return

          if (blob) {
            const url = URL.createObjectURL(blob)
            if (frameUrlRef.current) URL.revokeObjectURL(frameUrlRef.current)
            frameUrlRef.current = url
            setFrameUrl(url)
          }
          setHistory(metrics.history || [])
        }
      } catch {
        if (!cancelled) setStatus(null)
      } finally {
        if (!cancelled) timeoutId = setTimeout(poll, refreshRate * 1000)
      }
    }

    poll()
    return () => {
      cancelled = true
      clearTimeout(timeoutId)
    }
  }, [refreshRate])

  const handleStart = async () => {
    setActionError('')
    try {
      await startPipeline(source, laneId)
    } catch (e) {
      setActionError(e.message)
    }
  }

  const handleStop = async () => {
    setActionError('')
    try {
      await stopPipeline()
    } catch (e) {
      setActionError(e.message)
    }
  }

  const running = Boolean(status?.running)
  const counts = status?.counts || {}

  return (
    <div className="app">
      <aside className="sidebar">
        <h2>🚦 Pipeline control</h2>

        <label htmlFor="source">Video source</label>
        <input
          id="source"
          value={source}
          onChange={(e) => setSource(e.target.value)}
          placeholder="0, path, or rtsp://"
        />

        <label htmlFor="lane">Lane ID</label>
        <input id="lane" value={laneId} onChange={(e) => setLaneId(e.target.value)} />

        <div className="button-row">
          <button className="primary" onClick={handleStart} disabled={running}>▶ Start Pipeline</button>
          <button onClick={handleStop} disabled={!running}>⏹ Stop</button>
        </div>

        <label htmlFor="refresh">Refresh every</label>
        <select id="refresh" value={refreshRate} onChange={(e) => setRefreshRate(Number(e.target.value))}>
          {REFRESH_OPTIONS.map((v) => (
            <option key={v} value={v}>{v}s</option>
          ))}
        </select>

        {actionError && <p className="error-text">{actionError}</p>}

        <hr />
        <p>{health ? '🟢 Backend online' : '🔴 Backend unreachable'}</p>
        {!health && <p className="hint">Start it with:<br /><code>python -m uvicorn backend.api:app --reload</code></p>}
      </aside>

      <main className="main">
        <h1>AI-Based Traffic Signal Controller</h1>
        <p className="subtitle">Live dashboard — React frontend, FastAPI backend</p>

        {!running ? (
          <div className="empty-state">
            Pipeline is not running. Set a video source in the sidebar and click <strong>Start Pipeline</strong>.
          </div>
        ) : (
          <>
            <div className="top-row">
              <div className="card">
                <h3>Signal</h3>
                <SignalLight active={status.signal_phase} />
              </div>
              <div className="card frame-card">
                <h3>Live view</h3>
                {frameUrl ? <img src={frameUrl} alt="live feed" /> : <p>Waiting for frames...</p>}
              </div>
              <div className="card">
                <h3>Density</h3>
                <DensityBadge density={status.density} />
              </div>
              <div className="card">
                <h3>Green time</h3>
                <p className="metric-value">{status.green_time_s}s</p>
              </div>
              <div className="card">
                <h3>Phase remaining</h3>
                <p className="metric-value">{status.signal_remaining}s</p>
              </div>
            </div>

            {status.emergency && (
              <div className="alert-banner">
                🚨 EMERGENCY vehicle flagged — signal jumping to immediate green
              </div>
            )}

            <div className="metrics-row">
              <div className="card"><h4>Total vehicles</h4><p className="metric-value">{status.total_vehicles}</p></div>
              <div className="card"><h4>Cars</h4><p className="metric-value">{counts.car || 0}</p></div>
              <div className="card"><h4>Bikes</h4><p className="metric-value">{counts.bike || 0}</p></div>
              <div className="card"><h4>Buses/Trucks</h4><p className="metric-value">{(counts.bus || 0) + (counts.truck || 0)}</p></div>
            </div>

            <div className="chart-row">
              <div className="card">
                <h3>Vehicle counts over time</h3>
                <VehicleChart history={history} />
              </div>
              <div className="card">
                <h3>Green time decisions</h3>
                <GreenTimeChart history={history} />
              </div>
            </div>

            <div className="card">
              <h3>Recent history</h3>
              <table className="history-table">
                <thead>
                  <tr><th>Time</th><th>Total</th><th>Density</th><th>Emergency</th><th>Green (s)</th></tr>
                </thead>
                <tbody>
                  {[...history].slice(-15).reverse().map((h, i) => (
                    <tr key={i}>
                      <td>{new Date(h.t * 1000).toLocaleTimeString()}</td>
                      <td>{h.total_vehicles}</td>
                      <td>{h.density}</td>
                      <td>{h.emergency ? 'Yes' : 'No'}</td>
                      <td>{h.green_time_s}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        )}
      </main>
    </div>
  )
}
