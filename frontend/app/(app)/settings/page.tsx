"use client"

import React, { useState } from 'react'
import { useAuthStore } from '@/stores/auth-store'
import { User, Bell, Shield, Key } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import { cn } from '@/lib/utils'

import { AccountSection } from '@/components/settings/AccountSection'
import { SecuritySection } from '@/components/settings/SecuritySection'
import { ApiKeysSection } from '@/components/settings/ApiKeysSection'
import { NotificationsSection } from '@/components/settings/NotificationsSection'

const SECTIONS = [
  { id: 'account',       label: 'Identity',       icon: User },
  { id: 'security',      label: 'Security',       icon: Shield },
  { id: 'api',           label: 'Tokens',         icon: Key },
  { id: 'notifications', label: 'Telemetry',      icon: Bell },
]

export default function SettingsPage() {
  const { isAuthenticated } = useAuthStore()
  const [activeSection, setActiveSection] = useState('account')

  if (!isAuthenticated) return null

  return (
    <div className="p-6 lg:p-8 max-w-6xl mx-auto min-h-screen"> {/* REFACTOR: [consolidate-hex] */}
      <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="mb-12 border-b border-ve-border pb-8">
         <div className="text-[10px] font-mono text-ve-muted uppercase tracking-widest mb-2">Workspace Integrity</div>
         <h1 className="text-[32px] font-semibold tracking-tight text-ve-text leading-tight">
            System <span className="text-ve-muted">Configuration</span>
         </h1>
         <p className="mt-3 text-[14px] font-mono text-ve-muted max-w-lg">
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
                    ? "bg-ve-surface text-ve-text border-ve-border"
                    : "text-ve-muted hover:bg-ve-bg hover:text-ve-text hover:border-ve-border"
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
