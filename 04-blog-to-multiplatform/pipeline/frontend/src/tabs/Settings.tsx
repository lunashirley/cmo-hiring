import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Save } from 'lucide-react'
import { api } from '../lib/api'
import { useStore } from '../store'
import { cn } from '../lib/cn'

const OLLAMA_SETTINGS = [
  { key: 'ollama_endpoint', label: 'Ollama Endpoint', type: 'url', help: 'e.g. http://localhost:11434' },
  { key: 'model', label: 'Model', type: 'text', help: 'e.g. deepseek-r1:8b, llama3.1:8b' },
]

const ANTHROPIC_SETTINGS = [
  { key: 'anthropic_api_key', label: 'Anthropic API Key', type: 'password', help: 'sk-ant-... (stored in DB, use env var ANTHROPIC_API_KEY for production)' },
  { key: 'model', label: 'Model', type: 'text', help: 'e.g. claude-sonnet-4-6, claude-opus-4-7, claude-haiku-4-5-20251001' },
]

const GENERAL_SETTING_GROUPS = [
  {
    group: 'Concurrency & Timeouts',
    settings: [
      { key: 'max_concurrency', label: 'Max Concurrency', type: 'number', help: 'Simultaneous model calls' },
      { key: 'per_call_timeout_s', label: 'Per-call Timeout (s)', type: 'number', help: 'Max seconds per LLM call before retry' },
      { key: 'run_timeout_s', label: 'Run Timeout (s)', type: 'number', help: 'Max seconds for a full generation run' },
    ],
  },
  {
    group: 'Atom Extraction',
    settings: [
      { key: 'atom_target_min', label: 'Min Atoms', type: 'number', help: 'Minimum atoms to extract' },
      { key: 'atom_target_max', label: 'Max Atoms', type: 'number', help: 'Maximum atoms to extract' },
    ],
  },
  {
    group: 'Quality & Learning',
    settings: [
      { key: 'qa_max_attempts', label: 'QA Max Attempts', type: 'number', help: 'Max HoC retry attempts before escalation' },
      { key: 'exemplar_pool_size', label: 'Exemplar Pool Size', type: 'number', help: 'Top-N rated outputs kept as exemplars' },
      { key: 'exemplars_injected', label: 'Exemplars Injected', type: 'number', help: 'How many exemplars to inject per generation' },
    ],
  },
]

export default function SettingsTab() {
  const { showToast } = useStore()
  const qc = useQueryClient()
  const [values, setValues] = useState<Record<string, string>>({})
  const [dirty, setDirty] = useState(false)

  const { data: settings } = useQuery({
    queryKey: ['settings'],
    queryFn: api.getSettings,
  })

  useEffect(() => {
    if (settings && Object.keys(values).length === 0) {
      setValues(settings)
    }
  }, [settings])

  const saveMutation = useMutation({
    mutationFn: () => api.updateSettings(values),
    onSuccess: () => {
      showToast('Settings saved')
      setDirty(false)
      qc.invalidateQueries({ queryKey: ['settings'] })
    },
    onError: (err: Error) => showToast(err.message, 'error'),
  })

  const update = (key: string, value: string) => {
    setValues((v) => ({ ...v, [key]: value }))
    setDirty(true)
  }

  const provider = values.provider || 'ollama'
  const inferenceSettings = provider === 'anthropic' ? ANTHROPIC_SETTINGS : OLLAMA_SETTINGS

  return (
    <div className="max-w-2xl mx-auto p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-lg font-semibold text-gray-900">Settings</h1>
        <div className="flex items-center gap-3">
          {dirty && !saveMutation.isPending && (
            <span className="text-xs text-amber-600 font-medium">(unsaved changes)</span>
          )}
          <button
            onClick={() => saveMutation.mutate()}
            disabled={!dirty || saveMutation.isPending}
            className="btn-primary"
          >
            <Save size={14} /> {saveMutation.isPending ? 'Saving...' : 'Save changes'}
          </button>
        </div>
      </div>

      {/* Provider + Inference */}
      <div className="card p-5 space-y-4">
        <h2 className="text-sm font-semibold text-gray-700">Inference Provider</h2>

        <div className="flex gap-2">
          {(['ollama', 'anthropic'] as const).map((p) => (
            <button
              key={p}
              onClick={() => {
                update('provider', p)
                if (p === 'anthropic' && (!values.model || values.model.startsWith('deepseek') || values.model.startsWith('llama') || values.model.startsWith('qwen'))) {
                  update('model', 'claude-sonnet-4-6')
                }
                if (p === 'ollama' && (!values.model || values.model.startsWith('claude'))) {
                  update('model', 'deepseek-r1:8b')
                }
              }}
              className={cn(
                'px-4 py-2 rounded-lg text-sm font-medium border transition-colors',
                provider === p
                  ? 'bg-brand-600 text-white border-brand-600'
                  : 'border-gray-200 text-gray-600 hover:border-brand-300',
              )}
            >
              {p === 'ollama' ? 'Ollama (local)' : 'Anthropic Claude API'}
            </button>
          ))}
        </div>

        {inferenceSettings.map((def) => (
          <div key={def.key}>
            <label className="label block mb-1">{def.label}</label>
            <input
              type={def.type === 'password' ? 'password' : 'text'}
              className="input"
              value={values[def.key] || ''}
              onChange={(e) => update(def.key, e.target.value)}
              autoComplete={def.type === 'password' ? 'off' : undefined}
            />
            <p className="text-xs text-gray-400 mt-1">{def.help}</p>
          </div>
        ))}
      </div>

      {GENERAL_SETTING_GROUPS.map((group) => (
        <div key={group.group} className="card p-5 space-y-4">
          <h2 className="text-sm font-semibold text-gray-700">{group.group}</h2>
          {group.settings.map((def) => (
            <div key={def.key}>
              <label className="label block mb-1">{def.label}</label>
              <input
                type="number"
                className="input"
                value={values[def.key] || ''}
                onChange={(e) => update(def.key, e.target.value)}
              />
              <p className="text-xs text-gray-400 mt-1">{def.help}</p>
            </div>
          ))}
        </div>
      ))}

      <div className="card p-5">
        <h2 className="text-sm font-semibold text-gray-700 mb-1">Authentication</h2>
        <p className="text-xs text-gray-500 mb-3">
          Set the <code className="bg-gray-100 px-1 rounded">PIPELINE_PASSWORD</code> environment variable to change the login password, then restart the backend.
        </p>
        <p className="text-xs text-gray-400">Default: <code className="bg-gray-100 px-1 rounded">admin</code></p>
      </div>
    </div>
  )
}
