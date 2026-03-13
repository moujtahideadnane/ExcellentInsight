"use client"

import React, { useEffect, useState } from 'react'
import { useRouter, usePathname } from 'next/navigation'
import { useAuthStore } from '@/stores/auth-store'
import { useJobStore } from '@/stores/job-store'
import {
  History,
  Settings,
  LogOut,
  Plus,
  Menu,
  X,
  ChevronLeft,
  ChevronRight,
  Terminal,
} from 'lucide-react'
import Link from 'next/link'
import Image from 'next/image'
import { cn } from '@/lib/utils'
import { motion, AnimatePresence } from 'framer-motion'
import PageTransition from '@/components/layout/PageTransition'

const navigation = [
  { name: 'Deployments', href: '/dashboard', icon: Terminal },
  { name: 'History Logs',   href: '/jobs',      icon: History },
  { name: 'Settings',  href: '/settings',  icon: Settings },
]

export default function ProtectedLayout({ children }: { children: React.ReactNode }) {
  const router   = useRouter()
  const pathname = usePathname()
  const { user, isAuthenticated, logout } = useAuthStore()
  const { activeJobId, clearActiveJob } = useJobStore()
  const [collapsed,   setCollapsed]   = useState(false)
  const [mobileOpen,  setMobileOpen]  = useState(false)
  const [hasHydrated, setHasHydrated] = useState(false)

  useEffect(() => {
    useAuthStore.persist.rehydrate()
    setHasHydrated(true)
  }, [])

  useEffect(() => {
    if (hasHydrated && !isAuthenticated) router.push('/login')
  }, [isAuthenticated, hasHydrated, router])

  useEffect(() => { setMobileOpen(false) }, [pathname])

  if (!hasHydrated)   return null
  if (!isAuthenticated) return null

  const userInitial = (user?.display_name?.[0] || user?.email?.[0] || '?').toUpperCase()
  const userName    = user?.display_name || user?.email?.split('@')[0] || ''

  const currentPage = navigation.find(
    n => n.href === pathname || (n.href === '/dashboard' && pathname?.startsWith('/dashboard'))
  )?.name ?? 'Terminal'

  return (
    <div className="flex h-screen overflow-hidden bg-ve-bg text-ve-text"> {/* REFACTOR: [consolidate-hex] */}

      {/* Mobile overlay */}
      <AnimatePresence>
        {mobileOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-40 lg:hidden bg-ve-overlay backdrop-blur-sm"
            onClick={() => setMobileOpen(false)}
          />
        )}
      </AnimatePresence>

      {/* Sidebar */}
      <aside
        className={cn(
          "fixed inset-y-0 left-0 z-50 flex flex-col transition-all duration-200 lg:relative lg:translate-x-0 bg-ve-bg border-r border-ve-border",
          collapsed ? "w-[64px]" : "w-[240px]",
          !mobileOpen && "-translate-x-full lg:translate-x-0",
          mobileOpen  && "w-[240px] translate-x-0"
        )}
      >
        {/* Logo */}
        <div className={cn("flex items-center h-14 px-4 shrink-0 border-b border-ve-border", collapsed ? "justify-center px-0" : "justify-between")}>
          {!collapsed && (
            <Link href="/" className="flex items-center gap-3">
              <div className="h-6 w-6 relative rounded-[2px] bg-ve-text flex items-center justify-center overflow-hidden">
                <Image src="/logo3.png" alt="ExcellentInsight Logo" fill className="object-contain p-0.5" />
              </div>
              <span className="font-semibold text-[14px] tracking-tight">
                ExcellentInsight
              </span>
            </Link>
          )}
          {collapsed && (
            <div className="h-6 w-6 relative rounded-[2px] bg-ve-btn-primary flex items-center justify-center overflow-hidden">
               <Image src="/logo3.png" alt="ExcellentInsight Logo" fill className="object-contain p-0.5" />
            </div>
          )}

          {/* Desktop collapse toggle */}
          <button
            onClick={() => setCollapsed(!collapsed)}
            className="hidden lg:flex h-6 w-6 items-center justify-center rounded-[4px] text-ve-muted hover:text-ve-text hover:bg-ve-surface transition-colors"
            aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
          >
            {collapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
          </button>

          {/* Mobile close */}
          <button
            onClick={() => setMobileOpen(false)}
            className="flex lg:hidden h-6 w-6 items-center justify-center rounded-[4px] text-ve-muted hover:bg-ve-surface"
            aria-label="Close menu"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* Navigation */}
        <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
          {navigation.map((item) => {
            const isActive = pathname === item.href || (item.href === '/dashboard' && pathname?.startsWith('/dashboard'))
            const href = (item.name === 'Deployments' && activeJobId) ? `/dashboard/${activeJobId}` : item.href

            return (
              <Link
                key={item.name}
                href={href}
                prefetch={true}
                className={cn(
                  "flex items-center gap-3 px-3 py-2 rounded-[4px] text-[13px] font-medium transition-colors cursor-pointer",
                  isActive 
                    ? "bg-ve-surface text-ve-text border border-ve-border" 
                    : "text-ve-muted border border-transparent hover:bg-ve-surface hover:text-ve-text",
                  collapsed && "justify-center px-0 border-transparent shadow-none w-10 h-10 mx-auto"
                )}
                title={collapsed ? item.name : undefined}
              >
                <item.icon className="h-4 w-4 shrink-0" />
                {!collapsed && <span className="truncate">{item.name}</span>}
              </Link>
            )
          })}
        </nav>

        {/* Profile / Logout */}
        <div className="p-3 border-t border-ve-border">
          {!collapsed ? (
            <div className="flex items-center gap-3 px-3 py-2 rounded-[4px] bg-ve-surface border border-ve-border">
              <div className="h-6 w-6 rounded-[2px] bg-ve-text text-ve-bg flex items-center justify-center text-[10px] font-mono font-bold shrink-0">
                {userInitial}
              </div>
              <div className="flex-1 min-w-0">
                <div className="text-[12px] font-medium text-ve-text truncate">{userName}</div>
                <div className="text-[10px] font-mono text-ve-muted truncate">{user?.email}</div>
              </div>
              <button
                onClick={() => logout()}
                className="h-6 w-6 flex items-center justify-center rounded-[4px] text-ve-muted hover:text-ve-text hover:bg-ve-elevated transition-colors"
                title="Sign out"
                aria-label="Sign out"
              >
                <LogOut className="h-3.5 w-3.5" />
              </button>
            </div>
          ) : (
            <button
              onClick={() => logout()}
              className="w-10 h-10 mx-auto flex items-center justify-center rounded-[4px] text-ve-muted hover:text-ve-text hover:bg-ve-surface transition-colors"
              title="Sign out"
              aria-label="Sign out"
            >
              <LogOut className="h-4 w-4" />
            </button>
          )}
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col overflow-hidden bg-ve-bg">
        
        {/* Top bar */}
        <header className="h-14 flex items-center justify-between px-6 shrink-0 border-b border-ve-border bg-ve-bg">
          <div className="flex items-center gap-4">
            <button
              onClick={() => setMobileOpen(true)}
              className="p-1.5 rounded-[4px] lg:hidden text-ve-muted hover:bg-ve-surface"
              aria-label="Open menu"
            >
              <Menu className="h-5 w-5" />
            </button>
            <span className="text-[13px] font-mono font-medium text-ve-muted px-2 py-0.5 border border-ve-border rounded-[4px] bg-ve-surface">
              ~/{currentPage.toLowerCase()}
            </span>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={() => {
                clearActiveJob()
                router.push('/dashboard')
              }}
              className="hidden sm:flex items-center gap-2 h-7 px-3 rounded-[4px] bg-ve-btn-primary text-ve-btn-text text-[12px] font-medium hover:bg-ve-btn-hover transition-colors"
            >
              <Plus className="h-3.5 w-3.5" /> Initialize
            </button>
          </div>
        </header>

        {/* REFACTOR: [fix-alignment] — items-center ensures child max-w-* containers are horizontally centered */}
        <div className="flex-1 overflow-y-auto relative flex flex-col items-center">
          <PageTransition>
            {children}
          </PageTransition>
        </div>
      </main>
    </div>
  )
}
