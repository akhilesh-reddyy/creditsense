import { useState } from 'react'
import { RotateCcw, AlertCircle, Clock, ChevronRight } from 'lucide-react'
import ApplicantForm from '../components/ApplicantForm'
import RiskGauge from '../components/RiskGauge'
import ShapWaterfall from '../components/ShapWaterfall'
import CounterfactualCards from '../components/CounterfactualCards'
import { useScore } from '../hooks/useScore'
import clsx from 'clsx'

const BAND_BORDER = {
  LOW:      'border-green-500/30',
  MODERATE: 'border-amber-500/30',
  HIGH:     'border-red-500/30',
  CRITICAL: 'border-purple-500/30',
}

const TABS = ['Risk Drivers', 'Improvements']

export default function ScorerPage() {
  const { form, setField, result, loading, error, submit, reset } = useScore()
  const [tab, setTab] = useState(0)

  return (
    <div className="min-h-screen grid-bg">
      {/* Header */}
      <header className="border-b border-ink-800 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div
            className="w-8 h-8 rounded-lg flex items-center justify-center text-ink-900 font-bold text-sm"
            style={{ background: '#B8FF3C' }}
          >
            CS
          </div>
          <div>
            <h1 className="text-sm font-semibold text-ink-100 font-body">CreditSense</h1>
            <p className="text-xs text-ink-400">Explainable Credit Risk Engine</p>
          </div>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse-dot" />
          <span className="text-xs text-ink-400">Model v1.0</span>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-4 py-8 grid grid-cols-1 lg:grid-cols-[380px_1fr] gap-6">
        {/* Left: Form */}
        <div className="rounded-2xl border border-ink-800 bg-ink-900/60 p-5 backdrop-blur-sm h-fit">
          <div className="flex items-center justify-between mb-5">
            <h2 className="text-base font-semibold text-ink-100">Applicant Profile</h2>
            {result && (
              <button
                onClick={reset}
                className="flex items-center gap-1.5 text-xs text-ink-400 hover:text-acid-400 transition-colors"
              >
                <RotateCcw size={12} />
                Reset
              </button>
            )}
          </div>
          <ApplicantForm form={form} setField={setField} onSubmit={submit} loading={loading} />
        </div>

        {/* Right: Results */}
        <div className="space-y-4">
          {error && (
            <div className="rounded-xl border border-red-500/30 bg-red-500/10 p-4 flex items-start gap-3">
              <AlertCircle size={16} className="text-red-400 flex-shrink-0 mt-0.5" />
              <div>
                <p className="text-sm font-medium text-red-300">Scoring Failed</p>
                <p className="text-xs text-red-400/80 mt-0.5">{error}</p>
              </div>
            </div>
          )}

          {!result && !error && (
            <div className="rounded-2xl border border-ink-800 bg-ink-900/40 h-96 flex flex-col items-center justify-center gap-3 text-center">
              <div className="w-12 h-12 rounded-full border border-ink-700 flex items-center justify-center">
                <ChevronRight size={20} className="text-ink-600" />
              </div>
              <p className="text-sm text-ink-500">Fill the form and click <span className="text-acid-400">Assess Risk</span></p>
              <p className="text-xs text-ink-600 max-w-xs">
                Get a default probability, SHAP-powered risk drivers, and counterfactual recommendations.
              </p>
            </div>
          )}

          {result && (
            <div className="animate-slide-up space-y-4">
              {/* Score card */}
              <div
                className={clsx(
                  'rounded-2xl border p-6 bg-ink-900/60 backdrop-blur-sm',
                  BAND_BORDER[result.band]
                )}
              >
                <div className="flex flex-col sm:flex-row items-center gap-6">
                  <RiskGauge
                    probability={result.probability}
                    band={result.band}
                    score={result.score}
                  />
                  <div className="flex-1 space-y-3">
                    <div>
                      <p className="text-xs text-ink-400 uppercase tracking-wider mb-1">Assessment</p>
                      <p className="text-base text-ink-100">{result.band_description}</p>
                    </div>
                    <div className="grid grid-cols-2 gap-3">
                      <Stat label="Default Prob." value={`${(result.probability * 100).toFixed(1)}%`} />
                      <Stat label="Risk Score" value={result.score} mono />
                      <Stat label="Risk Band" value={result.band} colored={result.band} />
                      <Stat
                        label="Latency"
                        value={`${result.latency_ms}ms`}
                        icon={<Clock size={10} className="text-ink-400" />}
                        mono
                      />
                    </div>
                  </div>
                </div>
              </div>

              {/* Tabs */}
              <div className="rounded-2xl border border-ink-800 bg-ink-900/60 backdrop-blur-sm overflow-hidden">
                <div className="flex border-b border-ink-800">
                  {TABS.map((t, i) => (
                    <button
                      key={t}
                      onClick={() => setTab(i)}
                      className={clsx(
                        'flex-1 py-3 text-sm font-medium transition-colors',
                        tab === i
                          ? 'text-acid-400 border-b-2 border-acid-400 -mb-px'
                          : 'text-ink-400 hover:text-ink-200'
                      )}
                    >
                      {t}
                    </button>
                  ))}
                </div>
                <div className="p-5">
                  {tab === 0 && <ShapWaterfall factors={result.top_factors} />}
                  {tab === 1 && <CounterfactualCards counterfactuals={result.counterfactuals} />}
                </div>
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  )
}

function Stat({ label, value, mono, colored, icon }) {
  const COLORED_TEXT = {
    LOW:      '#22C55E',
    MODERATE: '#F59E0B',
    HIGH:     '#EF4444',
    CRITICAL: '#7C3AED',
  }
  return (
    <div className="rounded-lg bg-ink-800 px-3 py-2 border border-ink-700">
      <p className="text-xs text-ink-400 mb-0.5 flex items-center gap-1">{icon}{label}</p>
      <p
        className={clsx('text-sm font-semibold', mono && 'font-mono')}
        style={colored ? { color: COLORED_TEXT[colored] } : { color: '#E4E4EC' }}
      >
        {value}
      </p>
    </div>
  )
}
