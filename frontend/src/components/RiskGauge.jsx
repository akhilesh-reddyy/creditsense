import { useEffect, useRef } from 'react'

const BAND_COLORS = {
  LOW:      '#22C55E',
  MODERATE: '#F59E0B',
  HIGH:     '#EF4444',
  CRITICAL: '#7C3AED',
}

const RADIUS = 70
const STROKE  = 10
const CIRC    = 2 * Math.PI * RADIUS
// We only use the top 75% of the circle (270°)
const ARC_LEN = CIRC * 0.75
const ROTATION = 135 // start bottom-left

export default function RiskGauge({ probability = 0, band = 'LOW', score = 0 }) {
  const arcRef = useRef(null)
  const color  = BAND_COLORS[band] || '#22C55E'

  useEffect(() => {
    const el = arcRef.current
    if (!el) return
    const target = ARC_LEN * (1 - probability)
    // Animate from full offset (hidden) to target
    el.style.transition = 'none'
    el.style.strokeDashoffset = ARC_LEN
    requestAnimationFrame(() => {
      requestAnimationFrame(() => {
        el.style.transition = 'stroke-dashoffset 1.2s cubic-bezier(0.16, 1, 0.3, 1)'
        el.style.strokeDashoffset = target
      })
    })
  }, [probability])

  const cx = 90, cy = 90

  return (
    <div className="flex flex-col items-center gap-2">
      <svg width="180" height="140" viewBox="0 0 180 140">
        {/* Track */}
        <circle
          cx={cx} cy={cy} r={RADIUS}
          fill="none"
          stroke="#1A1A26"
          strokeWidth={STROKE}
          strokeDasharray={`${ARC_LEN} ${CIRC}`}
          strokeDashoffset={0}
          strokeLinecap="round"
          transform={`rotate(${ROTATION} ${cx} ${cy})`}
        />
        {/* Fill arc */}
        <circle
          ref={arcRef}
          cx={cx} cy={cy} r={RADIUS}
          fill="none"
          stroke={color}
          strokeWidth={STROKE}
          strokeDasharray={`${ARC_LEN} ${CIRC}`}
          strokeDashoffset={ARC_LEN}
          strokeLinecap="round"
          transform={`rotate(${ROTATION} ${cx} ${cy})`}
          style={{ filter: `drop-shadow(0 0 8px ${color}66)` }}
        />
        {/* Score label */}
        <text
          x={cx} y={cy - 6}
          textAnchor="middle"
          fill={color}
          fontSize="28"
          fontWeight="600"
          fontFamily="JetBrains Mono, monospace"
        >
          {score}
        </text>
        <text
          x={cx} y={cy + 16}
          textAnchor="middle"
          fill="#8888A4"
          fontSize="11"
          fontFamily="DM Sans, sans-serif"
          fontWeight="400"
        >
          RISK SCORE / 1000
        </text>
        {/* Band label */}
        <text
          x={cx} y={cy + 34}
          textAnchor="middle"
          fill={color}
          fontSize="13"
          fontFamily="DM Sans, sans-serif"
          fontWeight="600"
          letterSpacing="2"
        >
          {band}
        </text>
        {/* Min/Max labels */}
        <text x="14" y="130" fill="#44445A" fontSize="10" fontFamily="DM Sans">0</text>
        <text x="155" y="130" fill="#44445A" fontSize="10" fontFamily="DM Sans">1K</text>
      </svg>
      <p className="text-xs text-ink-400 text-center max-w-[200px] leading-relaxed">
        {getProbabilityLabel(probability)}
      </p>
    </div>
  )
}

function getProbabilityLabel(p) {
  if (p < 0.15) return `${(p * 100).toFixed(1)}% default probability — strong candidate`
  if (p < 0.35) return `${(p * 100).toFixed(1)}% default probability — review recommended`
  if (p < 0.60) return `${(p * 100).toFixed(1)}% default probability — manual underwriting`
  return `${(p * 100).toFixed(1)}% default probability — decline or escalate`
}
