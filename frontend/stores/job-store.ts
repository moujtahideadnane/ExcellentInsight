import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface JobState {
  activeJobId: string | null
  setActiveJobId: (id: string | null) => void
  clearActiveJob: () => void
}

export const useJobStore = create<JobState>()(
  persist(
    (set) => ({
      activeJobId: null,
      setActiveJobId: (id) => set({ activeJobId: id }),
      clearActiveJob: () => set({ activeJobId: null }),
    }),
    {
      name: 'excellent-insight-job-storage',
      skipHydration: true,
    }
  )
)
