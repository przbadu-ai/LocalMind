import { create } from 'zustand'

interface HeaderState {
  title: string
  setTitle: (title: string) => void
  clearTitle: () => void
}

export const useHeaderStore = create<HeaderState>((set) => ({
  title: '',
  setTitle: (title) => set({ title }),
  clearTitle: () => set({ title: '' }),
}))