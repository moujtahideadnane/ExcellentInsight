"use client"

import React, { useRef, useEffect, useState } from 'react'
import Link from 'next/link'
import Image from 'next/image'
import dynamic from 'next/dynamic'
import {
  motion,
  useMotionValue,
  useSpring,
} from 'framer-motion'
import {
  ArrowRight, Terminal
} from 'lucide-react'
import { useAuthStore } from '@/stores/auth-store'
import { cn } from '@/lib/utils'

// Lazy load landing page artifacts for better initial page load
const ZeroSchemaMatrix = dynamic(() => import('@/components/landing/artifacts/ingestion/ZeroSchemaMatrix').then(mod => ({ default: mod.ZeroSchemaMatrix })), {
  loading: () => <div className="min-h-[400px] flex items-center justify-center"><span className="text-[#888888] font-mono text-sm">Loading...</span></div>,
  ssr: false
})
const SubSecondRenderer = dynamic(() => import('@/components/landing/artifacts/rendering/SubSecondRenderer').then(mod => ({ default: mod.SubSecondRenderer })), {
  loading: () => <div className="min-h-[400px] flex items-center justify-center"><span className="text-[#888888] font-mono text-sm">Loading...</span></div>,
  ssr: false
})
const EdgeTerminal = dynamic(() => import('@/components/landing/artifacts/api/EdgeTerminal').then(mod => ({ default: mod.EdgeTerminal })), {
  loading: () => <div className="min-h-[400px] flex items-center justify-center"><span className="text-[#888888] font-mono text-sm">Loading...</span></div>,
  ssr: false
})
const InferenceEngine = dynamic(() => import('@/components/landing/artifacts/inference/InferenceEngine').then(mod => ({ default: mod.InferenceEngine })), {
  loading: () => <div className="min-h-[400px] flex items-center justify-center"><span className="text-[#888888] font-mono text-sm">Loading...</span></div>,
  ssr: false
})

/* ── Magnetic Button Wrapper (Surgical, low-lag) ─────────────────── */
function MagneticButton({ children, className }: { children: React.ReactNode; className?: string }) {
  const ref = useRef<HTMLDivElement>(null)
  const x = useMotionValue(0)
  const y = useMotionValue(0)
  const sx = useSpring(x, { stiffness: 300, damping: 20 }) // Tighter spring
  const sy = useSpring(y, { stiffness: 300, damping: 20 })

  const handleMouse = (e: React.MouseEvent) => {
    if (!ref.current) return
    const rect = ref.current.getBoundingClientRect()
    const cx = rect.left + rect.width / 2
    const cy = rect.top + rect.height / 2
    x.set((e.clientX - cx) * 0.2)
    y.set((e.clientY - cy) * 0.2)
  }

  return (
    <motion.div
      ref={ref}
      style={{ x: sx, y: sy }}
      className={className}
      onMouseMove={handleMouse}
      onMouseLeave={() => { x.set(0); y.set(0) }}
    >
      {children}
    </motion.div>
  )
}

/* ── Typewriter Precision (Section 5.4) ────────────────────────── */
function TypewriterText({ text, delay = 0, className }: { text: string; delay?: number; className?: string }) {
  const [displayed, setDisplayed] = useState('')
  const [started, setStarted] = useState(false)
  const ref = useRef<HTMLSpanElement>(null)

  useEffect(() => {
    const observer = new IntersectionObserver((entries) => {
      const entry = entries[0]
      if (entry?.isIntersecting && !started) {
        setStarted(true)
        setTimeout(() => {
          let i = 0
          const weights: Record<string, number> = { ',': 200, '.': 350, '!': 350, '?': 350, ':': 150, ' ': 60 }
          const type = () => {
            if (i < text.length) {
              setDisplayed(text.substring(0, i + 1))
              const char = text[i] as string
              i++
              setTimeout(type, weights[char] || 30) // Fast, mechanical typing
            }
          }
          type()
        }, delay * 1000)
      }
    }, { threshold: 0.1 })
    if (ref.current) observer.observe(ref.current)
    return () => observer.disconnect()
  }, [text, delay, started])

  return <span ref={ref} className={className}>{displayed}</span>
}

/* ── Terminal Output Simulation (Excel Analysis) ────── */
function TerminalOutput() {
  const lines = [
    "[INFO] Processing sales_report_Q4.xlsx...",
    "[OK]   File uploaded: 3 sheets, 4.2MB",
    "[INFO] Auto-detecting schema and data types...",
    "[OK]   Detected 12 columns, 15,420 rows across sheets",
    "[INFO] AI analyzing business metrics...",
    "[OK]   Identified 8 KPIs: Revenue, Growth, Conversion Rate...",
    "[INFO] Generating interactive dashboard...",
    "[OK]   Analysis complete. Dashboard ready in 47.3s"
  ]

  const [visibleLines, setVisibleLines] = useState<number>(0)

  useEffect(() => {
    let current = 0
    const interval = setInterval(() => {
      if (current < lines.length) {
        setVisibleLines(prev => prev + 1)
        current++
      } else {
        clearInterval(interval)
      }
    }, 450)
    return () => clearInterval(interval)
  }, [lines.length])

  return (
    <div className="w-full bg-[#000000] border border-[#333333] rounded-md overflow-hidden font-mono text-[13px] leading-relaxed shadow-2xl relative">
      <div className="flex flex-col p-4 gap-1 min-h-[220px]">
        {lines.slice(0, visibleLines).map((line, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            className={`flex gap-3 ${line.includes('[OK]') ? 'text-[#EDEDED]' : line.includes('[WARN]') ? 'text-[#F5A623]' : 'text-[#888888]'}`}
          >
            <span>›</span>
            <span>{line}</span>
          </motion.div>
        ))}
        {visibleLines < lines.length && (
          <motion.div animate={{ opacity: [1, 0] }} transition={{ repeat: Infinity, duration: 0.8 }} className="w-2.5 h-4 bg-[#EDEDED] mt-1 ml-4" />
        )}
      </div>
      {/* Vercel Edge aesthetic: tiny technical labels */}
      <div className="absolute top-2 right-4 text-[10px] text-[#888888]">us-east-1</div>
    </div>
  )
}

/* ── Scroll-Synced Counter (Section 5.5) ────────────────────────── */
function Counter({ target, suffix = '' }: { target: number; suffix?: string }) {
  const [count, setCount] = useState(0)
  const ref = useRef<HTMLSpanElement>(null)
  const started = useRef(false)

  useEffect(() => {
    const observer = new IntersectionObserver((entries) => {
      const entry = entries[0]
      if (entry?.isIntersecting && !started.current) {
        started.current = true
        let start = 0
        const duration = 1200 // Faster
        const step = (timestamp: number) => {
          if (!start) start = timestamp
          const progress = Math.min((timestamp - start) / duration, 1)
          const ease = 1 - Math.pow(1 - progress, 3)
          setCount(Math.floor(ease * target))
          if (progress < 1) requestAnimationFrame(step)
          else setCount(target)
        }
        requestAnimationFrame(step)
      }
    }, { threshold: 0.5 })
    if (ref.current) observer.observe(ref.current)
    return () => observer.disconnect()
  }, [target])

  return <span ref={ref}>{count.toLocaleString()}{suffix}</span>
}


export default function LandingClient() {
  const [scrolled, setScrolled] = useState(false)
  const [mounted, setMounted] = useState(false)
  const { isAuthenticated } = useAuthStore()

  useEffect(() => {
    setMounted(true)
    useAuthStore.persist.rehydrate()
    const onScroll = () => {
      setScrolled(window.scrollY > 30)
      // Custom Scroll Velocity Tilt applied to hero
      const velocity = window.scrollY * 0.05
      const tilt = Math.max(-4, Math.min(4, velocity))
      document.body.style.setProperty('--scroll-tilt', `${tilt}deg`)
    }
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => window.removeEventListener('scroll', onScroll)
  }, [])

  return (
    <div className="min-h-screen bg-[#000000] text-[#EDEDED] selection:bg-[#0070F3] selection:text-white font-[family-name:var(--font-sans)] overflow-x-hidden">

      {/* ── Navigation (Sticky, pure black) ── */}
      <nav className={cn(
        "fixed top-0 left-0 right-0 z-50 flex items-center justify-between px-6 md:px-12 py-4 transition-all duration-200",
        scrolled ? "bg-black/90 backdrop-blur-md border-b border-[#333333]" : "bg-transparent"
      )}>
        <div className="flex items-center gap-3">
          <div className="h-7 w-7 relative bg-white flex items-center justify-center rounded-[5px] overflow-hidden shadow-sm">
             <Image src="/logo3.png" alt="ExcellentInsight Logo" fill className="object-contain p-1" />
          </div>
          <span className="font-semibold tracking-tight text-[16px]">ExcellentInsight</span>
        </div>

        <div className="hidden md:flex items-center gap-8 text-[13px] font-medium text-[#888888]">
          <Link href="#features" className="hover:text-white transition-colors">Features</Link>
          <Link href="#how-it-works" className="hover:text-white transition-colors">How It Works</Link>
          <Link href="#use-cases" className="hover:text-white transition-colors">Use Cases</Link>
        </div>

        <div className="flex items-center gap-6 text-[13px] font-medium">
          {!isAuthenticated ? (
            <>
              <Link href="/login" className="text-[#888888] hover:text-white transition-colors">Login</Link>
              <MagneticButton>
                <Link href="/signup" className="bg-white text-black px-4 py-1.5 rounded-[6px] hover:bg-[#CCCCCC] transition-colors flex items-center gap-2">
                  Deploy
                </Link>
              </MagneticButton>
            </>
          ) : (
            <Link href="/dashboard" className="bg-white text-black px-4 py-1.5 rounded-[6px] hover:bg-[#CCCCCC] transition-colors flex items-center gap-2">
              <Terminal className="h-3.5 w-3.5" /> Dashboard
            </Link>
          )}
        </div>
      </nav>

      {/* ── Hero (Monumental Typography & Terminal) ── */}
      <section className="relative min-h-[85vh] flex items-center py-24 lg:py-32 px-4 sm:px-6 lg:px-8 w-full max-w-7xl mx-auto scroll-tilt-target">
        <div className="flex-1 flex flex-col items-start gap-8 z-10 w-full mb-16 md:mb-0">

          <h1 className="text-[clamp(3.5rem,8vw,6rem)] font-bold leading-[0.9] tracking-tighter">
            Transform Excel <br className="hidden md:block" />
            <span className="text-[#888888]">into insights.</span>
          </h1>

          <p className="text-[16px] text-[#888888] max-w-md leading-relaxed">
            <TypewriterText text="Upload any Excel or CSV file. AI automatically detects KPIs, generates interactive dashboards, and surfaces actionable insights in under 60 seconds. Zero configuration required." />
          </p>

          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.8 }} className="flex items-center gap-4 mt-4 w-full flex-wrap">
            <MagneticButton>
              <Link href="/signup" className="bg-white text-black px-6 py-3 rounded-[6px] text-sm font-medium hover:bg-[#CCCCCC] transition-colors flex items-center gap-2">
                Analyze Your First File <ArrowRight className="h-4 w-4" />
              </Link>
            </MagneticButton>
            <Link href="/dashboard" className="px-6 py-3 rounded-[6px] text-sm font-medium text-[#888888] bg-[#111111] border border-[#333333] hover:text-white hover:border-[#888888] transition-colors flex items-center gap-2">
              <Terminal className="h-4 w-4" />
              View Sample Dashboard
            </Link>
          </motion.div>
        </div>

        <div className="flex-1 w-full max-w-[600px] xl:max-w-none">
          <motion.div initial={{ opacity: 0, transform: 'translateY(20px) scale(0.98)' }} animate={{ opacity: 1, transform: 'translateY(0) scale(1)' }} transition={{ duration: 0.5, delay: 0.2 }} >
            {mounted && <TerminalOutput />}
          </motion.div>

          {/* Dashboard Metrics Grid */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-8 w-full">
             {[
               { val: 60, l: 'Sec Analysis', suffix: '' },
               { val: 15, l: 'K+ Files', suffix: '' },
               { val: 99, l: '% Accuracy', suffix: '' },
               { val: 0, l: 'Config', suffix: '' }
             ].map((s, i) => (
               <motion.div key={i} initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.5 + i * 0.1 }} className="bg-[#111111] p-4 flex flex-col justify-center items-center gap-1 border border-[#333333] rounded-[6px] hover:bg-[#1C1C1C] hover:border-[#888888] transition-colors cursor-default">
                  <span className="font-mono text-[18px] font-medium text-white"><Counter target={s.val} suffix={s.suffix} /></span>
                  <span className="text-[10px] tracking-widest uppercase text-[#888888]">{s.l}</span>
               </motion.div>
             ))}
          </div>
        </div>
      </section>

      {/* ── ARTIFACT I : ZeroSchemaMatrix ── */}
      <ZeroSchemaMatrix />

      {/* ── ARTIFACT II : SubSecondRenderer ── */}
      <SubSecondRenderer />

      {/* ── ARTIFACT III : EdgeTerminal ── */}
      <EdgeTerminal />

      {/* ── ARTIFACT IV : InferenceEngine ── */}
      <InferenceEngine />

      {/* ── Call To Action ── */}
      <section className="py-24 lg:py-32 px-4 sm:px-6 lg:px-8 border-t border-[#222222] w-full max-w-7xl mx-auto" id="get-started">
        <div className="max-w-4xl mx-auto flex flex-col items-center text-center gap-8" data-animate>
          <div className="h-14 w-14 relative bg-white flex items-center justify-center rounded-[10px] overflow-hidden shadow-lg">
             <Image src="/logo3.png" alt="ExcellentInsight Logo" fill className="object-contain p-2" />
          </div>
          <h2 className="text-[clamp(2.5rem,5vw,4rem)] font-bold tracking-tighter leading-[1]">
            Transform your spreadsheets <br/> into intelligence today.
          </h2>
          <p className="text-[#888888] text-[16px] max-w-2xl leading-relaxed">
            Join thousands of teams using ExcellentInsight to analyze Excel and CSV files with AI.
            No credit card required. Start with our free tier and upgrade as you grow.
          </p>

          {/* Feature highlights */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 w-full mt-8 mb-8">
            <div className="flex flex-col items-center gap-2 p-4">
              <div className="text-[#EDEDED] font-mono text-[24px] font-bold">60s</div>
              <div className="text-[#888888] text-[13px]">Average analysis time</div>
            </div>
            <div className="flex flex-col items-center gap-2 p-4">
              <div className="text-[#EDEDED] font-mono text-[24px] font-bold">Auto</div>
              <div className="text-[#888888] text-[13px]">KPI detection powered by AI</div>
            </div>
            <div className="flex flex-col items-center gap-2 p-4">
              <div className="text-[#EDEDED] font-mono text-[24px] font-bold">Zero</div>
              <div className="text-[#888888] text-[13px]">Configuration required</div>
            </div>
          </div>

          <div className="flex items-center gap-4 mt-4">
            <MagneticButton>
              <Link href="/signup" className="bg-white text-black px-8 py-3 rounded-[6px] font-medium hover:bg-[#CCCCCC] transition-colors text-sm">
                Start Free Analysis
              </Link>
            </MagneticButton>
            <Link href="/dashboard" className="px-8 py-3 rounded-[6px] font-medium text-white border border-[#333333] hover:bg-[#111111] transition-colors text-sm">
              View Demo Dashboard
            </Link>
          </div>
        </div>
      </section>

      {/* ── Footer ── */}
      <footer className="border-t border-[#222222] py-12 px-4 sm:px-6 lg:px-8 text-[#888888] text-[13px] flex flex-col md:flex-row items-center justify-between gap-6 max-w-7xl mx-auto w-full">
         <div className="flex items-center gap-2 font-mono">
            <div className="h-5 w-5 relative bg-white flex items-center justify-center rounded-[3px] overflow-hidden">
               <Image src="/logo3.png" alt="ExcellentInsight Logo" fill className="object-contain p-0.5" />
            </div>
            ExcellentInsight © 2026
         </div>
         <div className="flex items-center gap-6 font-medium">
            <a href="https://github.com/moujtahideadnane/ExcellentInsight" target="_blank" rel="noopener noreferrer" className="hover:text-white transition-colors">GitHub</a>
            <a href="https://github.com/moujtahideadnane/ExcellentInsight/blob/main/docs/API.md" target="_blank" rel="noopener noreferrer" className="hover:text-white transition-colors">API Docs</a>
            <a href="https://github.com/moujtahideadnane/ExcellentInsight/blob/main/docs/FEATURES.md" target="_blank" rel="noopener noreferrer" className="hover:text-white transition-colors">Features</a>
            <a href="https://github.com/moujtahideadnane/ExcellentInsight/issues" target="_blank" rel="noopener noreferrer" className="hover:text-white transition-colors">Support</a>
         </div>
      </footer>
    </div>
  )
}
