import { useEffect, useState } from 'react'
import { CheckCircle, XCircle, Loader, AlertTriangle } from 'lucide-react'
import { cn } from '../lib/cn'

interface StreamEvent {
  type: string
  platform?: string
  attempt?: number
  status?: string
  output_id?: string
  error?: string
  summary?: string
}

interface PlatformState {
  status: 'waiting' | 'generating' | 'qa' | 'pass' | 'fail' | 'escalated' | 'done'
  attempts: number
  outputId?: string
  summary?: string
}

const PLATFORMS = ['linkedin', 'x_twitter', 'newsletter', 'video_script']

const PLATFORM_LABELS: Record<string, string> = {
  linkedin: 'LinkedIn',
  x_twitter: 'X (Twitter)',
  newsletter: 'Newsletter',
  video_script: 'Video Script',
}

interface Props {
  runId: string
  onComplete: () => void
}

export default function GenerationStream({ runId, onComplete }: Props) {
  const [platforms, setPlatforms] = useState<Record<string, PlatformState>>(
    Object.fromEntries(PLATFORMS.map((p) => [p, { status: 'waiting', attempts: 0 }]))
  )
  const [log, setLog] = useState<string[]>([])
  const [done, setDone] = useState(false)

  useEffect(() => {
    const es = new EventSource(`/api/runs/${runId}/generate/stream`, { withCredentials: true })

    es.onmessage = (e) => {
      const event: StreamEvent = JSON.parse(e.data)

      if (event.type === 'heartbeat') return

      setLog((prev) => [...prev.slice(-50), `${event.type}${event.platform ? ` [${event.platform}]` : ''}${event.summary ? `: ${event.summary}` : ''}`])

      if (event.platform) {
        setPlatforms((prev) => {
          const cur = prev[event.platform!] || { status: 'waiting', attempts: 0 }
          const next = { ...cur }
          if (event.type === 'platform_start') {
            next.status = 'generating'
            next.attempts = event.attempt || 1
          } else if (event.type === 'hoc_start') {
            next.status = 'qa'
          } else if (event.type === 'hoc_pass') {
            next.status = 'pass'
          } else if (event.type === 'hoc_fail') {
            next.status = 'fail'
            next.summary = event.summary
          } else if (event.type === 'platform_done') {
            next.status = event.status === 'escalated' ? 'escalated' : 'done'
            next.outputId = event.output_id
            if (event.status === 'escalated' && event.summary) next.summary = event.summary
          }
          return { ...prev, [event.platform!]: next }
        })
      }

      if (event.type === 'complete') {
        setDone(true)
        es.close()
        // Hold the view for 1.5s so the user can read all platform results
        setTimeout(onComplete, 1500)
      }

      if (event.type === 'error') {
        setLog((prev) => [...prev, `ERROR: ${event.error}`])
      }
    }

    es.onerror = () => {
      setLog((prev) => [...prev, 'Stream disconnected'])
      es.close()
    }

    return () => es.close()
  }, [runId, onComplete])

  return (
    <div className="space-y-4">
      <h3 className="text-sm font-semibold text-gray-700">Generation Progress</h3>

      {/* Platform cards */}
      <div className="grid grid-cols-2 gap-3">
        {PLATFORMS.map((p) => {
          const state = platforms[p]
          return (
            <div key={p} className="card p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-gray-800">{PLATFORM_LABELS[p]}</span>
                <StatusIcon status={state.status} />
              </div>
              <div className="text-xs text-gray-400">
                {state.status === 'waiting' && 'Waiting...'}
                {state.status === 'generating' && `Generating (attempt ${state.attempts})`}
                {state.status === 'qa' && 'HoC reviewing...'}
                {state.status === 'pass' && 'QA passed'}
                {state.status === 'fail' && `QA failed (attempt ${state.attempts})`}
                {state.status === 'done' && 'Approved'}
                {state.status === 'escalated' && 'Escalated (3 attempts)'}
              </div>
              {(state.status === 'fail' || state.status === 'escalated') && state.summary && (
                <div className="text-xs text-red-500 mt-1 leading-relaxed">
                  {state.summary.length > 100 ? `${state.summary.slice(0, 100)}…` : state.summary}
                </div>
              )}
              {state.attempts > 1 && state.status !== 'waiting' && (
                <div className="text-xs text-amber-600 mt-1">{state.attempts} attempts</div>
              )}
            </div>
          )
        })}
      </div>

      {/* Log tail */}
      <div className="bg-gray-900 rounded-lg p-3 font-mono text-xs text-gray-300 h-28 overflow-y-auto space-y-0.5">
        {log.map((line, i) => (
          <div key={i}>{line}</div>
        ))}
        {!done && <div className="text-gray-500 animate-pulse">▋</div>}
      </div>

      {done && (
        <div className="flex items-center gap-2 text-green-700 text-sm font-medium">
          <CheckCircle size={16} />
          Generation complete
        </div>
      )}
    </div>
  )
}

function StatusIcon({ status }: { status: PlatformState['status'] }) {
  if (status === 'waiting') return <div className="w-4 h-4 rounded-full bg-gray-200" />
  if (status === 'generating' || status === 'qa')
    return <Loader size={16} className="text-brand-500 animate-spin" />
  if (status === 'pass' || status === 'done')
    return <CheckCircle size={16} className="text-green-500" />
  if (status === 'fail')
    return <AlertTriangle size={16} className="text-amber-500" />
  if (status === 'escalated')
    return <XCircle size={16} className="text-red-500" />
  return null
}
