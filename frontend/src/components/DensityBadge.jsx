const COLORS = { LOW: '#2FB344', MEDIUM: '#F5A524', HIGH: '#E5484D', EMERGENCY: '#8B5CF6' }

export default function DensityBadge({ density }) {
  const color = COLORS[density] || '#888'
  return (
    <span className="density-badge" style={{ background: color }}>
      {density}
    </span>
  )
}
