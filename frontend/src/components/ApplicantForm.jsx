import { Loader2 } from 'lucide-react'
import clsx from 'clsx'

const SECTIONS = [
  {
    title: 'Demographics',
    fields: [
      { key: 'age', label: 'Age', type: 'number', min: 18, max: 75, step: 1, suffix: 'yrs' },
      { key: 'monthly_income', label: 'Monthly Income', type: 'number', min: 8000, max: 500000, step: 1000, prefix: '₹' },
    ],
  },
  {
    title: 'Loan Details',
    fields: [
      { key: 'loan_amount', label: 'Loan Amount', type: 'number', min: 100000, max: 5000000, step: 50000, prefix: '₹' },
      { key: 'loan_tenure_months', label: 'Tenure', type: 'number', min: 6, max: 120, step: 6, suffix: 'mo' },
      { key: 'emi_to_income_ratio', label: 'EMI / Income', type: 'number', min: 0.05, max: 0.95, step: 0.01, suffix: '' },
      { key: 'debt_to_income_ratio', label: 'Debt / Income', type: 'number', min: 0.05, max: 1.5, step: 0.01, suffix: '' },
    ],
  },
  {
    title: 'Credit Profile',
    fields: [
      { key: 'cibil_score', label: 'CIBIL Score', type: 'number', min: 300, max: 900, step: 1 },
      { key: 'existing_loans', label: 'Existing Loans', type: 'number', min: 0, max: 20, step: 1 },
      { key: 'months_since_delinquency', label: 'Months Since Delinquency', type: 'number', min: 0, max: 99, step: 1, hint: '99 = never' },
      { key: 'inquiries_last_6m', label: 'Credit Inquiries (6m)', type: 'number', min: 0, max: 20, step: 1 },
    ],
  },
  {
    title: 'Employment',
    fields: [
      {
        key: 'employment_type', label: 'Employment Type', type: 'select',
        options: [{ value: 0, label: 'Salaried' }, { value: 1, label: 'Self-Employed' }, { value: 2, label: 'Business Owner' }],
      },
      { key: 'years_employed', label: 'Years at Job', type: 'number', min: 0, max: 40, step: 0.5, suffix: 'yrs' },
    ],
  },
  {
    title: 'Behavioral Signals',
    fields: [
      { key: 'payment_timing_score', label: 'Payment Timing Score', type: 'number', min: 0, max: 1, step: 0.01, hint: '1.0 = always on time' },
      { key: 'partial_payment_ratio', label: 'Partial Payment Ratio', type: 'number', min: 0, max: 1, step: 0.01, hint: '0 = always full EMI' },
    ],
  },
]

export default function ApplicantForm({ form, setField, onSubmit, loading }) {
  return (
    <form
      onSubmit={e => { e.preventDefault(); onSubmit() }}
      className="space-y-6"
    >
      {SECTIONS.map(section => (
        <div key={section.title}>
          <h3 className="text-xs font-semibold tracking-widest text-ink-400 uppercase mb-3">
            {section.title}
          </h3>
          <div className="grid grid-cols-2 gap-3">
            {section.fields.map(field => (
              <div key={field.key} className={field.type === 'select' ? 'col-span-2' : ''}>
                <label className="block text-xs text-ink-400 mb-1">
                  {field.label}
                  {field.hint && <span className="ml-1 opacity-60">({field.hint})</span>}
                </label>

                {field.type === 'select' ? (
                  <select
                    value={form[field.key]}
                    onChange={e => setField(field.key, Number(e.target.value))}
                    className="w-full bg-ink-800 border border-ink-600 rounded-lg px-3 py-2 text-sm text-ink-100 focus:outline-none focus:border-acid-400/60 transition-colors"
                  >
                    {field.options.map(opt => (
                      <option key={opt.value} value={opt.value}>{opt.label}</option>
                    ))}
                  </select>
                ) : (
                  <div className="relative">
                    {field.prefix && (
                      <span className="absolute left-3 top-1/2 -translate-y-1/2 text-xs text-ink-400">
                        {field.prefix}
                      </span>
                    )}
                    <input
                      type="number"
                      value={form[field.key]}
                      min={field.min}
                      max={field.max}
                      step={field.step}
                      onChange={e => setField(field.key, e.target.value)}
                      className={clsx(
                        'w-full bg-ink-800 border border-ink-600 rounded-lg py-2 text-sm text-ink-100',
                        'focus:outline-none focus:border-acid-400/60 transition-colors',
                        field.prefix ? 'pl-6 pr-3' : 'px-3',
                        field.suffix ? 'pr-10' : ''
                      )}
                    />
                    {field.suffix && (
                      <span className="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-ink-400">
                        {field.suffix}
                      </span>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      ))}

      <button
        type="submit"
        disabled={loading}
        className={clsx(
          'w-full py-3 rounded-xl font-semibold text-sm transition-all duration-200',
          'flex items-center justify-center gap-2',
          loading
            ? 'bg-ink-600 text-ink-400 cursor-not-allowed'
            : 'bg-acid-400 text-ink-900 hover:bg-acid-300 active:scale-[0.98]'
        )}
        style={!loading ? { boxShadow: '0 0 24px rgba(184,255,60,0.3)' } : {}}
      >
        {loading ? (
          <>
            <Loader2 size={16} className="animate-spin" />
            Scoring…
          </>
        ) : (
          'Assess Risk'
        )}
      </button>
    </form>
  )
}
