"use client"

import React, { useEffect, useState } from 'react'
import { useAuthStore } from '@/stores/auth-store'
import api, { getErrorMessage } from '@/lib/api'
import {
  User, Bell, Shield, Key, LogOut, Save, Loader2,
  Eye, EyeOff, Plus, Trash2, Copy, Check, AlertTriangle,
  Building2, Crown, Server
} from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import { toast } from 'sonner'
import { cn } from '@/lib/utils'

const SECTIONS = [
  { id: 'account',       label: 'Identity',       icon: User },
  { id: 'security',      label: 'Security',       icon: Shield },
  { id: 'api',           label: 'Tokens',         icon: Key },
  { id: 'notifications', label: 'Telemetry',      icon: Bell },
]

interface Profile {
  id: string
  email: string
  display_name: string | null
  role: string
  org_name: string
  org_plan: string
  created_at: string
}

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

function SectionHeader({ title, subtitle }: { title: string; subtitle: string }) {
  return (
    <div className="mb-8 border-b border-[#333333] pb-6">
      <h2 className="text-[20px] font-semibold tracking-tight text-[#EDEDED]">{title}</h2>
      <p className="text-[12px] font-mono text-[#888888] mt-2">{subtitle}</p>
    </div>
  )
}

// ── Account Section ────────────────────────────────────────────────────────────
function AccountSection() {
  const { user: storeUser, setAuth, logout } = useAuthStore()
  const [profile, setProfile] = useState<Profile | null>(null)
  const [displayName, setDisplayName] = useState('')
  const [isSaving, setIsSaving] = useState(false)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    async function load() {
      try {
        const res = await api.get('/settings/profile')
        setProfile(res.data)
        setDisplayName(res.data.display_name || res.data.email.split('@')[0])
      } catch {
        // fallback to store
        setDisplayName(storeUser?.display_name || storeUser?.email?.split('@')[0] || '')
      } finally {
        setIsLoading(false)
      }
    }
    load()
  }, [storeUser])

  const handleSave = async () => {
    setIsSaving(true)
    try {
      const res = await api.patch('/settings/profile', { display_name: displayName })
      setProfile(res.data)
      if (storeUser) {
        const tokens = useAuthStore.getState()
        setAuth({ ...storeUser, display_name: res.data.display_name }, tokens.accessToken || '', tokens.refreshToken || '')
      }
      toast.success('Identity profile updated')
    } catch (err) {
      toast.error(getErrorMessage(err))
    } finally {
      setIsSaving(false)
    }
  }

  if (isLoading) return <div className="flex items-center justify-center py-20"><Loader2 className="h-6 w-6 animate-spin text-[#0070F3]" /></div>

  const initial = (displayName || profile?.email || '?').charAt(0).toUpperCase()

  return (
    <div className="space-y-6">
      <SectionHeader title="System Identity" subtitle="Manage your primary authentication identity within the environment." />

      <div className="bg-[#000000] border border-[#333333] rounded-[4px] p-6 lg:p-8">
        <div className="flex items-center gap-6 mb-8">
          <div className="h-16 w-16 rounded-[4px] flex items-center justify-center text-[24px] font-mono bg-[#111111] border border-[#333333] text-[#EDEDED] shrink-0">
            {initial}
          </div>
          <div className="min-w-0">
            <div className="font-semibold text-[18px] text-[#EDEDED] tracking-tight truncate">{displayName}</div>
            <div className="text-[#888888] font-mono text-[11px] mt-1 truncate">{profile?.email || storeUser?.email}</div>
            <div className="flex items-center gap-2 mt-3 flex-wrap">
              {profile?.role === 'admin' && (
                <span className="flex items-center gap-1.5 px-2 py-0.5 rounded-[2px] bg-[#111111] text-[#EDEDED] border border-[#333333] text-[9px] font-mono uppercase tracking-widest">
                  <Crown className="h-3 w-3" /> sudo
                </span>
              )}
              <span className="flex items-center gap-1.5 px-2 py-0.5 rounded-[2px] bg-[#111111] text-[#888888] border border-[#333333] text-[9px] font-mono uppercase tracking-widest">
                <Building2 className="h-3 w-3" /> {profile?.org_name || 'root'}
              </span>
              <span className="flex items-center gap-1.5 px-2 py-0.5 rounded-[2px] bg-[#0070F3]/10 text-[#0070F3] border border-[#0070F3]/30 text-[9px] font-mono uppercase tracking-widest">
                {profile?.org_plan || 'base'} runtime
              </span>
            </div>
          </div>
        </div>

        <div className="space-y-5 pt-8 border-t border-[#333333]">
          <div className="space-y-2">
             <label className="text-[10px] font-mono uppercase tracking-widest text-[#888888]">Display Name Alias</label>
             <input
               className="h-10 w-full bg-[#111111] border border-[#333333] rounded-[4px] px-3 text-[13px] text-[#EDEDED] font-mono outline-none focus:border-[#888888] transition-colors"
               value={displayName}
               onChange={(e) => setDisplayName(e.target.value)}
               placeholder="root alias"
               maxLength={80}
             />
          </div>
          <div className="space-y-2">
            <label className="text-[10px] font-mono uppercase tracking-widest text-[#888888]">Authenticated Address</label>
            <input
               className="h-10 w-full bg-[#111111] border border-[#222222] rounded-[4px] px-3 text-[13px] text-[#888888] font-mono outline-none cursor-not-allowed"
               value={profile?.email || storeUser?.email || ''}
               disabled
               type="email"
             />
             <p className="text-[10px] font-mono text-[#555555] uppercase tracking-widest">Fixed identifier. Requires superuser token to modify.</p>
          </div>
        </div>
      </div>

      <div className="flex items-center justify-between">
        <button
          onClick={() => logout()}
          className="flex items-center gap-2 text-[10px] font-mono text-[#FF4444] hover:text-[#FF6666] transition-colors uppercase tracking-widest"
        >
          <LogOut className="h-3.5 w-3.5" />
          Terminate Session
        </button>
        <button
          onClick={handleSave}
          disabled={isSaving}
          className="flex items-center gap-2 px-6 py-2 rounded-[4px] bg-[#EDEDED] text-[#000000] font-medium text-[13px] disabled:opacity-50 hover:bg-[#CCCCCC] transition-colors"
        >
          {isSaving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
          {isSaving ? 'Commit...' : 'Commit Changes'}
        </button>
      </div>
    </div>
  )
}

// ── Security Section ────────────────────────────────────────────────────────────
function SecuritySection() {
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
  const strengthColor = ['', 'bg-[#FF4444]', 'bg-[#F5A623]', 'bg-[#F5A623]', 'bg-[#EDEDED]', 'bg-[#0070F3]'][strength]

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
      <div className="bg-[#000000] border border-[#333333] rounded-[4px] p-6 lg:p-8 space-y-6">
        <div className="space-y-2">
          <label className="text-[10px] font-mono uppercase tracking-widest text-[#888888]">Current Hash</label>
          <div className="relative">
            <input
              type={showCurrent ? 'text' : 'password'}
              className="h-10 w-full bg-[#111111] border border-[#333333] rounded-[4px] px-3 pr-10 text-[13px] text-[#EDEDED] font-mono outline-none focus:border-[#888888] transition-colors"
              value={current}
              onChange={(e) => setCurrent(e.target.value)}
              placeholder="••••••••"
            />
            <button type="button" onClick={() => setShowCurrent(v => !v)} className="absolute right-3 top-1/2 -translate-y-1/2 text-[#888888] hover:text-[#EDEDED]">
              {showCurrent ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
            </button>
          </div>
        </div>

        <div className="space-y-2">
          <label className="text-[10px] font-mono uppercase tracking-widest text-[#888888]">New Hash Directive</label>
          <div className="relative">
             <input
              type={showNext ? 'text' : 'password'}
              className="h-10 w-full bg-[#111111] border border-[#333333] rounded-[4px] px-3 pr-10 text-[13px] text-[#EDEDED] font-mono outline-none focus:border-[#888888] transition-colors"
              value={next}
              onChange={(e) => setNext(e.target.value)}
              placeholder="Minimum 8 bytes"
            />
            <button type="button" onClick={() => setShowNext(v => !v)} className="absolute right-3 top-1/2 -translate-y-1/2 text-[#888888] hover:text-[#EDEDED]">
              {showNext ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
            </button>
          </div>
          {next && (
            <div className="space-y-1.5 pt-2">
              <div className="flex gap-1 h-0.5">
                {[1,2,3,4,5].map(i => (
                  <div key={i} className={cn("flex-1 transition-colors duration-300", i <= strength ? strengthColor : 'bg-[#333333]')} />
                ))}
              </div>
              <p className="text-[9px] font-mono text-[#888888] uppercase tracking-widest">Entropy Level: {strengthLabel}</p>
            </div>
          )}
        </div>

        <div className="space-y-2">
          <label className="text-[10px] font-mono uppercase tracking-widest text-[#888888]">Verify New Directive</label>
          <input
            type="password"
            className={cn("h-10 w-full bg-[#111111] border rounded-[4px] px-3 pr-10 text-[13px] text-[#EDEDED] font-mono outline-none transition-colors", confirm && next !== confirm ? "border-[#FF4444]" : "border-[#333333] focus:border-[#888888]")}
            value={confirm}
            onChange={(e) => setConfirm(e.target.value)}
            placeholder="Re-enter configuration"
          />
          {confirm && next !== confirm && (
            <p className="text-[9px] font-mono text-[#FF4444] uppercase tracking-widest flex items-center gap-1.5 mt-2">
              <AlertTriangle className="h-3 w-3" /> Integrity mismatch
            </p>
          )}
        </div>

        <div className="pt-4 flex justify-end border-t border-[#333333]">
          <button
             onClick={handleChange}
             disabled={isSaving || !current || !next || !confirm}
             className="flex items-center gap-2 px-6 py-2 rounded-[4px] bg-[#EDEDED] text-[#000000] font-medium text-[13px] disabled:opacity-50 hover:bg-[#CCCCCC] transition-colors"
          >
             {isSaving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Shield className="h-4 w-4" />}
             {isSaving ? 'Encrypting...' : 'Update Proof'}
          </button>
        </div>
      </div>
    </div>
  )
}

// ── API Keys Section ────────────────────────────────────────────────────────────
function ApiKeysSection() {
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
    navigator.clipboard.writeText(text)
    setCopiedId(id)
    setTimeout(() => setCopiedId(null), 2000)
    toast.success('Buffer appended')
  }

  if (isLoading) return <div className="flex items-center justify-center py-20"><Loader2 className="h-6 w-6 animate-spin text-[#0070F3]" /></div>

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <SectionHeader title="Access Tokens" subtitle="Machine identities for programmatic system integration." />
        {!showCreateForm && (
          <button onClick={() => setShowCreateForm(true)} className="flex items-center gap-2 rounded-[4px] bg-[#EDEDED] text-[#000000] px-4 py-1.5 font-medium text-[12px] hover:bg-[#CCCCCC] transition-colors shrink-0">
            <Plus className="h-3.5 w-3.5" /> Initialize Token
          </button>
        )}
      </div>

      {/* New key revealed banner */}
      <AnimatePresence>
        {revealedKey && (
          <motion.div
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            className="rounded-[4px] border border-[#0070F3] bg-[#000000] p-6"
          >
             <div className="flex items-center gap-3 mb-4">
               <div className="h-8 w-8 rounded-[4px] bg-[#0070F3]/10 flex items-center justify-center shrink-0">
                 <Key className="h-4 w-4 text-[#0070F3]" />
               </div>
               <div>
                  <span className="text-[13px] font-medium text-[#EDEDED] block tracking-tight">Access token generated</span>
                  <p className="text-[11px] font-mono text-[#888888] mt-0.5">This secret is shown once. Store it securely in your local environment.</p>
               </div>
             </div>
             
             <div className="flex items-center gap-2 bg-[#111111] rounded-[4px] border border-[#333333] px-4 py-3">
               <code className="flex-1 text-[13px] text-[#EDEDED] font-mono break-all selection:bg-[#0070F3]/30">{revealedKey.key}</code>
               <button onClick={() => handleCopy(revealedKey.key, revealedKey.id)} className="shrink-0 p-2 rounded-[4px] hover:bg-[#222222] border border-transparent hover:border-[#333333] transition-colors">
                  {copiedId === revealedKey.id ? <Check className="h-4 w-4 text-[#0070F3]" /> : <Copy className="h-4 w-4 text-[#888888]" />}
               </button>
             </div>
             <button onClick={() => setRevealedKey(null)} className="mt-4 text-[9px] font-mono uppercase tracking-widest text-[#888888] hover:text-[#EDEDED] transition-colors">
               [ Dismiss Alert ]
             </button>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Create form */}
      <AnimatePresence>
        {showCreateForm && (
          <motion.div initial={{ opacity: 0, y: -8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -8 }} className="bg-[#000000] border border-[#333333] rounded-[4px] p-6 space-y-5">
            <div className="text-[14px] font-medium text-[#EDEDED] tracking-tight">Initialize Configuration</div>
            
            <div className="space-y-2">
               <label className="text-[10px] font-mono uppercase tracking-widest text-[#888888]">Alias</label>
               <input
                 className="h-10 w-full bg-[#111111] border border-[#333333] rounded-[4px] px-3 text-[13px] text-[#EDEDED] font-mono outline-none focus:border-[#888888] transition-colors"
                 placeholder="Terminal process identifier"
                 value={newLabel}
                 onChange={(e) => setNewLabel(e.target.value)}
                 maxLength={80}
               />
            </div>
            
            <div className="space-y-2">
               <label className="text-[10px] font-mono uppercase tracking-widest text-[#888888]">Validity Window</label>
               <select
                 className="h-10 w-full bg-[#111111] border border-[#333333] rounded-[4px] px-3 text-[13px] text-[#EDEDED] font-mono outline-none focus:border-[#888888] transition-colors appearance-none"
                 value={expiryDays}
                 onChange={(e) => setExpiryDays(e.target.value)}
               >
                 <option value="never">Infinite duration</option>
                 <option value="30">30 cycles (days)</option>
                 <option value="90">90 cycles (days)</option>
                 <option value="365">365 cycles (days)</option>
               </select>
            </div>
            
            <div className="flex items-center gap-4 pt-4 border-t border-[#333333]">
               <button onClick={handleCreate} disabled={isCreating || !newLabel.trim()} className="flex items-center gap-2 rounded-[4px] bg-[#EDEDED] text-[#000000] px-4 py-2 font-medium text-[13px] hover:bg-[#CCCCCC] transition-colors disabled:opacity-50">
                 {isCreating ? <Loader2 className="h-4 w-4 animate-spin" /> : <Key className="h-4 w-4" />}
                 {isCreating ? 'Compiling...' : 'Generate Resource'}
               </button>
               <button onClick={() => setShowCreateForm(false)} className="text-[11px] font-mono uppercase tracking-widest text-[#888888] hover:text-[#EDEDED] transition-colors">Abort</button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Keys list */}
      <div className="space-y-3">
        {keys.length === 0 ? (
          <div className="border border-dashed border-[#333333] rounded-[4px] py-20 text-center bg-[#111111]">
            <Server className="h-8 w-8 mx-auto mb-4 text-[#333333]" />
            <p className="text-[11px] font-mono text-[#888888] uppercase tracking-widest">Null Output Array</p>
            <p className="text-[12px] font-mono text-[#555555] mt-2">Initialize access tokens for automated systems integration.</p>
          </div>
        ) : (
          keys.map((k) => (
            <div key={k.id} className="bg-[#000000] border border-[#333333] rounded-[4px] px-6 py-5 flex items-start sm:items-center justify-between gap-4 flex-col sm:flex-row hover:border-[#888888] transition-colors">
              
              <div className="flex items-center gap-4 flex-1 min-w-0">
                 <div className="h-10 w-10 rounded-[4px] bg-[#111111] border border-[#333333] flex items-center justify-center shrink-0">
                   <Key className="h-4 w-4 text-[#888888]" />
                 </div>
                 <div className="min-w-0">
                    <div className="flex items-center gap-3 mb-1.5">
                       <span className="text-[14px] font-semibold text-[#EDEDED] truncate tracking-tight">{k.label}</span>
                       {k.is_active ? (
                         <span className="px-1.5 py-0.5 rounded-[2px] bg-[#111111] border border-[#333333] text-[#EDEDED] text-[9px] font-mono uppercase tracking-widest">Active</span>
                       ) : (
                         <span className="px-1.5 py-0.5 rounded-[2px] bg-[#2A0808] border border-[#5C1A1A] text-[#FF4444] text-[9px] font-mono uppercase tracking-widest">Revoked</span>
                       )}
                    </div>
                    <div className="flex items-center gap-3 flex-wrap text-[10px] font-mono text-[#888888] uppercase tracking-wider">
                       <span className="text-[#EDEDED]">{k.key_prefix}••••••••</span>
                       <span className="hidden sm:inline-block h-3 w-px bg-[#333333]" />
                       <span>{new Date(k.created_at).toLocaleDateString()}</span>
                       {k.expires_at && (
                         <>
                           <span className="hidden sm:inline-block h-3 w-px bg-[#333333]" />
                           <span className="text-[#FF4444]">T-{new Date(k.expires_at).toLocaleDateString()}</span>
                         </>
                       )}
                       {k.last_used_at && (
                         <>
                           <span className="hidden sm:inline-block h-3 w-px bg-[#333333]" />
                           <span className="text-[#0070F3]">Ping: {new Date(k.last_used_at).toLocaleDateString()}</span>
                         </>
                       )}
                    </div>
                 </div>
              </div>
              
              <button
                 onClick={() => handleRevoke(k.id)}
                 className="h-8 w-8 rounded-[4px] flex items-center justify-center text-[#888888] hover:text-[#FF4444] border border-transparent hover:border-[#FF4444] hover:bg-[#2A0808] transition-all shrink-0"
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

// ── Notifications Section ─────────────────────
function NotificationsSection() {
  const [prefs, setPrefs] = useState({
    analysis_complete: true,
    weekly_summary: false,
    product_updates: true,
  })

  const toggles: { key: keyof typeof prefs; label: string; desc: string }[] = [
    { key: 'analysis_complete', label: 'Runtime Complete Event', desc: 'Interrupt when computational tasks resolve.' },
    { key: 'weekly_summary', label: 'Digest Operations', desc: 'Aggregated analytics transmitted weekly.' },
    { key: 'product_updates', label: 'Platform Telemetry', desc: 'New schema properties and node structures.' },
  ]

  return (
    <div className="space-y-6">
      <SectionHeader title="System Telemetry" subtitle="Configure event interruption flags via external transports." />
      <div className="bg-[#000000] border border-[#333333] rounded-[4px] divide-y divide-[#333333]">
        {toggles.map((t) => (
          <div key={t.key} className="flex items-center justify-between gap-6 p-6">
            <div>
              <div className="text-[14px] font-medium text-[#EDEDED] tracking-tight">{t.label}</div>
              <div className="text-[11px] font-mono text-[#888888] mt-1 pr-6">{t.desc}</div>
            </div>
            <button
               onClick={() => setPrefs(p => ({ ...p, [t.key]: !p[t.key] }))}
               className={cn(
                 "relative w-10 h-5 rounded-full transition-all duration-300 shrink-0 border border-[#333333]",
                 prefs[t.key] ? "bg-[#EDEDED]" : "bg-[#111111]"
               )}
            >
               <span className={cn(
                  "absolute top-[1px] h-4 w-4 rounded-full transition-all duration-300",
                  prefs[t.key] ? "left-5 bg-[#000000]" : "left-1 bg-[#888888]"
               )} />
            </button>
          </div>
        ))}
      </div>
      <div className="flex justify-end border-t border-[#333333] pt-6 gap-4 mt-6">
         <button onClick={() => toast.success('Telemetry updated')} className="flex items-center gap-2 rounded-[4px] bg-[#EDEDED] text-[#000000] px-6 py-2 font-medium text-[13px] hover:bg-[#CCCCCC] transition-colors">
            <Save className="h-4 w-4" /> Save Flags
         </button>
      </div>
    </div>
  )
}

// ── Main page ──────────────────────────────────────────────────────────────────
export default function SettingsPage() {
  const { isAuthenticated } = useAuthStore()
  const [activeSection, setActiveSection] = useState('account')

  if (!isAuthenticated) return null

  return (
    <div className="p-6 lg:p-8 max-w-6xl mx-auto min-h-screen">
      <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="mb-12 border-b border-[#333333] pb-8">
         <div className="text-[10px] font-mono text-[#888888] uppercase tracking-widest mb-2">Workspace Integrity</div>
         <h1 className="text-[32px] font-semibold tracking-tight text-[#EDEDED] leading-tight">
            System <span className="text-[#888888]">Configuration</span>
         </h1>
         <p className="mt-3 text-[14px] font-mono text-[#888888] max-w-lg">
            Modify underlying environmental values, access scopes, and telemetry nodes.
         </p>
      </motion.div>

      <div className="flex flex-col lg:flex-row gap-12">
        {/* Sidebar nav */}
        <aside className="w-full lg:w-56 shrink-0">
          <nav className="flex lg:flex-col gap-2 overflow-x-auto pb-4 lg:pb-0">
            {SECTIONS.map((s) => (
              <button
                key={s.id}
                onClick={() => setActiveSection(s.id)}
                className={cn(
                  "flex items-center gap-3 px-4 py-3 rounded-[4px] text-[13px] font-medium text-left transition-all shrink-0 lg:shrink w-full border border-transparent",
                  activeSection === s.id
                    ? "bg-[#111111] text-[#EDEDED] border-[#333333]"
                    : "text-[#888888] hover:bg-[#000000] hover:text-[#EDEDED] hover:border-[#333333]"
                )}
              >
                <s.icon className="h-4 w-4 shrink-0" />
                {s.label}
              </button>
            ))}
          </nav>
        </aside>

        {/* Content panel */}
        <div className="flex-1 min-w-0 pb-32">
          <AnimatePresence mode="wait">
            <motion.div
              key={activeSection}
              initial={{ opacity: 0, x: 8 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -8 }}
              transition={{ duration: 0.15 }}
            >
              {activeSection === 'account' && <AccountSection />}
              {activeSection === 'security' && <SecuritySection />}
              {activeSection === 'api' && <ApiKeysSection />}
              {activeSection === 'notifications' && <NotificationsSection />}
            </motion.div>
          </AnimatePresence>
        </div>
      </div>
    </div>
  )
}
