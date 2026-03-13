"use client"

import React, { useState } from 'react'
import { Save } from 'lucide-react'
import { toast } from 'sonner'
import { cn } from '@/lib/utils'
import { SectionHeader } from './SectionHeader'

export function NotificationsSection() {
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
