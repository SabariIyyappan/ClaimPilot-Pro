import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { Entity, CodeSuggestion } from '@/lib/types';

interface ClaimState {
  text: string;
  entities: Entity[];
  suggestions: CodeSuggestion[];
  approved: CodeSuggestion[];
  amount: number;
  signedBy: string;
  
  setText: (text: string) => void;
  setEntities: (entities: Entity[]) => void;
  setSuggestions: (suggestions: CodeSuggestion[]) => void;
  setApproved: (approved: CodeSuggestion[]) => void;
  toggleApproved: (suggestion: CodeSuggestion) => void;
  removeApproved: (code: string) => void;
  addApproved: (suggestion: CodeSuggestion) => void;
  updateApproved: (code: string, updates: Partial<CodeSuggestion>) => void;
  setAmount: (amount: number) => void;
  setSignedBy: (signedBy: string) => void;
  reset: () => void;
}

const initialState = {
  text: '',
  entities: [],
  suggestions: [],
  approved: [],
  amount: 0,
  signedBy: '',
};

export const useClaimStore = create<ClaimState>()(
  persist(
    (set) => ({
      ...initialState,
      
      setText: (text) => set({ text }),
      setEntities: (entities) => set({ entities }),
      setSuggestions: (suggestions) => set({ suggestions }),
      setApproved: (approved) => set({ approved }),
      
      toggleApproved: (suggestion) =>
        set((state) => {
          const exists = state.approved.find((a) => a.code === suggestion.code);
          if (exists) {
            return { approved: state.approved.filter((a) => a.code !== suggestion.code) };
          }
          return { approved: [...state.approved, suggestion] };
        }),
      
      removeApproved: (code) =>
        set((state) => ({
          approved: state.approved.filter((a) => a.code !== code),
        })),
      
      addApproved: (suggestion) =>
        set((state) => ({ approved: [...state.approved, suggestion] })),
      
      updateApproved: (code, updates) =>
        set((state) => ({
          approved: state.approved.map((a) =>
            a.code === code ? { ...a, ...updates } : a
          ),
        })),
      
      setAmount: (amount) => set({ amount }),
      setSignedBy: (signedBy) => set({ signedBy }),
      reset: () => set(initialState),
    }),
    {
      name: 'claim-storage',
      partialize: (state) => ({
        text: state.text,
        entities: state.entities,
        suggestions: state.suggestions,
        approved: state.approved,
        amount: state.amount,
        signedBy: state.signedBy,
      }),
    }
  )
);
