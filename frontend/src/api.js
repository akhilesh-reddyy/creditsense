const BASE = '/api/v1'

export async function scoreApplicant(data) {
  const res = await fetch(`${BASE}/score`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || `HTTP ${res.status}`)
  }
  return res.json()
}

export async function getFeatures() {
  const res = await fetch(`${BASE}/features`)
  if (!res.ok) throw new Error('Failed to load feature metadata')
  return res.json()
}

export async function getMetrics() {
  const res = await fetch(`${BASE}/metrics`)
  if (!res.ok) throw new Error('Failed to load metrics')
  return res.json()
}

export async function healthCheck() {
  const res = await fetch(`${BASE}/health`)
  if (!res.ok) return { status: 'error', model_loaded: false }
  return res.json()
}
