import { useEffect, useRef } from 'react'

const COLORS = {
  increases_risk: { bar: '#EF4444', bg: 'rgba(239,68,68,0.08)', border: 'rgba(239,68,68,0.2)' },
  decreases_risk: { bar: '#22C55E', bg: 'rgba(34,197,94,0.08)', border: 'rgba(34,197,94,0.2)' },
}

const MAGNITUDE_LABELS = {
  high:   'Strong driver',
  medium: 'Moderate driver',
  low:    'Weak driver',
}

export default function ShapWaterfall({ factors = [] }) {
  if (!factors.length) return null

  const maxAbs = Math.max(...factors.map(f => Math.abs(f.shap_value)), 0.001)

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-medium text-ink-200 tracking-wide uppercase">
          Risk Drivers
        </h3>
        <div className="flex gap-3 text-xs text-ink-400">
          <span className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-sm bg-red-500 inline-block" />
            Increases risk
          </span>
          <span className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-sm bg-green-500 inline-block" />
            Decreases risk
          </span>
        </div>
      </div>

      {factors.map((factor, i) => {
        const pct      = (Math.abs(factor.shap_value) / maxAbs) * 100
        const colors   = COLORS[factor.direction]
        const isRisk   = factor.direction === 'increases_risk'
        const formattedVal = formatValue(factor.feature, factor.value)

        return (
          <div
            key={factor.feature}
            className="rounded-lg p-3 transition-all duration-200 hover:scale-[1.01]"
            style={{ background: colors.bg, border: `1px solid ${colors.border}`, animationDelay: `${i * 80}ms` }}
          >
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-ink-100">
                {factor.display_name}
              </span>
              <div className="flex items-center gap-2">
                <span className="text-xs text-ink-400 font-mono">
                  {formattedVal}
                </span>
                <span
                  className="text-xs px-2 py-0.5 rounded-full font-medium"
                  style={{ color: colors.bar, background: colors.bg, border: `1px solid ${colors.border}` }}
                >
                  {MAGNITUDE_LABELS[factor.magnitude]}
                </span>
              </div>
            </div>

            {/* Bar */}
            <div className="h-1.5 w-full bg-ink-800 rounded-full overflow-hidden">
              <div
                className="h-full rounded-full transition-all duration-700 ease-out"
                style={{
                  width: `${pct}%`,
                  background: colors.bar,
                  boxShadow: `0 0 6px ${colors.bar}66`,
                  transitionDelay: `${i * 80 + 300}ms`,
                }}
              />
            </div>

            <p className="text-xs text-ink-400 mt-1.5">
              {getFactorNarrative(factor)}
            </p>
          </div>
        )
      })}
    </div>
  )
}

function formatValue(feature, value) {
  const pctFeatures = ['emi_to_income_ratio', 'debt_to_income_ratio', 'payment_timing_score', 'partial_payment_ratio']
  const currFeatures = ['monthly_income', 'loan_amount']

  if (pctFeatures.includes(feature)) return `${(value * 100).toFixed(0)}%`
  if (currFeatures.includes(feature)) return `₹${Number(value).toLocaleString('en-IN')}`
  if (feature === 'months_since_delinquency' && value >= 99) return 'Never'
  if (feature === 'employment_type') return ['Salaried', 'Self-Employed', 'Business Owner'][value] ?? value
  if (Number.isInteger(value)) return value.toString()
  return value.toFixed(2)
}

function getFactorNarrative(factor) {
  const dir = factor.direction === 'increases_risk' ? 'pushing risk up' : 'pulling risk down'
  const strength = factor.shap_value > 0
    ? `+${(factor.shap_value * 100).toFixed(1)}%`
    : `${(factor.shap_value * 100).toFixed(1)}%`
  return `SHAP contribution: ${strength} default probability (${dir})`
}
