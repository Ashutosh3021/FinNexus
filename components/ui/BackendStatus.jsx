'use client'

import React, { useEffect, useState } from 'react'

export default function BackendStatus() {
  const [status, setStatus] = useState('offline')
  const [dismissed, setDismissed] = useState(false)

  async function check() {
    try {
      const res = await fetch('/api/health')
      const j = await res.json()
      setStatus(j?.status === 'online' ? 'online' : 'offline')
    } catch (e) {
      setStatus('offline')
    }
  }

  useEffect(() => {
    check()
    const id = setInterval(check, 10000)
    return () => clearInterval(id)
  }, [])

  if (status === 'online') {
    return (
      <div className="flex items-center gap-2 text-sm text-green-400">
        <span className="w-2 h-2 rounded-full bg-green-400 inline-block" />
        <span className="hidden sm:inline">Live Data</span>
      </div>
    )
  }

  // Offline: show compact indicator and top dismissible banner
  return (
    <div className="flex flex-col items-end">
      <div className="flex items-center gap-2 text-sm text-amber-400">
        <span className="w-2 h-2 rounded-full bg-amber-400 inline-block" />
        <span className="hidden sm:inline">Demo Mode</span>
      </div>

      {!dismissed && (
        <div className="fixed top-0 left-0 right-0 bg-amber-50 text-amber-900 border-b border-amber-200 z-50 p-2 flex items-center justify-between">
          <div className="text-sm">⚠️ Running in demo mode — backend offline. Data shown is for demonstration only.</div>
          <button onClick={() => setDismissed(true)} className="ml-4 text-sm font-semibold underline">Dismiss</button>
        </div>
      )}
    </div>
  )
}
