const COLORS = { car: '#4F8EF7', bike: '#F5A524', bus: '#2FB344', truck: '#E5484D' }
const KEYS = ['car', 'bike', 'bus', 'truck']

export default function VehicleChart({ history }) {
  if (!history.length) return <div className="chart-empty">No data yet</div>

  const width = 480
  const height = 220
  const padding = 24
  const barGap = 3
  const n = history.length
  const barWidth = Math.max(2, (width - padding * 2) / n - barGap)
  const maxTotal = Math.max(1, ...history.map((h) => h.total_vehicles))
  const usableHeight = height - padding * 2

  return (
    <svg viewBox={`0 0 ${width} ${height}`} className="chart-svg">
      {history.map((h, i) => {
        const x = padding + i * (barWidth + barGap)
        let yCursor = height - padding
        return (
          <g key={i}>
            {KEYS.map((key) => {
              const value = h.counts?.[key] || 0
              const barHeight = (value / maxTotal) * usableHeight
              const y = yCursor - barHeight
              yCursor = y
              if (barHeight <= 0) return null
              return <rect key={key} x={x} y={y} width={barWidth} height={barHeight} fill={COLORS[key]} />
            })}
          </g>
        )
      })}
      <line x1={padding} y1={height - padding} x2={width - padding} y2={height - padding} stroke="#444" />
      <g className="chart-legend">
        {KEYS.map((key, i) => (
          <g key={key} transform={`translate(${padding + i * 100}, 8)`}>
            <rect width="10" height="10" fill={COLORS[key]} />
            <text x="14" y="9" fontSize="10" fill="#ccc">{key}</text>
          </g>
        ))}
      </g>
    </svg>
  )
}
