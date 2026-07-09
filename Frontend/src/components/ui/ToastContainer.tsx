/**
 * ToastContainer — renders toast notifications at the bottom-right of the screen.
 * Mount once in App.tsx (outside the router) so toasts survive route transitions.
 */
import { useToastStore } from '../../hooks/useToast'
import { cn } from '../../lib/utils'
import { CheckCircle2, AlertCircle, Info, X } from 'lucide-react'

const ICONS = {
  success: <CheckCircle2 size={15} className="text-primary shrink-0" />,
  error:   <AlertCircle  size={15} className="text-error   shrink-0" />,
  info:    <Info         size={15} className="text-secondary shrink-0" />,
}

const BORDER_COLORS = {
  success: 'border-primary/30',
  error:   'border-error/30',
  info:    'border-outline-variant/30',
}

export function ToastContainer() {
  const { toasts, dismiss } = useToastStore()

  if (toasts.length === 0) return null

  return (
    <div
      className="fixed bottom-4 right-4 z-[999] flex flex-col gap-2 max-w-sm w-full pointer-events-none"
      aria-live="polite"
      aria-label="Notifications"
    >
      {toasts.map((t) => (
        <div
          key={t.id}
          role="alert"
          className={cn(
            'flex items-start gap-3 bg-surface-container-low rounded-xl border px-4 py-3',
            'shadow-[0_4px_24px_rgba(0,0,0,0.4)] backdrop-blur-sm',
            'pointer-events-auto',
            BORDER_COLORS[t.variant],
          )}
        >
          {ICONS[t.variant]}
          <p className="flex-1 text-xs font-headline text-on-surface leading-relaxed">
            {t.message}
          </p>
          <button
            onClick={() => dismiss(t.id)}
            className="text-on-surface-variant hover:text-on-surface transition-colors mt-0.5"
            aria-label="Dismiss notification"
          >
            <X size={13} />
          </button>
        </div>
      ))}
    </div>
  )
}
