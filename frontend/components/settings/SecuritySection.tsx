"use client"

import React, { useState } from 'react'
import api, { getErrorMessage } from '@/lib/api'
import { Eye, EyeOff, Loader2, Shield, AlertTriangle } from 'lucide-react'
import { toast } from 'sonner'
import { cn } from '@/lib/utils'
import { SectionHeader } from './SectionHeader'

export function SecuritySection() {
  const [current, setCurrent] = useState('')
  const [next, setNext] = useState('')
  const [confirm, setConfirm] = useState('')
  const [showCurrent, setShowCurrent] = useState(false)
  const [showNext, setShowNext] = useState(false)
  const [isSaving, setIsSaving] = useState(false)

  const strength = (() => {
    if (!next) return 0
    let s = 0
    if (next.length >= 8)  s++
    if (next.length >= 12) s++
    if (/[A-Z]/.test(next)) s++
    if (/[0-9]/.test(next)) s++
    if (/[^A-Za-z0-9]/.test(next)) s++
    return s
  })()

  const strengthLabel = ['', 'CRITICAL', 'WEAK', 'MODERATE', 'ACCEPTABLE', 'SECURE'][strength]
  const strengthColor = ['', 'bg-ve-error', 'bg-ve-warning', 'bg-ve-warning', 'bg-ve-text', 'bg-ve-blue'][strength] // REFACTOR: [consolidate-hex]

  const handleChange = async () => {
    if (next !== confirm) { toast.error('Hashes do not match'); return }
    if (next.length < 8) { toast.error('Minimum length: 8 bytes'); return }
    setIsSaving(true)
    try {
      await api.post('/settings/change-password', { current_password: current, new_password: next })
      toast.success('Access credentials updated')
      setCurrent(''); setNext(''); setConfirm('')
    } catch (err) {
      toast.error(getErrorMessage(err))
    } finally {
      setIsSaving(false)
    }
  }

  return (
    <div className="space-y-6">
      <SectionHeader title="Access Security" subtitle="Manage your access control list and cryptographic proofs." />
      <div className="bg-ve-bg border border-ve-border rounded-[4px] p-6 lg:p-8 space-y-6">
        <div className="space-y-2">
          <label className="text-[10px] font-mono uppercase tracking-widest text-ve-muted">Current Hash</label>
          <div className="relative">
            <input
              type={showCurrent ? 'text' : 'password'}
              className="h-10 w-full bg-ve-surface border border-ve-border rounded-[4px] px-3 pr-10 text-[13px] text-ve-text font-mono outline-none focus:border-ve-muted transition-colors"
              value={current}
              onChange={(e) => setCurrent(e.target.value)}
              placeholder="••••••••"
            />
            <button type="button" onClick={() => setShowCurrent(v => !v)} className="absolute right-3 top-1/2 -translate-y-1/2 text-ve-muted hover:text-ve-text">
              {showCurrent ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
            </button>
          </div>
        </div>

        <div className="space-y-2">
          <label className="text-[10px] font-mono uppercase tracking-widest text-ve-muted">New Hash Directive</label>
          <div className="relative">
             <input
              type={showNext ? 'text' : 'password'}
              className="h-10 w-full bg-ve-surface border border-ve-border rounded-[4px] px-3 pr-10 text-[13px] text-ve-text font-mono outline-none focus:border-ve-muted transition-colors"
              value={next}
              onChange={(e) => setNext(e.target.value)}
              placeholder="Minimum 8 bytes"
            />
            <button type="button" onClick={() => setShowNext(v => !v)} className="absolute right-3 top-1/2 -translate-y-1/2 text-ve-muted hover:text-ve-text">
              {showNext ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
            </button>
          </div>
          {next && (
            <div className="space-y-1.5 pt-2">
              <div className="flex gap-1 h-0.5">
                {[1,2,3,4,5].map(i => (
                  <div key={i} className={cn("flex-1 transition-colors duration-300", i <= strength ? strengthColor : 'bg-ve-border')} />
                ))}
              </div>
              <p className="text-[9px] font-mono text-ve-muted uppercase tracking-widest">Entropy Level: {strengthLabel}</p>
            </div>
          )}
        </div>

        <div className="space-y-2">
          <label className="text-[10px] font-mono uppercase tracking-widest text-ve-muted">Verify New Directive</label>
          <input
            type="password"
            className={cn("h-10 w-full bg-ve-surface border rounded-[4px] px-3 pr-10 text-[13px] text-ve-text font-mono outline-none transition-colors", confirm && next !== confirm ? "border-ve-error" : "border-ve-border focus:border-ve-muted")}
            value={confirm}
            onChange={(e) => setConfirm(e.target.value)}
            placeholder="Re-enter configuration"
          />
          {confirm && next !== confirm && (
            <p className="text-[9px] font-mono text-ve-error uppercase tracking-widest flex items-center gap-1.5 mt-2">
              <AlertTriangle className="h-3 w-3" /> Integrity mismatch
            </p>
          )}
        </div>

        <div className="pt-4 flex justify-end border-t border-ve-border">
          <button
             onClick={handleChange}
             disabled={isSaving || !current || !next || !confirm}
             className="flex items-center gap-2 px-6 py-2 rounded-[4px] bg-ve-btn-primary text-ve-btn-text font-medium text-[13px] disabled:opacity-50 hover:bg-ve-btn-hover transition-colors"
          >
             {isSaving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Shield className="h-4 w-4" />}
             {isSaving ? 'Encrypting...' : 'Update Proof'}
          </button>
        </div>
      </div>
    </div>
  )
}
