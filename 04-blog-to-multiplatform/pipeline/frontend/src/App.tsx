import { useEffect, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { api } from './lib/api'
import { useStore, type TabName } from './store'
import LoginPage from './components/LoginPage'
import PipelineTab from './tabs/Pipeline'
import OutputsTab from './tabs/Outputs'
import RatingsTab from './tabs/Ratings'
import BrandVoicesTab from './tabs/BrandVoices'
import AgentsTab from './tabs/Agents'
import LogsTab from './tabs/Logs'
import SettingsTab from './tabs/Settings'

const TABS: { id: TabName; label: string }[] = [
  { id: 'pipeline', label: 'Pipeline' },
  { id: 'outputs', label: 'Outputs' },
  { id: 'ratings', label: 'Ratings' },
  { id: 'brand-voices', label: 'Brand Voices' },
  { id: 'agents', label: 'Agents' },
  { id: 'logs', label: 'Logs' },
  { id: 'settings', label: 'Settings' },
]

export default function App() {
  const { activeTab, setActiveTab, toast, clearToast } = useStore()

  const { data: user, isLoading, isError } = useQuery({
    queryKey: ['me'],
    queryFn: api.me,
    retry: false,
  })

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-gray-400 text-sm">Loading...</div>
      </div>
    )
  }

  if (isError || !user) {
    return <LoginPage />
  }

  return (
    <div className="min-h-screen flex flex-col">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 px-6 py-3 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-7 h-7 rounded-lg bg-brand-600 flex items-center justify-center">
            <span className="text-white text-xs font-bold">R</span>
          </div>
          <span className="font-semibold text-gray-900 text-sm">Content Repurposing Pipeline</span>
        </div>
        <button
          onClick={() => api.logout().then(() => window.location.reload())}
          className="text-xs text-gray-400 hover:text-gray-600 transition-colors"
        >
          Sign out
        </button>
      </header>

      {/* Tab nav */}
      <nav className="bg-white border-b border-gray-200 px-6">
        <div className="flex gap-1">
          {TABS.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
                activeTab === tab.id
                  ? 'border-brand-600 text-brand-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </nav>

      {/* Content */}
      <main className="flex-1 overflow-auto">
        {activeTab === 'pipeline' && <PipelineTab />}
        {activeTab === 'outputs' && <OutputsTab />}
        {activeTab === 'ratings' && <RatingsTab />}
        {activeTab === 'brand-voices' && <BrandVoicesTab />}
        {activeTab === 'agents' && <AgentsTab />}
        {activeTab === 'logs' && <LogsTab />}
        {activeTab === 'settings' && <SettingsTab />}
      </main>

      {/* Toast */}
      {toast && (
        <div
          className={`fixed bottom-6 right-6 px-4 py-3 rounded-lg shadow-lg text-sm font-medium text-white z-50 transition-all ${
            toast.type === 'error' ? 'bg-red-600' : 'bg-green-600'
          }`}
          onClick={clearToast}
        >
          {toast.message}
        </div>
      )}
    </div>
  )
}
