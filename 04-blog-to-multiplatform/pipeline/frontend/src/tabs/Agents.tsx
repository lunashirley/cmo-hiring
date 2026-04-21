import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Save, History, ChevronRight, X } from 'lucide-react'
import { api, type AgentMeta, type AgentFull, type AgentHistoryEntry } from '../lib/api'
import { useStore } from '../store'
import { cn } from '../lib/cn'

const AGENT_DESCRIPTIONS: Record<string, string> = {
  atom_extractor: 'Extracts typed content atoms from source text',
  linkedin: 'Generates LinkedIn posts',
  x: 'Generates X (Twitter) posts or threads',
  newsletter: 'Generates newsletter sections',
  instagram: 'Generates Instagram carousel copy',
  head_of_content: 'QA reviewer with per-platform rubric',
}

export default function AgentsTab() {
  const { showToast } = useStore()
  const qc = useQueryClient()

  const [selected, setSelected] = useState<string | null>(null)
  const [editContent, setEditContent] = useState('')
  const [showHistory, setShowHistory] = useState(false)

  const { data: agents = [] } = useQuery<AgentMeta[]>({
    queryKey: ['agents'],
    queryFn: api.listAgents,
  })

  const { data: full } = useQuery<AgentFull>({
    queryKey: ['agent', selected],
    queryFn: () => api.getAgent(selected!),
    enabled: !!selected,
  })

  const { data: history = [] } = useQuery<AgentHistoryEntry[]>({
    queryKey: ['agent-history', selected],
    queryFn: () => api.getAgentHistory(selected!),
    enabled: !!selected && showHistory,
  })

  useEffect(() => {
    if (full) setEditContent(full.content)
  }, [full?.name])

  const saveMutation = useMutation({
    mutationFn: () => api.updateAgent(selected!, editContent),
    onSuccess: () => {
      showToast('Agent config saved')
      qc.invalidateQueries({ queryKey: ['agents'] })
      qc.invalidateQueries({ queryKey: ['agent', selected] })
      qc.invalidateQueries({ queryKey: ['agent-history', selected] })
    },
    onError: (err: Error) => showToast(err.message, 'error'),
  })

  return (
    <div className="flex h-[calc(100vh-112px)]">
      {/* Sidebar */}
      <div className="w-56 border-r border-gray-200 bg-white flex-shrink-0">
        <div className="p-3 border-b border-gray-100">
          <p className="text-xs text-gray-500 px-1">Changes take effect on next run — no restart needed.</p>
        </div>
        <div className="py-2">
          {agents.length === 0 && <p className="p-4 text-xs text-gray-400">No agents found</p>}
          {agents.map((a) => (
            <button
              key={a.name}
              onClick={() => { setSelected(a.name); setShowHistory(false) }}
              className={cn(
                'w-full text-left px-3 py-2.5 flex items-center justify-between group hover:bg-gray-50 transition-colors',
                selected === a.name && 'bg-brand-50',
              )}
            >
              <div>
                <div className={cn('text-sm font-medium', selected === a.name ? 'text-brand-700' : 'text-gray-700')}>
                  {a.name}
                </div>
                <div className="text-xs text-gray-400">{AGENT_DESCRIPTIONS[a.name] || `v${a.version}`}</div>
              </div>
              <ChevronRight size={14} className="text-gray-300 group-hover:text-gray-400" />
            </button>
          ))}
        </div>
      </div>

      {/* Editor */}
      <div className="flex-1 flex flex-col min-w-0">
        {selected ? (
          <>
            <div className="px-6 py-3 border-b border-gray-200 flex items-center justify-between bg-white flex-shrink-0">
              <div className="flex items-center gap-3">
                <span className="text-sm font-medium text-gray-700">{selected}</span>
                <span className="text-xs text-gray-400">v{full?.version}</span>
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setShowHistory(!showHistory)}
                  className={cn('btn-ghost text-xs', showHistory && 'bg-gray-100')}
                >
                  <History size={13} /> History
                </button>
                <button
                  onClick={() => saveMutation.mutate()}
                  disabled={saveMutation.isPending}
                  className="btn-primary text-xs"
                >
                  <Save size={13} /> {saveMutation.isPending ? 'Saving...' : 'Save'}
                </button>
              </div>
            </div>

            <div className="flex flex-1 min-h-0">
              <textarea
                className="flex-1 font-mono text-sm p-6 resize-none focus:outline-none focus:ring-2 focus:ring-brand-500 focus:ring-inset bg-white"
                value={editContent}
                onChange={(e) => setEditContent(e.target.value)}
                spellCheck={false}
              />

              {showHistory && (
                <div className="w-64 border-l border-gray-200 bg-gray-50 flex flex-col flex-shrink-0">
                  <div className="px-4 py-3 border-b border-gray-200 flex items-center justify-between">
                    <span className="text-xs font-medium text-gray-700">Version history</span>
                    <button onClick={() => setShowHistory(false)} className="text-gray-400 hover:text-gray-600">
                      <X size={14} />
                    </button>
                  </div>
                  <div className="flex-1 overflow-y-auto divide-y divide-gray-100">
                    {history.length === 0 && (
                      <p className="p-4 text-xs text-gray-400">No previous versions</p>
                    )}
                    {history.map((entry, i) => (
                      <div key={i} className="p-3">
                        <div className="text-xs font-medium text-gray-700">v{entry.version}</div>
                        <div className="text-xs text-gray-400 mb-2">
                          {new Date(entry.created_at).toLocaleString()}
                        </div>
                        <button
                          onClick={() => setEditContent(entry.content)}
                          className="text-xs text-brand-600 hover:text-brand-700"
                        >
                          Restore this version
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </>
        ) : (
          <div className="flex-1 flex items-center justify-center text-sm text-gray-400">
            Select an agent to view and edit its config
          </div>
        )}
      </div>
    </div>
  )
}
