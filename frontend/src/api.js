// All requests are relative — in production the built React app is served
// by FastAPI on the same origin, so no CORS/base-URL config is needed. In
// dev (`npm run dev`), vite.config.js proxies these same paths to :8000.

export async function getHealth() {
  try {
    const r = await fetch('/health')
    return r.ok
  } catch {
    return false
  }
}

export async function getStatus() {
  const r = await fetch('/status')
  if (!r.ok) throw new Error(`status ${r.status}`)
  return r.json()
}

export async function getMetrics() {
  const r = await fetch('/metrics')
  if (!r.ok) throw new Error(`metrics ${r.status}`)
  return r.json()
}

export async function getFrameBlob() {
  const r = await fetch('/frame')
  if (!r.ok) return null
  return r.blob()
}

export async function startPipeline(source, laneId) {
  const r = await fetch('/pipeline/start', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ source, lane_id: laneId }),
  })
  if (!r.ok) {
    const err = await r.json().catch(() => ({}))
    throw new Error(err.detail || `start failed (${r.status})`)
  }
  return r.json()
}

export async function stopPipeline() {
  const r = await fetch('/pipeline/stop', { method: 'POST' })
  if (!r.ok) {
    const err = await r.json().catch(() => ({}))
    throw new Error(err.detail || `stop failed (${r.status})`)
  }
  return r.json()
}
