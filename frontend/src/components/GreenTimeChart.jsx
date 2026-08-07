export default function GreenTimeChart({ history }) {
  if (!history.length) return <div className="chart-empty">No data yet</div>

  const width = 480
  const height = 220
  const padding = 24
  const n = history.length
  const maxGreen = Math.max(1, ...history.map((h) => h.green_time_s))
  const usableWidth = width - padding * 2
  const usableHeight = height - padding * 2

  const pointFor = (h, i) => {
    const x = padding + (n === 1 ? usableWidth / 2 : (i / (n - 1)) * usableWidth)
    const y = height - padding - (h.green_time_s / maxGreen) * usableHeight
    return [x, y]
  }

  const points = history.map(pointFor)
  const polylinePoints = points.map(([x, y]) => `${x},${y}`).join(' ')

  return (
    <svg viewBox={`0 0 ${width} ${height}`} className="chart-svg">
      <line x1={padding} y1={height - padding} x2={width - padding} y2={height - padding} stroke="#444" />
      <polyline points={polylinePoints} fill="none" stroke="#2FB344" strokeWidth="2" />
      {points.map(([x, y], i) => (
        <circle key={i} cx={x} cy={y} r="3" fill="#2FB344" />
      ))}
    </svg>
  )
}
