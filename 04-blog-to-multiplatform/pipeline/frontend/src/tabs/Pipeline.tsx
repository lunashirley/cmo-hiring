import { useState, useCallback } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  type DragEndEvent,
} from '@dnd-kit/core'
import {
  SortableContext,
  sortableKeyboardCoordinates,
  verticalListSortingStrategy,
} from '@dnd-kit/sortable'
import { restrictToVerticalAxis } from '@dnd-kit/modifiers'
import { Plus, Play, CheckSquare, Globe, FileText } from 'lucide-react'
import { api, type Run, type Atom } from '../lib/api'
import { useStore } from '../store'
import AtomCard from '../components/AtomCard'
import GenerationStream from '../components/GenerationStream'

type Stage = 'input' | 'ingesting' | 'extracting' | 'hitl' | 'generating' | 'done' | 'error'

export default function PipelineTab() {
  const { showToast, setActiveRunId, activeRunId, setActiveTab } = useStore()
  const qc = useQueryClient()

  const [url, setUrl] = useState('')
  const [pasteMode, setPasteMode] = useState(false)
  const [pastedText, setPastedText] = useState('')
  const [stage, setStage] = useState<Stage>('input')
  const [runId, setRunId] = useState<string | null>(null)
  const [newAtomText, setNewAtomText] = useState('')
  const [newAtomType, setNewAtomType] = useState('insight')
  const [addingAtom, setAddingAtom] = useState(false)

  // Poll run status — stop during 'generating' (SSE handles that transition)
  const { data: run } = useQuery<Run>({
    queryKey: ['run', runId],
    queryFn: () => api.getRun(runId!),
    enabled: !!runId && ['ingesting', 'extracting'].includes(stage),
    refetchInterval: (query) => {
      const s = query.state.data?.status
      return s && ['hitl', 'done', 'error'].includes(s) ? false : 2000
    },
  })

  // Sync stage from run status
  if (run && run.status !== stage) {
    if (['extracting', 'hitl', 'done', 'error', 'generating'].includes(run.status)) {
      setStage(run.status as Stage)
    }
  }

  const { data: atoms = [], refetch: refetchAtoms } = useQuery<Atom[]>({
    queryKey: ['atoms', runId],
    queryFn: () => api.getAtoms(runId!),
    enabled: !!runId && stage === 'hitl',
  })

  const { data: brandVoices = [] } = useQuery({
    queryKey: ['brand-voices'],
    queryFn: api.listBrandVoices,
  })

  const [selectedVoice, setSelectedVoice] = useState('')

  const createRunMutation = useMutation({
    mutationFn: () =>
      pasteMode ? api.createRun(undefined, pastedText) : api.createRun(url || undefined),
    onSuccess: (data) => {
      setRunId(data.run_id)
      setActiveRunId(data.run_id)
      setStage('ingesting')
    },
    onError: (err: Error) => showToast(err.message, 'error'),
  })

  const updateAtomMutation = useMutation({
    mutationFn: ({ atomId, updates }: { atomId: string; updates: Partial<Atom> }) =>
      api.updateAtom(runId!, atomId, updates),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['atoms', runId] }),
    onError: (err: Error) => showToast(err.message, 'error'),
  })

  const deleteAtomMutation = useMutation({
    mutationFn: (atomId: string) => api.deleteAtom(runId!, atomId),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['atoms', runId] }),
    onError: (err: Error) => showToast(err.message, 'error'),
  })

  const addAtomMutation = useMutation({
    mutationFn: () => api.addAtom(runId!, { type: newAtomType, text: newAtomText }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['atoms', runId] })
      setNewAtomText('')
      setAddingAtom(false)
    },
    onError: (err: Error) => showToast(err.message, 'error'),
  })

  const startGenerationMutation = useMutation({
    mutationFn: async () => {
      if (selectedVoice) await api.setBrandVoice(runId!, selectedVoice)
      return api.startGeneration(runId!)
    },
    onSuccess: () => {
      // Clear stale cached run status ('hitl') so it can't snap us back mid-generation
      qc.removeQueries({ queryKey: ['run', runId] })
      setStage('generating')
    },
    onError: (err: Error) => showToast(err.message, 'error'),
  })

  const sensors = useSensors(
    useSensor(PointerSensor),
    useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates }),
  )

  const handleDragEnd = useCallback(
    async (event: DragEndEvent) => {
      const { active, over } = event
      if (!over || active.id === over.id) return
      const oldIndex = atoms.findIndex((a) => a.id === active.id)
      const newIndex = atoms.findIndex((a) => a.id === over.id)
      if (oldIndex === -1 || newIndex === -1) return
      const reordered = [...atoms]
      const [moved] = reordered.splice(oldIndex, 1)
      reordered.splice(newIndex, 0, moved)
      await api.reorderAtoms(runId!, reordered.map((a) => a.id))
      qc.invalidateQueries({ queryKey: ['atoms', runId] })
    },
    [atoms, runId, qc],
  )

  const approvedCount = atoms.filter((a) => a.approved).length
  const canGenerate = approvedCount > 0 && selectedVoice

  // ── Render ──────────────────────────────────────────────────────────────────

  if (stage === 'input') {
    return (
      <div className="max-w-2xl mx-auto p-8">
        <h1 className="text-xl font-semibold text-gray-900 mb-1">New Pipeline Run</h1>
        <p className="text-sm text-gray-500 mb-6">Paste a blog URL or raw text to start extracting content atoms.</p>

        <div className="card p-6 space-y-4">
          <div className="flex gap-3 mb-1">
            <button
              onClick={() => setPasteMode(false)}
              className={`text-sm font-medium pb-1 border-b-2 transition-colors ${!pasteMode ? 'border-brand-600 text-brand-600' : 'border-transparent text-gray-400'}`}
            >
              <Globe size={14} className="inline mr-1.5" />URL
            </button>
            <button
              onClick={() => setPasteMode(true)}
              className={`text-sm font-medium pb-1 border-b-2 transition-colors ${pasteMode ? 'border-brand-600 text-brand-600' : 'border-transparent text-gray-400'}`}
            >
              <FileText size={14} className="inline mr-1.5" />Paste text
            </button>
          </div>

          {!pasteMode ? (
            <input
              type="url"
              className="input"
              placeholder="https://www.reservio.com/blog/..."
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && createRunMutation.mutate()}
            />
          ) : (
            <textarea
              className="input resize-none"
              placeholder="Paste article text here..."
              rows={8}
              value={pastedText}
              onChange={(e) => setPastedText(e.target.value)}
            />
          )}

          <button
            onClick={() => createRunMutation.mutate()}
            disabled={createRunMutation.isPending || (!url && !pastedText)}
            className="btn-primary w-full justify-center"
          >
            {createRunMutation.isPending ? 'Starting...' : 'Start Pipeline'}
          </button>
        </div>
      </div>
    )
  }

  if (stage === 'ingesting' || stage === 'extracting') {
    return (
      <div className="max-w-2xl mx-auto p-8 text-center">
        <div className="card p-10">
          <div className="w-10 h-10 border-2 border-brand-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <h2 className="text-base font-semibold text-gray-900 mb-1">
            {stage === 'ingesting' ? 'Fetching article...' : 'Extracting content atoms...'}
          </h2>
          <p className="text-sm text-gray-400">
            {stage === 'ingesting'
              ? 'Retrieving content via Jina Reader'
              : 'Analyzing article and identifying reusable atoms'}
          </p>
        </div>
      </div>
    )
  }

  if (stage === 'error') {
    return (
      <div className="max-w-2xl mx-auto p-8">
        <div className="card p-6 border-red-200">
          <p className="text-red-700 font-medium mb-2">Pipeline error</p>
          <p className="text-sm text-gray-600">{run?.error_msg || 'Unknown error'}</p>
          <button onClick={() => setStage('input')} className="btn-secondary mt-4">
            Start over
          </button>
        </div>
      </div>
    )
  }

  if (stage === 'hitl') {
    return (
      <div className="max-w-3xl mx-auto p-6 space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-lg font-semibold text-gray-900">Review Content Atoms</h1>
            <p className="text-sm text-gray-500 mt-0.5">
              {atoms.length} atoms extracted — approve, edit, reorder, or add more.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-500">{approvedCount} approved</span>
            <button
              onClick={() => api.bulkApprove(runId!).then(() => refetchAtoms())}
              className="btn-secondary text-xs"
            >
              <CheckSquare size={13} /> Approve all
            </button>
          </div>
        </div>

        {/* Brand voice selector */}
        <div className="card p-4 flex items-center gap-4">
          <label className="label whitespace-nowrap">Brand Voice</label>
          <select
            className="input flex-1"
            value={selectedVoice}
            onChange={(e) => setSelectedVoice(e.target.value)}
          >
            <option value="">Select brand voice...</option>
            {brandVoices.filter((v) => !v.archived).map((v) => (
              <option key={v.slug} value={v.slug}>{v.name}</option>
            ))}
          </select>
        </div>

        {/* Atom list */}
        <DndContext
          sensors={sensors}
          collisionDetection={closestCenter}
          modifiers={[restrictToVerticalAxis]}
          onDragEnd={handleDragEnd}
        >
          <SortableContext items={atoms.map((a) => a.id)} strategy={verticalListSortingStrategy}>
            <div className="space-y-2">
              {atoms.map((atom) => (
                <AtomCard
                  key={atom.id}
                  atom={atom}
                  onUpdate={(updates) => updateAtomMutation.mutate({ atomId: atom.id, updates })}
                  onDelete={() => deleteAtomMutation.mutate(atom.id)}
                />
              ))}
            </div>
          </SortableContext>
        </DndContext>

        {/* Add atom */}
        {addingAtom ? (
          <div className="card p-4 space-y-3">
            <div className="flex gap-3">
              <select className="input w-36" value={newAtomType} onChange={(e) => setNewAtomType(e.target.value)}>
                {['stat', 'insight', 'quote', 'anecdote'].map((t) => (
                  <option key={t} value={t}>{t}</option>
                ))}
              </select>
              <textarea
                className="input flex-1 resize-none"
                placeholder="Atom text..."
                rows={2}
                value={newAtomText}
                onChange={(e) => setNewAtomText(e.target.value)}
              />
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => addAtomMutation.mutate()}
                disabled={!newAtomText.trim()}
                className="btn-primary text-xs"
              >
                Add
              </button>
              <button onClick={() => setAddingAtom(false)} className="btn-ghost text-xs">Cancel</button>
            </div>
          </div>
        ) : (
          <button onClick={() => setAddingAtom(true)} className="btn-ghost text-sm w-full justify-center border border-dashed border-gray-300">
            <Plus size={14} /> Add atom manually
          </button>
        )}

        {/* Generate CTA */}
        <div className="sticky bottom-0 bg-gray-50 border-t border-gray-200 -mx-6 px-6 py-4">
          <button
            onClick={() => startGenerationMutation.mutate()}
            disabled={!canGenerate || startGenerationMutation.isPending}
            className="btn-primary w-full justify-center"
          >
            <Play size={15} />
            {startGenerationMutation.isPending
              ? 'Starting...'
              : `Generate Content (${approvedCount} atom${approvedCount !== 1 ? 's' : ''})`}
          </button>
          {approvedCount === 0 && (
            <p className="text-xs text-center text-amber-600 mt-2">Approve at least one atom to continue</p>
          )}
          {approvedCount > 0 && !selectedVoice && (
            <p className="text-xs text-center text-amber-600 mt-2">Select a brand voice to continue</p>
          )}
        </div>
      </div>
    )
  }

  if (stage === 'generating') {
    return (
      <div className="max-w-2xl mx-auto p-8">
        <GenerationStream
          runId={runId!}
          onComplete={() => {
            setStage('done')
            qc.invalidateQueries({ queryKey: ['outputs', runId] })
          }}
        />
      </div>
    )
  }

  if (stage === 'done') {
    return (
      <div className="max-w-2xl mx-auto p-8 text-center">
        <div className="card p-10">
          <div className="w-12 h-12 rounded-full bg-green-100 flex items-center justify-center mx-auto mb-4">
            <Play size={20} className="text-green-600" />
          </div>
          <h2 className="text-base font-semibold text-gray-900 mb-1">Generation complete</h2>
          <p className="text-sm text-gray-500 mb-6">All platform outputs have been generated and saved.</p>
          <div className="flex gap-3 justify-center">
            <button onClick={() => setActiveTab('outputs')} className="btn-primary">
              View Outputs
            </button>
            <button onClick={() => { setStage('input'); setRunId(null) }} className="btn-secondary">
              New Run
            </button>
          </div>
        </div>
      </div>
    )
  }

  return null
}
