import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { api, type LogEntry, type Scorecard } from '../lib/api'
import { cn } from '../lib/cn'

const EVENT_COLORS: Record<string, string> = {
  start: 'text-blue-600 bg-blue-50',
  response: 'text-green-700 bg-green-50',
  pass: 'text-green-700 bg-green-50',
  fail: 'text-red-600 bg-red-50',
  retry: 'text-amber-700 bg-amber-50',
  error: 'text-red-700 bg-red-50',
  prompt: 'text-gray-600 bg-gray-50',
}

export default function LogsTab() {
  const [agentFilter, setAgentFilter] = useState('')
  const [eventFilter, setEventFilter] = useState('')

  const { data: logs = [], isLoading: logsLoading } = useQuery<LogEntry[]>({
    queryKey: ['logs', agentFilter, eventFilter],
    queryFn: () => api.getLogs({
      agent: agentFilter || undefined,
      event: eventFilter || undefined,
      limit: 100,
    }),
    refetchInterval: 5000,
  })

  const { data: scorecards = [] } = useQuery<Scorecard[]>({
    queryKey: ['scorecards'],
    queryFn: api.getScorecards,
    refetchInterval: 10000,
  })

  const agents = ['extractor', 'linkedin', 'x', 'newsletter', 'instagram', 'hoc']
  const events = ['start', 'response', 'retry', 'pass', 'fail', 'error']

  return (
    <div className="p-6 space-y-6">
      <h1 className="text-lg font-semibold text-gray-900">Logs & Observability</h1>

      {/* Scorecards */}
      {scorecards.length > 0 && (
        <div>
          <h2 className="text-sm font-semibold text-gray-700 mb-3">Agent Scorecards</h2>
          <div className="overflow-x-auto">
            <table className="w-full text-sm card overflow-hidden">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="px-4 py-3 text-left label">Agent</th>
                  <th className="px-4 py-3 text-right label">Calls</th>
                  <th className="px-4 py-3 text-right label">Avg ms</th>
                  <th className="px-4 py-3 text-right label">Retry rate</th>
                  <th className="px-4 py-3 text-right label">Pass rate</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {scorecards.map((s) => (
                  <tr key={s.agent} className="hover:bg-gray-50 transition-colors">
                    <td className="px-4 py-3 font-mono text-sm text-gray-800">{s.agent}</td>
                    <td className="px-4 py-3 text-right tabular-nums text-gray-600">{s.calls}</td>
                    <td className="px-4 py-3 text-right tabular-nums text-gray-600">{s.avg_ms.toLocaleString()}</td>
                    <td className="px-4 py-3 text-right tabular-nums">
                      <span className={cn('font-medium', s.retry_rate > 0.3 ? 'text-amber-600' : 'text-gray-600')}>
                        {(s.retry_rate * 100).toFixed(0)}%
                      </span>
                    </td>
                    <td className="px-4 py-3 text-right tabular-nums">
                      <span className={cn('font-medium', s.pass_rate < 0.7 ? 'text-red-500' : 'text-green-600')}>
                        {(s.pass_rate * 100).toFixed(0)}%
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="card p-4 flex gap-3 items-center flex-wrap">
        <select
          className="input w-40 text-sm"
          value={agentFilter}
          onChange={(e) => setAgentFilter(e.target.value)}
        >
          <option value="">All agents</option>
          {agents.map((a) => <option key={a} value={a}>{a}</option>)}
        </select>
        <select
          className="input w-40 text-sm"
          value={eventFilter}
          onChange={(e) => setEventFilter(e.target.value)}
        >
          <option value="">All events</option>
          {events.map((e) => <option key={e} value={e}>{e}</option>)}
        </select>
        <span className="text-xs text-gray-400">{logs.length} entries (auto-refreshes every 5s)</span>
      </div>

      {/* Log table */}
      {logsLoading ? (
        <div className="text-sm text-gray-400">Loading...</div>
      ) : (
        <div className="card overflow-hidden">
          <div className="overflow-x-auto max-h-[500px] overflow-y-auto">
            <table className="w-full text-xs">
              <thead className="bg-gray-50 border-b border-gray-200 sticky top-0">
                <tr>
                  <th className="px-3 py-2.5 text-left label">Time</th>
                  <th className="px-3 py-2.5 text-left label">Agent</th>
                  <th className="px-3 py-2.5 text-left label">Event</th>
                  <th className="px-3 py-2.5 text-right label">Attempt</th>
                  <th className="px-3 py-2.5 text-right label">ms</th>
                  <th className="px-3 py-2.5 text-right label">Tokens in</th>
                  <th className="px-3 py-2.5 text-right label">Tokens out</th>
                  <th className="px-3 py-2.5 text-left label">Notes</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {logs.map((log) => (
                  <tr key={log.id} className="hover:bg-gray-50 transition-colors font-mono">
                    <td className="px-3 py-2 text-gray-400 whitespace-nowrap">
                      {new Date(log.ts).toLocaleTimeString()}
                    </td>
                    <td className="px-3 py-2 text-gray-700">{log.agent}</td>
                    <td className="px-3 py-2">
                      <span className={cn('badge', EVENT_COLORS[log.event] || 'bg-gray-100 text-gray-600')}>
                        {log.event}
                      </span>
                    </td>
                    <td className="px-3 py-2 text-right text-gray-500">{log.attempt}</td>
                    <td className="px-3 py-2 text-right tabular-nums text-gray-500">
                      {log.duration_ms > 0 ? log.duration_ms.toLocaleString() : '-'}
                    </td>
                    <td className="px-3 py-2 text-right tabular-nums text-gray-500">
                      {log.token_in > 0 ? log.token_in : '-'}
                    </td>
                    <td className="px-3 py-2 text-right tabular-nums text-gray-500">
                      {log.token_out > 0 ? log.token_out : '-'}
                    </td>
                    <td className="px-3 py-2 text-gray-400 max-w-xs truncate">{log.notes || ''}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            {logs.length === 0 && (
              <div className="px-4 py-8 text-center text-sm text-gray-400">No log entries match the current filters</div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
