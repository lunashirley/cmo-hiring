import { useQuery } from '@tanstack/react-query'
import { api, type RatingSummary } from '../lib/api'
import { cn } from '../lib/cn'

const PLATFORM_COLORS: Record<string, string> = {
  linkedin: 'bg-blue-500',
  x: 'bg-gray-500',
  newsletter: 'bg-purple-500',
  instagram: 'bg-pink-500',
}

export default function RatingsTab() {
  const { data: summary = [], isLoading } = useQuery<RatingSummary[]>({
    queryKey: ['ratings-summary'],
    queryFn: api.getRatingsSummary,
  })

  if (isLoading) return <div className="p-8 text-sm text-gray-400">Loading...</div>

  if (summary.length === 0) {
    return (
      <div className="p-8 max-w-2xl mx-auto">
        <div className="card p-10 text-center text-sm text-gray-400">
          No ratings yet. Rate outputs from the Outputs tab.
        </div>
      </div>
    )
  }

  const maxScore = 5

  return (
    <div className="p-6 max-w-3xl mx-auto space-y-6">
      <h1 className="text-lg font-semibold text-gray-900">Platform Performance</h1>

      <div className="grid grid-cols-2 gap-4">
        {summary.map((s) => (
          <div key={s.platform} className="card p-5">
            <div className="flex items-center justify-between mb-3">
              <span className="text-sm font-semibold text-gray-800 capitalize">{s.platform}</span>
              <span className="text-2xl font-bold text-gray-900">{s.avg_score.toFixed(1)}</span>
            </div>

            {/* Bar */}
            <div className="h-2 rounded-full bg-gray-100 overflow-hidden mb-3">
              <div
                className={cn('h-full rounded-full transition-all', PLATFORM_COLORS[s.platform] || 'bg-brand-500')}
                style={{ width: `${(s.avg_score / maxScore) * 100}%` }}
              />
            </div>

            <div className="flex justify-between text-xs text-gray-400">
              <span>{s.count} ratings</span>
              <span>Avg: {s.avg_score.toFixed(2)} / 5</span>
            </div>
          </div>
        ))}
      </div>

      {/* Summary table */}
      <div className="card overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 border-b border-gray-200">
            <tr>
              <th className="px-4 py-3 text-left label">Platform</th>
              <th className="px-4 py-3 text-right label">Avg Score</th>
              <th className="px-4 py-3 text-right label">Ratings</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {summary
              .sort((a, b) => b.avg_score - a.avg_score)
              .map((s) => (
                <tr key={s.platform} className="hover:bg-gray-50 transition-colors">
                  <td className="px-4 py-3 font-medium capitalize text-gray-800">{s.platform}</td>
                  <td className="px-4 py-3 text-right tabular-nums text-gray-700">{s.avg_score.toFixed(2)}</td>
                  <td className="px-4 py-3 text-right tabular-nums text-gray-500">{s.count}</td>
                </tr>
              ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
