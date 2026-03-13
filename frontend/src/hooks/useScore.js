import { useState, useCallback } from 'react'
import { scoreApplicant } from '../api'

const DEFAULTS = {
  age: 32,
  monthly_income: 45000,
  cibil_score: 680,
  loan_amount: 500000,
  loan_tenure_months: 36,
  emi_to_income_ratio: 0.35,
  debt_to_income_ratio: 0.45,
  employment_type: 0,
  years_employed: 4,
  existing_loans: 1,
  months_since_delinquency: 99,
  inquiries_last_6m: 2,
  payment_timing_score: 0.85,
  partial_payment_ratio: 0.05,
}

export function useScore() {
  const [form, setForm]     = useState(DEFAULTS)
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError]   = useState(null)

  const setField = useCallback((key, value) => {
    setForm(prev => ({ ...prev, [key]: value }))
  }, [])

  const submit = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      // Coerce all values to numbers before sending
      const payload = Object.fromEntries(
        Object.entries(form).map(([k, v]) => [k, Number(v)])
      )
      const data = await scoreApplicant(payload)
      setResult(data)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }, [form])

  const reset = useCallback(() => {
    setResult(null)
    setError(null)
    setForm(DEFAULTS)
  }, [])

  return { form, setField, result, loading, error, submit, reset }
}
