import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Download, Edit2, Check, X, Star, ChevronDown, ChevronRight, Globe, FileText, Trash2 } from 'lucide-react'
import { api, type Output, type Run } from '../lib/api'
import { useStore } from '../store'
import { cn } from '../lib/cn'

const PLATFORM_COLORS: Record<string, string> = {
  linkedin: 'bg-blue-50 text-blue-700',
  x_twitter: 'bg-gray-100 text-gray-700',
  newsletter: 'bg-purple-50 text-purple-700',
  video_script: 'bg-orange-50 text-orange-700',
}

const STATUS_COLORS: Record<string, string> = {
  approved: 'text-green-600',
  escalated: 'text-red-500',
  edited: 'text-amber-600',
  final: 'text-brand-600',
  draft: 'text-gray-400',
}

const RATING_LABELS = ['', 'Worst', 'Low', 'Average', 'High', 'Best']
const RATING_TAGS = ['hook', 'length', 'CTA', 'atom choice', 'tone', 'format', 'timing', 'other']

export default function OutputsTab() {
  const { showToast } = useStore()
  const qc = useQueryClient()

  const { data: outputs = [], isLoading: outputsLoading } = useQuery<Output[]>({
    queryKey: ['all-outputs'],
    queryFn: api.listOutputs,
  })

  const { data: runs = [] } = useQuery<Run[]>({
    queryKey: ['runs'],
    queryFn: api.listRuns,
  })

  const [editing, setEditing] = useState<string | null>(null)
  const [editContent, setEditContent] = useState('')
  const [rating, setRating] = useState<{ id: string; score: number; tags: string[]; note: string } | null>(null)
  const [filterPlatform, setFilterPlatform] = useState<string>('all')
  const [collapsed, setCollapsed] = useState<Set<string>>(new Set())

  const editMutation = useMutation({
    mutationFn: ({ id, content }: { id: string; content: string }) => api.editOutput(id, content),
    onSuccess: () => {
      showToast('Output saved')
      setEditing(null)
      qc.invalidateQueries({ queryKey: ['all-outputs'] })
    },
    onError: (err: Error) => showToast(err.message, 'error'),
  })

  const deleteRunMutation = useMutation({
    mutationFn: (id: string) => api.deleteRun(id),
    onSuccess: () => {
      showToast('Run deleted')
      qc.invalidateQueries({ queryKey: ['all-outputs'] })
      qc.invalidateQueries({ queryKey: ['runs'] })
    },
    onError: (err: Error) => showToast(err.message, 'error'),
  })

  const [confirmDeleteRun, setConfirmDeleteRun] = useState<string | null>(null)

  const rateMutation = useMutation({
    mutationFn: ({ id, score, tags, note }: { id: string; score: number; tags: string[]; note: string }) =>
      api.rateOutput(id, score, tags, note || undefined),
    onSuccess: () => {
      showToast('Rating saved')
      setRating(null)
    },
    onError: (err: Error) => showToast(err.message, 'error'),
  })

  const runMap = new Map(runs.map((r) => [r.id, r]))

  const filtered = filterPlatform === 'all' ? outputs : outputs.filter((o) => o.platform === filterPlatform)

  // Group by run_id, preserving run order (most recent first)
  const groupedByRun = filtered.reduce<Map<string, Output[]>>((acc, o) => {
    if (!acc.has(o.run_id)) acc.set(o.run_id, [])
    acc.get(o.run_id)!.push(o)
    return acc
  }, new Map())

  const runIds = Array.from(groupedByRun.keys()).sort((a, b) => {
    const ra = runMap.get(a)
    const rb = runMap.get(b)
    return (rb?.created_at ?? '').localeCompare(ra?.created_at ?? '')
  })

  const toggleCollapse = (runId: string) => {
    setCollapsed((prev) => {
      const next = new Set(prev)
      next.has(runId) ? next.delete(runId) : next.add(runId)
      return next
    })
  }

  if (outputsLoading) return <div className="p-8 text-sm text-gray-400">Loading...</div>

  return (
    <div className="p-6 space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-lg font-semibold text-gray-900">Outputs</h1>
        <div className="flex gap-2">
          {['all', 'linkedin', 'x_twitter', 'newsletter', 'video_script'].map((p) => (
            <button
              key={p}
              onClick={() => setFilterPlatform(p)}
              className={cn('btn text-xs py-1 capitalize', filterPlatform === p ? 'btn-primary' : 'btn-secondary')}
            >
              {p === 'x_twitter' ? 'X (Twitter)' : p === 'video_script' ? 'Video Script' : p}
            </button>
          ))}
        </div>
      </div>

      {runIds.length === 0 && (
        <div className="card p-10 text-center text-sm text-gray-400">
          No outputs yet. Run the pipeline to generate content.
        </div>
      )}

      <div className="space-y-4">
        {runIds.map((runId) => {
          const run = runMap.get(runId)
          const runOutputs = groupedByRun.get(runId) ?? []
          const isCollapsed = collapsed.has(runId)

          return (
            <div key={runId} className="card overflow-hidden">
              {/* Run header */}
              <div className="flex items-center bg-gray-50 border-b border-gray-100">
                <button
                  onClick={() => toggleCollapse(runId)}
                  className="flex-1 flex items-center gap-3 px-5 py-3.5 hover:bg-gray-100 transition-colors text-left min-w-0"
                >
                  {isCollapsed ? <ChevronRight size={15} className="text-gray-400 flex-shrink-0" /> : <ChevronDown size={15} className="text-gray-400 flex-shrink-0" />}
                  <div className="min-w-0">
                    <div className="flex items-center gap-2">
                      {run?.source_type === 'url' ? (
                        <Globe size={13} className="text-gray-400 flex-shrink-0" />
                      ) : (
                        <FileText size={13} className="text-gray-400 flex-shrink-0" />
                      )}
                      <span className="text-sm font-medium text-gray-800 truncate">
                        {run?.url || 'Pasted text'}
                      </span>
                    </div>
                    <div className="text-xs text-gray-400 mt-0.5">
                      {run ? new Date(run.created_at).toLocaleString() : runId}
                    </div>
                  </div>
                  <div className="flex items-center gap-1.5 flex-shrink-0 ml-2">
                    {runOutputs.map((o) => (
                      <span key={o.id} className={cn('badge text-xs', PLATFORM_COLORS[o.platform] || 'bg-gray-100 text-gray-600')}>
                        {o.platform === 'x_twitter' ? 'X (Twitter)' : o.platform === 'video_script' ? 'Video Script' : o.platform}
                      </span>
                    ))}
                  </div>
                </button>
                {/* Delete run */}
                <div className="px-3 flex-shrink-0">
                  {confirmDeleteRun === runId ? (
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => { deleteRunMutation.mutate(runId); setConfirmDeleteRun(null) }}
                        className="text-xs text-red-600 font-medium hover:text-red-700"
                      >
                        Delete
                      </button>
                      <button
                        onClick={() => setConfirmDeleteRun(null)}
                        className="text-xs text-gray-400 hover:text-gray-600"
                      >
                        Cancel
                      </button>
                    </div>
                  ) : (
                    <button
                      onClick={(e) => { e.stopPropagation(); setConfirmDeleteRun(runId) }}
                      className="p-1 text-gray-400 hover:text-red-500 transition-colors"
                      title="Delete this run"
                    >
                      <Trash2 size={14} />
                    </button>
                  )}
                </div>
              </div>

              {/* Outputs for this run */}
              {!isCollapsed && (
                <div className="divide-y divide-gray-100">
                  {runOutputs.map((output) => (
                    <div key={output.id}>
                      <div className="flex items-center justify-between px-5 py-3 bg-white">
                        <div className="flex items-center gap-3">
                          <span className={cn('badge', PLATFORM_COLORS[output.platform] || 'bg-gray-100 text-gray-600')}>
                            {output.platform === 'x_twitter' ? 'X (Twitter)' : output.platform}
                          </span>
                          <span className={cn('text-xs font-medium', STATUS_COLORS[output.status] || 'text-gray-400')}>
                            {output.status}
                          </span>
                          {output.qa_attempts > 1 && (
                            <span className="text-xs text-gray-400">{output.qa_attempts} QA attempts</span>
                          )}
                        </div>
                        <div className="flex items-center gap-2">
                          <button
                            onClick={() => setRating({ id: output.id, score: 3, tags: [], note: '' })}
                            className="btn-ghost text-xs py-1"
                          >
                            <Star size={12} /> Rate
                          </button>
                          <button
                            onClick={() => {
                              setEditing(output.id)
                              setEditContent(output.content)
                            }}
                            className="btn-ghost text-xs py-1"
                          >
                            <Edit2 size={12} /> Edit
                          </button>
                          <a href={api.exportUrl(output.id)} download className="btn-secondary text-xs py-1">
                            <Download size={12} /> Export
                          </a>
                        </div>
                      </div>

                      <div className="px-5 py-4 bg-white">
                        {editing === output.id ? (
                          <div className="space-y-3">
                            <textarea
                              className="input font-mono text-xs resize-none"
                              rows={15}
                              value={editContent}
                              onChange={(e) => setEditContent(e.target.value)}
                            />
                            <div className="flex gap-2">
                              <button
                                onClick={() => editMutation.mutate({ id: output.id, content: editContent })}
                                disabled={editMutation.isPending}
                                className="btn-primary text-xs"
                              >
                                <Check size={12} /> {editMutation.isPending ? 'Saving...' : 'Save'}
                              </button>
                              <button onClick={() => setEditing(null)} className="btn-ghost text-xs">
                                <X size={12} /> Cancel
                              </button>
                            </div>
                          </div>
                        ) : (
                          <pre className="text-sm text-gray-800 whitespace-pre-wrap leading-relaxed font-sans">
                            {output.content}
                          </pre>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )
        })}
      </div>

      {/* Rating modal */}
      {rating && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-40" onClick={() => setRating(null)}>
          <div className="card p-6 w-full max-w-sm" onClick={(e) => e.stopPropagation()}>
            <h3 className="text-base font-semibold text-gray-900 mb-4">Rate this output</h3>

            <div className="flex gap-2 mb-4">
              {[1, 2, 3, 4, 5].map((s) => (
                <button
                  key={s}
                  onClick={() => setRating({ ...rating, score: s })}
                  className={cn(
                    'flex-1 py-2 rounded-lg text-sm font-medium border transition-colors',
                    rating.score === s
                      ? 'bg-brand-600 text-white border-brand-600'
                      : 'border-gray-200 text-gray-600 hover:border-brand-300',
                  )}
                >
                  {RATING_LABELS[s]}
                </button>
              ))}
            </div>

            <div className="mb-4">
              <p className="text-xs text-gray-500 mb-2">What drove this? (optional)</p>
              <div className="flex flex-wrap gap-1.5">
                {RATING_TAGS.map((tag) => (
                  <button
                    key={tag}
                    onClick={() =>
                      setRating({
                        ...rating,
                        tags: rating.tags.includes(tag)
                          ? rating.tags.filter((t) => t !== tag)
                          : [...rating.tags.slice(0, 2), tag],
                      })
                    }
                    className={cn(
                      'badge border text-xs cursor-pointer transition-colors',
                      rating.tags.includes(tag)
                        ? 'bg-brand-50 text-brand-700 border-brand-300'
                        : 'bg-gray-50 text-gray-600 border-gray-200 hover:border-gray-300',
                    )}
                  >
                    {tag}
                  </button>
                ))}
              </div>
            </div>

            <textarea
              className="input text-sm resize-none mb-4"
              placeholder="Optional note..."
              rows={2}
              value={rating.note}
              onChange={(e) => setRating({ ...rating, note: e.target.value })}
            />

            <div className="flex gap-2">
              <button
                onClick={() => rateMutation.mutate(rating)}
                disabled={rateMutation.isPending}
                className="btn-primary flex-1 justify-center"
              >
                Save Rating
              </button>
              <button onClick={() => setRating(null)} className="btn-secondary">Cancel</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
