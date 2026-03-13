"use client"

import React, { useEffect, useState } from 'react'
import api, { getErrorMessage } from '@/lib/api'
import { Key, Plus, Loader2, Copy, Check, Trash2, Server } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import { toast } from 'sonner'
import { SectionHeader } from './SectionHeader'

interface ApiKeyData {
  id: string
  label: string
  key_prefix: string
  is_active: boolean
  created_at: string
  expires_at: string | null
  last_used_at: string | null
}

interface NewKeyData extends ApiKeyData {
  key: string
}

export function ApiKeysSection() {
  const [keys, setKeys] = useState<ApiKeyData[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [newLabel, setNewLabel] = useState('')
  const [expiryDays, setExpiryDays] = useState<string>('never')
  const [isCreating, setIsCreating] = useState(false)
  const [revealedKey, setRevealedKey] = useState<NewKeyData | null>(null)
  const [copiedId, setCopiedId] = useState<string | null>(null)
  const [showCreateForm, setShowCreateForm] = useState(false)

  useEffect(() => {
    async function load() {
      try {
        const res = await api.get('/settings/api-keys')
        setKeys(res.data)
      } catch (err) {
        toast.error(getErrorMessage(err))
      } finally {
        setIsLoading(false)
      }
    }
    load()
  }, [])

  const handleCreate = async () => {
    if (!newLabel.trim()) { toast.error('Identify alias required'); return }
    setIsCreating(true)
    try {
      const payload: { label: string; expires_in_days?: number } = { label: newLabel.trim() }
      if (expiryDays !== 'never') payload.expires_in_days = parseInt(expiryDays)
      const res = await api.post('/settings/api-keys', payload)
      setRevealedKey(res.data)
      setKeys(prev => [res.data, ...prev])
      setNewLabel('')
      setExpiryDays('never')
      setShowCreateForm(false)
      toast.success('Token generated')
    } catch (err) {
      toast.error(getErrorMessage(err))
    } finally {
      setIsCreating(false)
    }
  }

  const handleRevoke = async (keyId: string) => {
    try {
      await api.delete(`/settings/api-keys/${keyId}`)
      setKeys(prev => prev.filter(k => k.id !== keyId))
      if (revealedKey?.id === keyId) setRevealedKey(null)
      toast.success('Token revoked')
    } catch (err) {
      toast.error(getErrorMessage(err))
    }
  }

  const handleCopy = (text: string, id: string) => {
    try {
      navigator.clipboard.writeText(text)
      setCopiedId(id)
      setTimeout(() => setCopiedId(null), 2000)
      toast.success('Buffer appended')
    } catch {
      toast.error('Failed to copy to clipboard')
    }
  }

  if (isLoading) return <div className="flex items-center justify-center py-20"><Loader2 className="h-6 w-6 animate-spin text-ve-blue" /></div> // REFACTOR: [consolidate-hex]

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <SectionHeader title="Access Tokens" subtitle="Machine identities for programmatic system integration." />
        {!showCreateForm && (
          <button onClick={() => setShowCreateForm(true)} className="flex items-center gap-2 rounded-[4px] bg-ve-btn-primary text-ve-btn-text px-4 py-1.5 font-medium text-[12px] hover:bg-ve-btn-hover transition-colors shrink-0">
            <Plus className="h-3.5 w-3.5" /> Initialize Token
          </button>
        )}
      </div>

      <AnimatePresence>
        {revealedKey && (
          <motion.div
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            className="rounded-[4px] border border-ve-blue bg-ve-bg p-6"
          >
             <div className="flex items-center gap-3 mb-4">
               <div className="h-8 w-8 rounded-[4px] bg-ve-blue-muted flex items-center justify-center shrink-0">
                 <Key className="h-4 w-4 text-ve-blue" />
               </div>
               <div>
                  <span className="text-[13px] font-medium text-ve-text block tracking-tight">Access token generated</span>
                  <p className="text-[11px] font-mono text-ve-muted mt-0.5">This secret is shown once. Store it securely in your local environment.</p>
               </div>
             </div>
             
             <div className="flex items-center gap-2 bg-ve-surface rounded-[4px] border border-ve-border px-4 py-3">
               <code className="flex-1 text-[13px] text-ve-text font-mono break-all selection:bg-blue-500/30">{revealedKey.key}</code>
               <button onClick={() => handleCopy(revealedKey.key, revealedKey.id)} className="shrink-0 p-2 rounded-[4px] hover:bg-ve-border-subtle border border-transparent hover:border-ve-border transition-colors">
                  {copiedId === revealedKey.id ? <Check className="h-4 w-4 text-ve-blue" /> : <Copy className="h-4 w-4 text-ve-muted" />}
               </button>
             </div>
             <button onClick={() => setRevealedKey(null)} className="mt-4 text-[9px] font-mono uppercase tracking-widest text-ve-muted hover:text-ve-text transition-colors">
               [ Dismiss Alert ]
             </button>
          </motion.div>
        )}
      </AnimatePresence>

      <AnimatePresence>
        {showCreateForm && (
          <motion.div initial={{ opacity: 0, y: -8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -8 }} className="bg-ve-bg border border-ve-border rounded-[4px] p-6 space-y-5">
            <div className="text-[14px] font-medium text-ve-text tracking-tight">Initialize Configuration</div>
            
            <div className="space-y-2">
               <label className="text-[10px] font-mono uppercase tracking-widest text-ve-muted">Alias</label>
               <input
                 className="h-10 w-full bg-ve-surface border border-ve-border rounded-[4px] px-3 text-[13px] text-ve-text font-mono outline-none focus:border-ve-muted transition-colors"
                 placeholder="Terminal process identifier"
                 value={newLabel}
                 onChange={(e) => setNewLabel(e.target.value)}
                 maxLength={80}
               />
            </div>
            
            <div className="space-y-2">
               <label className="text-[10px] font-mono uppercase tracking-widest text-ve-muted">Validity Window</label>
               <select
                 className="h-10 w-full bg-ve-surface border border-ve-border rounded-[4px] px-3 text-[13px] text-ve-text font-mono outline-none focus:border-ve-muted transition-colors appearance-none"
                 value={expiryDays}
                 onChange={(e) => setExpiryDays(e.target.value)}
               >
                 <option value="never">Infinite duration</option>
                 <option value="30">30 cycles (days)</option>
                 <option value="90">90 cycles (days)</option>
                 <option value="365">365 cycles (days)</option>
               </select>
            </div>
            
            <div className="flex items-center gap-4 pt-4 border-t border-ve-border">
               <button onClick={handleCreate} disabled={isCreating || !newLabel.trim()} className="flex items-center gap-2 rounded-[4px] bg-ve-btn-primary text-ve-btn-text px-4 py-2 font-medium text-[13px] hover:bg-ve-btn-hover transition-colors disabled:opacity-50">
                 {isCreating ? <Loader2 className="h-4 w-4 animate-spin" /> : <Key className="h-4 w-4" />}
                 {isCreating ? 'Compiling...' : 'Generate Resource'}
               </button>
               <button onClick={() => setShowCreateForm(false)} className="text-[11px] font-mono uppercase tracking-widest text-ve-muted hover:text-ve-text transition-colors">Abort</button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      <div className="space-y-3">
        {keys.length === 0 ? (
          <div className="border border-dashed border-ve-border rounded-[4px] py-20 text-center bg-ve-surface">
            <Server className="h-8 w-8 mx-auto mb-4 text-ve-border" />
            <p className="text-[11px] font-mono text-ve-muted uppercase tracking-widest">Null Output Array</p>
            <p className="text-[12px] font-mono text-ve-dimmed mt-2">Initialize access tokens for automated systems integration.</p>
          </div>
        ) : (
          keys.map((k) => (
            <div key={k.id} className="bg-ve-bg border border-ve-border rounded-[4px] px-6 py-5 flex items-start sm:items-center justify-between gap-4 flex-col sm:flex-row hover:border-ve-muted transition-colors">
              
              <div className="flex items-center gap-4 flex-1 min-w-0">
                 <div className="h-10 w-10 rounded-[4px] bg-ve-surface border border-ve-border flex items-center justify-center shrink-0">
                   <Key className="h-4 w-4 text-ve-muted" />
                 </div>
                 <div className="min-w-0">
                    <div className="flex items-center gap-3 mb-1.5">
                       <span className="text-[14px] font-semibold text-ve-text truncate tracking-tight">{k.label}</span>
                       {k.is_active ? (
                         <span className="px-1.5 py-0.5 rounded-[2px] bg-ve-surface border border-ve-border text-ve-text text-[9px] font-mono uppercase tracking-widest">Active</span>
                       ) : (
                         <span className="px-1.5 py-0.5 rounded-[2px] bg-ve-error-bg border border-ve-error-border text-ve-error text-[9px] font-mono uppercase tracking-widest">Revoked</span>
                       )}
                    </div>
                    <div className="flex items-center gap-3 flex-wrap text-[10px] font-mono text-ve-muted uppercase tracking-wider">
                       <span className="text-ve-text">{k.key_prefix}••••••••</span>
                       <span className="hidden sm:inline-block h-3 w-px bg-ve-border" />
                       <span>{new Date(k.created_at).toLocaleDateString()}</span>
                       {k.expires_at && (
                         <>
                           <span className="hidden sm:inline-block h-3 w-px bg-ve-border" />
                           <span className="text-ve-error">T-{new Date(k.expires_at).toLocaleDateString()}</span>
                         </>
                       )}
                       {k.last_used_at && (
                         <>
                           <span className="hidden sm:inline-block h-3 w-px bg-ve-border" />
                           <span className="text-ve-blue">Ping: {new Date(k.last_used_at).toLocaleDateString()}</span>
                         </>
                       )}
                    </div>
                 </div>
              </div>
              
              <button
                 onClick={() => handleRevoke(k.id)}
                 className="h-8 w-8 rounded-[4px] flex items-center justify-center text-ve-muted hover:text-ve-error border border-transparent hover:border-ve-error hover:bg-ve-error-bg transition-all shrink-0"
                 title="Force Revoke"
              >
                 <Trash2 className="h-3.5 w-3.5" />
              </button>
            </div>
          ))
        )}
      </div>
    </div>
  )
}
