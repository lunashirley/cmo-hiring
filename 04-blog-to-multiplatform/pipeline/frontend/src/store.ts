import { create } from 'zustand'

export type TabName = 'pipeline' | 'outputs' | 'ratings' | 'brand-voices' | 'agents' | 'logs' | 'settings'

interface AppStore {
  activeTab: TabName
  setActiveTab: (tab: TabName) => void
  activeRunId: string | null
  setActiveRunId: (id: string | null) => void
  toast: { message: string; type: 'success' | 'error' } | null
  showToast: (message: string, type?: 'success' | 'error') => void
  clearToast: () => void
}

export const useStore = create<AppStore>((set) => ({
  activeTab: 'pipeline',
  setActiveTab: (tab) => set({ activeTab: tab }),
  activeRunId: null,
  setActiveRunId: (id) => set({ activeRunId: id }),
  toast: null,
  showToast: (message, type = 'success') => {
    set({ toast: { message, type } })
    setTimeout(() => set({ toast: null }), 4000)
  },
  clearToast: () => set({ toast: null }),
}))
