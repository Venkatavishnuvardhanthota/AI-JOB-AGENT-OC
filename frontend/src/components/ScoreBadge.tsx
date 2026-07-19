interface ScoreBadgeProps {
  score: number
  size?: 'sm' | 'md' | 'lg'
  label?: string
}

export function ScoreBadge({ score, size = 'md', label }: ScoreBadgeProps) {
  const pct = Math.round(score * 100)
  const color =
    pct >= 80 ? '#22c55e' :
    pct >= 60 ? '#84cc16' :
    pct >= 40 ? '#eab308' :
    pct >= 20 ? '#f97316' :
    '#ef4444'

  const dims = size === 'sm' ? 32 : size === 'lg' ? 56 : 40
  const stroke = size === 'sm' ? 3 : size === 'lg' ? 5 : 4
  const radius = (dims - stroke) / 2
  const circumference = 2 * Math.PI * radius
  const offset = circumference - (pct / 100) * circumference

  return (
    <div style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }} title={`${pct}% match`}>
      <svg width={dims} height={dims} style={{ transform: 'rotate(-90deg)' }}>
        <circle cx={dims / 2} cy={dims / 2} r={radius} fill="none" stroke="#e5e7eb" strokeWidth={stroke} />
        <circle
          cx={dims / 2}
          cy={dims / 2}
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth={stroke}
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
        />
      </svg>
      <span style={{ fontSize: size === 'sm' ? 11 : size === 'lg' ? 18 : 14, fontWeight: 600, color }}>
        {pct}%
      </span>
      {label && <span style={{ fontSize: 12, color: '#6b7280' }}>{label}</span>}
    </div>
  )
}
