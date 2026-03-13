import { ArrowUp, ArrowDown, Zap } from 'lucide-react'

export default function CounterfactualCards({ counterfactuals = [] }) {
  if (!counterfactuals.length) return (
    <div className="text-center py-8 text-ink-400 text-sm">
      No actionable improvements found — profile is already optimal.
    </div>
  )

  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2 mb-3">
        <Zap size={14} className="text-acid-400" />
        <h3 className="text-sm font-medium text-ink-200 tracking-wide uppercase">
          How to Improve This Score
        </h3>
      </div>

      {counterfactuals.map((cf, i) => {
        const isUp = cf.suggested_value > cf.current_value
        const reductionPct = (cf.risk_reduction * 100).toFixed(1)

        return (
          <div
            key={cf.feature}
            className="rounded-lg p-4 border border-ink-600 bg-ink-800 hover:border-acid-400/30 transition-all duration-200"
            style={{ animationDelay: `${i * 100}ms` }}
          >
            <div className="flex items-start justify-between gap-3">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <span
                    className="w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0"
                    style={{ background: 'rgba(184,255,60,0.1)', border: '1px solid rgba(184,255,60,0.3)' }}
                  >
                    {isUp
                      ? <ArrowUp size={12} className="text-acid-400" />
                      : <ArrowDown size={12} className="text-acid-400" />
                    }
                  </span>
                  <span className="text-sm font-medium text-ink-100">
                    {cf.display_name}
                  </span>
                </div>
                <p className="text-xs text-ink-400 ml-8">
                  Change from{' '}
                  <span className="text-ink-200 font-mono">{formatVal(cf.feature, cf.current_value)}</span>
                  {' → '}
                  <span className="font-mono" style={{ color: '#B8FF3C' }}>{cf.formatted_change}</span>
                </p>
              </div>

              {/* Impact badge */}
              <div className="flex-shrink-0 text-right">
                <div
                  className="text-sm font-semibold font-mono px-2 py-1 rounded"
                  style={{ color: '#B8FF3C', background: 'rgba(184,255,60,0.1)', border: '1px solid rgba(184,255,60,0.2)' }}
                >
                  -{reductionPct}%
                </div>
                <div className="text-xs text-ink-400 mt-0.5">risk drop</div>
              </div>
            </div>
          </div>
        )
      })}

      <p className="text-xs text-ink-400 pt-2 border-t border-ink-800">
        Risk reductions are independent estimates — combined effect may differ.
      </p>
    </div>
  )
}

function formatVal(feature, value) {
  const pct = ['emi_to_income_ratio', 'debt_to_income_ratio', 'payment_timing_score', 'partial_payment_ratio']
  if (pct.includes(feature)) return `${(value * 100).toFixed(0)}%`
  if (feature === 'cibil_score') return value.toFixed(0)
  if (Number.isInteger(value)) return value.toString()
  return value.toFixed(2)
}
