import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, Save, ChevronRight } from 'lucide-react'
import { api, type BrandVoiceMeta, type BrandVoiceFull } from '../lib/api'
import { useStore } from '../store'
import { cn } from '../lib/cn'

const DEFAULT_TEMPLATE = `---
name: "New Voice"
slug: "new-voice"
created: "${new Date().toISOString().split('T')[0]}"
version: 1
---

## Tone descriptors
[Describe the overall tone: e.g. Direct, warm, commercial, no corporate filler.]

## Vocabulary — do
- [Words and phrases that fit this voice]

## Vocabulary — don't
- [Words and phrases to avoid]

## Sentence preferences
- [Sentence length and rhythm guidelines]

## CTA patterns
- [How to close content — direct question, single action, etc.]

## Reference examples
- [Paste 2-3 example sentences that capture this voice]
`

export default function BrandVoicesTab() {
  const { showToast } = useStore()
  const qc = useQueryClient()

  const [selected, setSelected] = useState<string | null>(null)
  const [creating, setCreating] = useState(false)
  const [newSlug, setNewSlug] = useState('')
  const [editContent, setEditContent] = useState('')

  const { data: voices = [] } = useQuery<BrandVoiceMeta[]>({
    queryKey: ['brand-voices'],
    queryFn: api.listBrandVoices,
  })

  const { data: full } = useQuery<BrandVoiceFull>({
    queryKey: ['brand-voice', selected],
    queryFn: () => api.getBrandVoice(selected!),
    enabled: !!selected,
  })

  useEffect(() => {
    if (full && !creating) setEditContent(full.content)
  }, [full?.slug])

  const saveMutation = useMutation({
    mutationFn: () =>
      creating
        ? api.createBrandVoice(newSlug, editContent)
        : api.updateBrandVoice(selected!, editContent),
    onSuccess: () => {
      showToast('Brand voice saved')
      qc.invalidateQueries({ queryKey: ['brand-voices'] })
      if (creating) {
        setSelected(newSlug)
        setCreating(false)
        setNewSlug('')
      } else {
        qc.invalidateQueries({ queryKey: ['brand-voice', selected] })
      }
    },
    onError: (err: Error) => showToast(err.message, 'error'),
  })

  const startCreate = () => {
    setCreating(true)
    setSelected(null)
    setEditContent(DEFAULT_TEMPLATE)
  }

  return (
    <div className="flex h-[calc(100vh-112px)]">
      {/* Sidebar */}
      <div className="w-56 border-r border-gray-200 bg-white flex flex-col">
        <div className="p-3 border-b border-gray-100">
          <button onClick={startCreate} className="btn-primary w-full justify-center text-xs">
            <Plus size={13} /> New Voice
          </button>
        </div>
        <div className="flex-1 overflow-y-auto py-2">
          {voices.map((v) => (
            <button
              key={v.slug}
              onClick={() => { setSelected(v.slug); setCreating(false) }}
              className={cn(
                'w-full text-left px-3 py-2.5 flex items-center justify-between group hover:bg-gray-50 transition-colors',
                selected === v.slug && !creating && 'bg-brand-50',
              )}
            >
              <div>
                <div className={cn('text-sm font-medium', selected === v.slug && !creating ? 'text-brand-700' : 'text-gray-700')}>
                  {v.name}
                </div>
                <div className="text-xs text-gray-400">v{v.version}</div>
              </div>
              <ChevronRight size={14} className="text-gray-300 group-hover:text-gray-400" />
            </button>
          ))}
        </div>
      </div>

      {/* Editor */}
      <div className="flex-1 flex flex-col">
        {creating || selected ? (
          <>
            <div className="px-6 py-3 border-b border-gray-200 flex items-center justify-between bg-white">
              <div>
                {creating ? (
                  <div className="flex items-center gap-2">
                    <span className="text-sm text-gray-500">Slug:</span>
                    <input
                      className="input text-sm py-1 w-40"
                      placeholder="my-voice-slug"
                      value={newSlug}
                      onChange={(e) => setNewSlug(e.target.value.toLowerCase().replace(/\s+/g, '-'))}
                    />
                  </div>
                ) : (
                  <span className="text-sm font-medium text-gray-700">{full?.name}</span>
                )}
              </div>
              <button
                onClick={() => saveMutation.mutate()}
                disabled={saveMutation.isPending || (creating && !newSlug)}
                className="btn-primary text-xs"
              >
                <Save size={13} /> {saveMutation.isPending ? 'Saving...' : 'Save'}
              </button>
            </div>
            <textarea
              className="flex-1 font-mono text-sm p-6 resize-none focus:outline-none focus:ring-2 focus:ring-brand-500 focus:ring-inset bg-white"
              value={editContent}
              onChange={(e) => setEditContent(e.target.value)}
              spellCheck={false}
            />
          </>
        ) : (
          <div className="flex-1 flex items-center justify-center text-sm text-gray-400">
            Select a brand voice or create a new one
          </div>
        )}
      </div>
    </div>
  )
}
