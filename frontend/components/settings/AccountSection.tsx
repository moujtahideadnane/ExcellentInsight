"use client"

import React, { useEffect, useState } from 'react'
import { useAuthStore } from '@/stores/auth-store'
import api, { getErrorMessage } from '@/lib/api'
import { Loader2, LogOut, Crown, Building2, Save } from 'lucide-react'
import { toast } from 'sonner'
import { SectionHeader } from './SectionHeader'

interface Profile {
  id: string
  email: string
  display_name: string | null
  role: string
  org_name: string
  org_plan: string
  created_at: string
}

export function AccountSection() {
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
              <span className="flex items-center gap-1.5 px-2 py-0.5 rounded-[2px] bg-blue-500/10 text-blue-500 border border-blue-500/30 text-[9px] font-mono uppercase tracking-widest">
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
