const BASE = '/api'

async function req<T>(method: string, path: string, body?: unknown): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method,
    credentials: 'include',
    headers: body ? { 'Content-Type': 'application/json' } : undefined,
    body: body ? JSON.stringify(body) : undefined,
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || 'Request failed')
  }
  return res.json()
}

export const api = {
  // Auth
  login: (password: string) => req<{ ok: boolean }>('POST', '/auth/login', { password }),
  logout: () => req<{ ok: boolean }>('POST', '/auth/logout'),
  me: () => req<{ username: string }>('GET', '/auth/me'),

  // Settings
  getSettings: () => req<Record<string, string>>('GET', '/settings'),
  updateSettings: (settings: Record<string, string>) => req('PUT', '/settings', { settings }),

  // Runs
  createRun: (url?: string, pasted_text?: string) => req<{ run_id: string; status: string }>('POST', '/runs', { url, pasted_text }),
  listRuns: () => req<Run[]>('GET', '/runs'),
  getRun: (id: string) => req<Run>('GET', `/runs/${id}`),
  deleteRun: (id: string) => req<{ ok: boolean }>('DELETE', `/runs/${id}`),

  // Atoms
  getAtoms: (runId: string) => req<Atom[]>('GET', `/runs/${runId}/atoms`),
  updateAtom: (runId: string, atomId: string, data: Partial<Atom>) =>
    req<Atom>('PUT', `/runs/${runId}/atoms/${atomId}`, data),
  addAtom: (runId: string, data: { type: string; text: string; proposed_angle?: string }) =>
    req<Atom>('POST', `/runs/${runId}/atoms`, data),
  deleteAtom: (runId: string, atomId: string) =>
    req<{ ok: boolean }>('DELETE', `/runs/${runId}/atoms/${atomId}`),
  reorderAtoms: (runId: string, atomIds: string[]) =>
    req<{ ok: boolean }>('POST', `/runs/${runId}/atoms/reorder`, { atom_ids: atomIds }),
  setBrandVoice: (runId: string, slug: string) =>
    req<{ ok: boolean }>('POST', `/runs/${runId}/brand-voice`, { brand_voice_slug: slug }),
  bulkApprove: (runId: string) =>
    req<{ ok: boolean }>('POST', `/runs/${runId}/atoms/bulk-approve`),

  // Generation
  startGeneration: (runId: string) =>
    req<{ ok: boolean }>('POST', `/runs/${runId}/generate/start`),

  // Outputs
  getOutputs: (runId: string) => req<Output[]>('GET', `/runs/${runId}/outputs`),
  listOutputs: () => req<Output[]>('GET', '/outputs'),
  editOutput: (id: string, content: string) =>
    req<{ id: string; diff: string }>('PUT', `/outputs/${id}`, { content }),
  exportUrl: (id: string, fmt = 'md') => `${BASE}/outputs/${id}/export?fmt=${fmt}`,

  // Ratings
  rateOutput: (id: string, score: number, tags: string[], note?: string) =>
    req('POST', `/outputs/${id}/rate`, { score, tags, note }),
  getRatingsSummary: () => req<RatingSummary[]>('GET', '/ratings'),

  // Brand voices
  listBrandVoices: () => req<BrandVoiceMeta[]>('GET', '/brand-voices'),
  getBrandVoice: (slug: string) => req<BrandVoiceFull>('GET', `/brand-voices/${slug}`),
  createBrandVoice: (slug: string, content: string) =>
    req('POST', '/brand-voices', { slug, content }),
  updateBrandVoice: (slug: string, content: string) =>
    req('PUT', `/brand-voices/${slug}`, { slug, content }),

  // Agents
  listAgents: () => req<AgentMeta[]>('GET', '/agents'),
  getAgent: (name: string) => req<AgentFull>('GET', `/agents/${name}`),
  updateAgent: (name: string, content: string) =>
    req('PUT', `/agents/${name}`, { content }),
  getAgentHistory: (name: string) => req<AgentHistoryEntry[]>('GET', `/agents/${name}/history`),

  // Logs
  getLogs: (params?: { run_id?: string; agent?: string; event?: string; limit?: number }) => {
    const filtered: Record<string, string> = {}
    if (params) {
      for (const [k, v] of Object.entries(params)) {
        if (v !== undefined && v !== null && v !== '') filtered[k] = String(v)
      }
    }
    const q = new URLSearchParams(filtered).toString()
    return req<LogEntry[]>('GET', `/logs${q ? `?${q}` : ''}`)
  },
  getScorecards: () => req<Scorecard[]>('GET', '/logs/scorecards'),
}

// Types
export interface Run {
  id: string
  url?: string
  source_type: string
  status: string
  brand_voice_slug?: string
  created_at: string
  error_msg?: string
}

export interface Atom {
  id: string
  run_id: string
  type: 'stat' | 'insight' | 'quote' | 'anecdote'
  text: string
  original_text: string
  is_edited: boolean
  proposed_angle: string
  confidence: number
  origin: 'extracted' | 'manual'
  priority: number
  approved: boolean
}

export interface Output {
  id: string
  run_id: string
  platform: string
  version: number
  content: string
  metadata: Record<string, unknown>
  status: string
  qa_attempts: number
  created_at: string
}

export interface RatingSummary {
  platform: string
  avg_score: number
  count: number
}

export interface BrandVoiceMeta {
  slug: string
  name: string
  version: number
  archived?: boolean
}

export interface BrandVoiceFull extends BrandVoiceMeta {
  content: string
  body: string
}

export interface AgentMeta {
  name: string
  version: number
}

export interface AgentFull extends AgentMeta {
  content: string
  body: string
}

export interface AgentHistoryEntry {
  version: number
  created_at: string
  content: string
}

export interface LogEntry {
  id: number
  ts: string
  run_id?: string
  agent: string
  event: string
  attempt: number
  duration_ms: number
  token_in: number
  token_out: number
  notes?: string
}

export interface Scorecard {
  agent: string
  calls: number
  avg_ms: number
  retry_rate: number
  pass_rate: number
}
