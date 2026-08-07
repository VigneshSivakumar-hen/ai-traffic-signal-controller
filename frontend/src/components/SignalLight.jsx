const COLORS = { RED: '#E5484D', YELLOW: '#F5A524', GREEN: '#2FB344' }

export default function SignalLight({ active }) {
  return (
    <div className="signal-housing">
      {['RED', 'YELLOW', 'GREEN'].map((light) => (
        <div
          key={light}
          className="signal-bulb"
          style={{
            background: light === active ? COLORS[light] : '#2A2A2A',
            boxShadow: light === active ? `0 0 16px ${COLORS[light]}` : 'none',
          }}
        />
      ))}
    </div>
  )
}
