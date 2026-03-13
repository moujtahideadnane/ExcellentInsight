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
    <div className="flex h-screen overflow-hidden bg-[#000000] text-[#EDEDED]">

      {/* Mobile overlay */}
      <AnimatePresence>
        {mobileOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-40 lg:hidden bg-[#000000]/80 backdrop-blur-sm"
            onClick={() => setMobileOpen(false)}
          />
        )}
      </AnimatePresence>

      {/* Sidebar */}
      <aside
        className={cn(
          "fixed inset-y-0 left-0 z-50 flex flex-col transition-all duration-200 lg:relative lg:translate-x-0 bg-[#000000] border-r border-[#333333]",
          collapsed ? "w-[64px]" : "w-[240px]",
          !mobileOpen && "-translate-x-full lg:translate-x-0",
          mobileOpen  && "w-[240px] translate-x-0"
        )}
      >
        {/* Logo */}
        <div className={cn("flex items-center h-14 px-4 shrink-0 border-b border-[#333333]", collapsed ? "justify-center px-0" : "justify-between")}>
          {!collapsed && (
            <Link href="/" className="flex items-center gap-3">
              <div className="h-6 w-6 relative rounded-[2px] bg-[#EDEDED] flex items-center justify-center overflow-hidden">
                <Image src="/logo3.png" alt="ExcellentInsight Logo" fill className="object-contain p-0.5" />
              </div>
              <span className="font-semibold text-[14px] tracking-tight">
                ExcellentInsight
              </span>
            </Link>
          )}
          {collapsed && (
            <div className="h-6 w-6 relative rounded-[2px] bg-[#EDEDED] flex items-center justify-center overflow-hidden">
               <Image src="/logo3.png" alt="ExcellentInsight Logo" fill className="object-contain p-0.5" />
            </div>
          )}

          {/* Desktop collapse toggle */}
          <button
            onClick={() => setCollapsed(!collapsed)}
            className="hidden lg:flex h-6 w-6 items-center justify-center rounded-[4px] text-[#888888] hover:text-[#EDEDED] hover:bg-[#111111] transition-colors"
            aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
          >
            {collapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
          </button>

          {/* Mobile close */}
          <button
            onClick={() => setMobileOpen(false)}
            className="flex lg:hidden h-6 w-6 items-center justify-center rounded-[4px] text-[#888888] hover:bg-[#111111]"
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
                    ? "bg-[#111111] text-[#EDEDED] border border-[#333333]" 
                    : "text-[#888888] border border-transparent hover:bg-[#111111] hover:text-[#EDEDED]",
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
        <div className="p-3 border-t border-[#333333]">
          {!collapsed ? (
            <div className="flex items-center gap-3 px-3 py-2 rounded-[4px] bg-[#111111] border border-[#333333]">
              <div className="h-6 w-6 rounded-[2px] bg-[#EDEDED] text-[#000000] flex items-center justify-center text-[10px] font-mono font-bold shrink-0">
                {userInitial}
              </div>
              <div className="flex-1 min-w-0">
                <div className="text-[12px] font-medium text-[#EDEDED] truncate">{userName}</div>
                <div className="text-[10px] font-mono text-[#888888] truncate">{user?.email}</div>
              </div>
              <button
                onClick={() => logout()}
                className="h-6 w-6 flex items-center justify-center rounded-[4px] text-[#888888] hover:text-[#EDEDED] hover:bg-[#1C1C1C] transition-colors"
                title="Sign out"
                aria-label="Sign out"
              >
                <LogOut className="h-3.5 w-3.5" />
              </button>
            </div>
          ) : (
            <button
              onClick={() => logout()}
              className="w-10 h-10 mx-auto flex items-center justify-center rounded-[4px] text-[#888888] hover:text-[#EDEDED] hover:bg-[#111111] transition-colors"
              title="Sign out"
              aria-label="Sign out"
            >
              <LogOut className="h-4 w-4" />
            </button>
          )}
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col overflow-hidden bg-[#000000]">
        
        {/* Top bar */}
        <header className="h-14 flex items-center justify-between px-6 shrink-0 border-b border-[#333333] bg-[#000000]">
          <div className="flex items-center gap-4">
            <button
              onClick={() => setMobileOpen(true)}
              className="p-1.5 rounded-[4px] lg:hidden text-[#888888] hover:bg-[#111111]"
              aria-label="Open menu"
            >
              <Menu className="h-5 w-5" />
            </button>
            <span className="text-[13px] font-mono font-medium text-[#888888] px-2 py-0.5 border border-[#333333] rounded-[4px] bg-[#111111]">
              ~/{currentPage.toLowerCase()}
            </span>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={() => {
                clearActiveJob()
                router.push('/dashboard')
              }}
              className="hidden sm:flex items-center gap-2 h-7 px-3 rounded-[4px] bg-[#EDEDED] text-[#000000] text-[12px] font-medium hover:bg-[#CCCCCC] transition-colors"
            >
              <Plus className="h-3.5 w-3.5" /> Initialize
            </button>
          </div>
        </header>

        {/* Page content */}
        <div className="flex-1 overflow-y-auto relative">
          <PageTransition>
            {children}
          </PageTransition>
        </div>
      </main>
    </div>
  )
}
