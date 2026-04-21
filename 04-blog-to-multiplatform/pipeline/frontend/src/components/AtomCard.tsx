import { useState } from 'react'
import { useSortable } from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'
import { GripVertical, Pencil, Trash2, Check, X, RotateCcw } from 'lucide-react'
import { cn } from '../lib/cn'
import type { Atom } from '../lib/api'

const TYPE_COLORS: Record<string, string> = {
  stat: 'bg-blue-50 text-blue-700 border-blue-200',
  insight: 'bg-purple-50 text-purple-700 border-purple-200',
  quote: 'bg-amber-50 text-amber-700 border-amber-200',
  anecdote: 'bg-green-50 text-green-700 border-green-200',
}

const ATOM_TYPES = ['stat', 'insight', 'quote', 'anecdote'] as const

interface Props {
  atom: Atom
  onUpdate: (updates: Partial<Atom>) => void
  onDelete: () => void
}

export default function AtomCard({ atom, onUpdate, onDelete }: Props) {
  const [editing, setEditing] = useState(false)
  const [editText, setEditText] = useState(atom.text)
  const [showUndo, setShowUndo] = useState(false)
  const [confirmDelete, setConfirmDelete] = useState(false)

  const { attributes, listeners, setNodeRef, transform, transition, isDragging } =
    useSortable({ id: atom.id })

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  }

  const saveEdit = () => {
    if (editText.trim() !== atom.original_text) {
      onUpdate({ text: editText.trim() })
      setShowUndo(true)
    }
    setEditing(false)
  }

  const cancelEdit = () => {
    setEditText(atom.text)
    setEditing(false)
  }

  const undoEdit = () => {
    onUpdate({ text: atom.original_text })
    setEditText(atom.original_text)
    setShowUndo(false)
  }

  return (
    <div
      ref={setNodeRef}
      style={style}
      className={cn(
        'card p-4 flex gap-3 group',
        atom.approved && 'ring-2 ring-brand-500 ring-offset-1',
        isDragging && 'shadow-xl',
      )}
    >
      {/* Drag handle */}
      <button
        {...attributes}
        {...listeners}
        className="mt-1 text-gray-300 hover:text-gray-500 cursor-grab active:cursor-grabbing flex-shrink-0"
      >
        <GripVertical size={16} />
      </button>

      {/* Body */}
      <div className="flex-1 min-w-0">
        <div className="flex items-start gap-2 mb-2">
          {/* Type selector */}
          <select
            value={atom.type}
            onChange={(e) => onUpdate({ type: e.target.value as Atom['type'] })}
            className={cn(
              'badge border text-xs font-medium cursor-pointer appearance-none px-2 py-0.5 rounded-md',
              TYPE_COLORS[atom.type],
            )}
          >
            {ATOM_TYPES.map((t) => (
              <option key={t} value={t}>{t}</option>
            ))}
          </select>

          {/* Confidence */}
          {atom.origin === 'extracted' && (
            <span className="text-xs text-gray-400 tabular-nums">
              {Math.round(atom.confidence * 100)}%
            </span>
          )}

          {atom.is_edited && (
            <span className="text-xs text-amber-600 font-medium">edited</span>
          )}

          {atom.origin === 'manual' && (
            <span className="text-xs text-gray-400">manual</span>
          )}
        </div>

        {/* Text */}
        {editing ? (
          <div className="space-y-2">
            <textarea
              autoFocus
              value={editText}
              onChange={(e) => setEditText(e.target.value)}
              className="input text-sm resize-none"
              rows={3}
            />
            <div className="flex gap-2">
              <button onClick={saveEdit} className="btn-primary py-1 text-xs">
                <Check size={12} /> Save
              </button>
              <button onClick={cancelEdit} className="btn-secondary py-1 text-xs">
                <X size={12} /> Cancel
              </button>
            </div>
          </div>
        ) : (
          <p className="text-sm text-gray-800 leading-relaxed">{atom.text}</p>
        )}

        {/* Proposed angle */}
        {atom.proposed_angle && !editing && (
          <p className="text-xs text-gray-400 mt-1.5 italic">{atom.proposed_angle}</p>
        )}
      </div>

      {/* Actions */}
      <div className="flex-shrink-0 flex flex-col items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
        <button
          onClick={() => onUpdate({ approved: !atom.approved })}
          title={atom.approved ? 'Unapprove' : 'Approve'}
          className={cn(
            'w-7 h-7 rounded-lg flex items-center justify-center text-xs transition-colors',
            atom.approved
              ? 'bg-brand-600 text-white'
              : 'border border-gray-200 text-gray-400 hover:border-brand-500 hover:text-brand-600',
          )}
        >
          <Check size={12} />
        </button>
        {!editing && (
          <button
            onClick={() => { setEditText(atom.text); setEditing(true) }}
            className="w-7 h-7 rounded-lg border border-gray-200 flex items-center justify-center text-gray-400 hover:text-gray-600 transition-colors"
          >
            <Pencil size={12} />
          </button>
        )}
        {showUndo && atom.is_edited && (
          <button
            onClick={undoEdit}
            title="Restore original"
            className="w-7 h-7 rounded-lg border border-gray-200 flex items-center justify-center text-amber-500 hover:text-amber-700 transition-colors"
          >
            <RotateCcw size={12} />
          </button>
        )}
        {confirmDelete ? (
          <div className="flex flex-col items-center gap-1">
            <button
              onClick={() => { onDelete(); setConfirmDelete(false) }}
              className="text-xs text-red-600 font-medium hover:text-red-800 whitespace-nowrap"
            >
              Confirm
            </button>
            <button
              onClick={() => setConfirmDelete(false)}
              className="text-xs text-gray-400 hover:text-gray-600 whitespace-nowrap"
            >
              Cancel
            </button>
          </div>
        ) : (
          <button
            onClick={() => setConfirmDelete(true)}
            className="w-7 h-7 rounded-lg border border-gray-200 flex items-center justify-center text-gray-400 hover:text-red-600 hover:border-red-200 transition-colors"
          >
            <Trash2 size={12} />
          </button>
        )}
      </div>
    </div>
  )
}
