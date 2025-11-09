import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { ClaimRecord } from '@/lib/types';

interface ClaimsState {
  items: ClaimRecord[];
  add: (rec: ClaimRecord) => void;
  clear: () => void;
}

export const useClaimsStore = create<ClaimsState>()(
  persist(
    (set) => ({
      items: [],
      add: (rec) =>
        set((state) => ({ items: [rec, ...state.items].slice(0, 200) })),
      clear: () => set({ items: [] }),
    }),
    {
      name: 'claims-history',
    }
  )
);

