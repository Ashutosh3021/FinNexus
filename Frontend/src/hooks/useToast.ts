/**
 * Lightweight toast notification hook.
 * Usage:
 *   const { toast } = useToast()
 *   toast('Something went wrong', 'error')
 *   toast('Saved!', 'success')
 */
import { create } from 'zustand'

export type ToastVariant = 'success' | 'error' | 'info'

export interface ToastMessage {
  id: string
  message: string
  variant: ToastVariant
}

interface ToastState {
  toasts: ToastMessage[]
  push: (message: string, variant?: ToastVariant) => void
  dismiss: (id: string) => void
}

export const useToastStore = create<ToastState>((set) => ({
  toasts: [],
  push: (message, variant = 'info') => {
    const id = `toast-${Date.now()}-${Math.random().toString(36).slice(2)}`
    set((s) => ({ toasts: [...s.toasts, { id, message, variant }] }))
    // Auto-dismiss after 4 seconds
    setTimeout(() => {
      set((s) => ({ toasts: s.toasts.filter((t) => t.id !== id) }))
    }, 4000)
  },
  dismiss: (id) => set((s) => ({ toasts: s.toasts.filter((t) => t.id !== id) })),
}))

/** Convenience hook — returns a `toast(message, variant?)` function. */
export function useToast() {
  const push = useToastStore((s) => s.push)
  return { toast: push }
}
