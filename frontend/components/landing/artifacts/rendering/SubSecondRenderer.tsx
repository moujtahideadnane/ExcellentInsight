"use client"

import React, { useState, useEffect, useRef, useMemo } from 'react'
import { motion, useInView, useAnimation } from 'framer-motion'
import { Activity } from 'lucide-react'

// Lightweight simulated scatter/area points
function seededRandom(seed: number) {
  const x = Math.sin(seed) * 10000;
  return x - Math.floor(x);
}

function generatePoints(count: number, width: number, height: number, variance: number) {
  const points = []
  for (let i = 0; i < count; i++) {
    const x = (i / count) * width
    // Sine wave + noise
    const noise = seededRandom(i + count) - 0.5;
    const y = (height / 2) + Math.sin(i * 0.1) * (height / 4) + noise * variance
    points.push(`${x.toFixed(2)},${Math.max(0, Math.min(height, y)).toFixed(2)}`)
  }
  return points.join(' ')
}

export function SubSecondRenderer() {
  const containerRef = useRef<HTMLDivElement>(null)
  const isInView = useInView(containerRef, { once: false, amount: 0.3 })
  const controls = useAnimation()
  
  const [level, setLevel] = useState<0 | 1 | 2>(0)
  const levels = [
    { label: '10K Rows', points: 100, variance: 20, timeMs: 4.2 },
    { label: '1M Rows', points: 400, variance: 80, timeMs: 12.8 },
    { label: '100M Rows', points: 1200, variance: 150, timeMs: 44.1 },
  ]

  // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
  const activeLevel = levels[level]!
  
  // Memoize path generation to simulate render speed without crushing the actual DOM immediately
  const pathData = useMemo(() => {
    return generatePoints(activeLevel.points, 1000, 300, activeLevel.variance)
  }, [activeLevel])

  // Telemetry state
  const [fps, setFps] = useState(60)
  
  useEffect(() => {
    if (isInView) {
      controls.start({ opacity: 1, y: 0 })
      const interval = setInterval(() => {
        // Slight fluctuation in FPS to make it feel real
        setFps(60 - Math.floor(Math.random() * 3))
      }, 500)
      return () => clearInterval(interval)
    } else {
      controls.set({ opacity: 0, y: 20 })
      return undefined
    }
  }, [isInView, controls])

  return (
    <motion.section 
      ref={containerRef}
      initial={{ opacity: 0, y: 20 }}
      animate={controls}
      className="py-32 px-6 md:px-12 max-w-7xl mx-auto border-t border-[#222222] relative"
    >
      <div className="mb-16 max-w-2xl">
        <div className="text-[10px] font-mono text-[#888888] py-1 px-2 border border-[#333333] rounded-[4px] w-fit mb-4">ARTIFACT II : COMPUTE</div>
        <h2 className="text-[32px] md:text-[48px] font-bold tracking-tight mb-4">Sub-Second Render Engine.</h2>
        <p className="text-[#888888] text-[16px] leading-relaxed">
          The visualization layer runs on a highly optimized Canvas/SVG hybrid. We push aggregation to the Edge and render millions of data points at an unwavering 60 frames per second.
        </p>
      </div>

      <div className="bg-[#050505] border border-[#333333] rounded-[6px] overflow-hidden relative">
        
        {/* Top Control Bar */}
        <div className="border-b border-[#222222] p-4 flex flex-col md:flex-row md:items-center justify-between gap-4 bg-[#000000]">
          <div className="flex bg-[#111111] p-1 rounded-[6px] border border-[#333333] w-fit">
            {levels.map((lvl, idx) => (
              <button
                key={idx}
                onClick={() => setLevel(idx as 0 | 1 | 2)}
                className={`px-4 py-1.5 text-[12px] font-mono rounded-[4px] transition-all ${level === idx ? 'bg-white text-black font-semibold shadow-sm' : 'text-[#888888] hover:text-[#EDEDED]'}`}
              >
                {lvl.label}
              </button>
            ))}
          </div>

          <div className="flex items-center gap-6">
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-[#00E5FF] animate-pulse" />
              <span className="text-[#888888] font-mono text-[12px]">FPS: {fps}</span>
            </div>
            <div className="flex items-center gap-2">
              <Activity className="h-4 w-4 text-[#888888]" />
              <span className="text-[#888888] font-mono text-[12px]">Latency: {activeLevel.timeMs.toFixed(1)}ms</span>
            </div>
          </div>
        </div>

        {/* The Chart Area (Simulated Density) */}
        <div className="relative h-[400px] w-full bg-[#000000] overflow-hidden flex items-end">
           {/* Grid Lines */}
           <div className="absolute inset-0 flex flex-col justify-between opacity-10 pointer-events-none p-4">
             {[1,2,3,4,5].map(i => <div key={i} className="border-b border-white w-full h-0" />)}
           </div>

           {/* The SVG Data Layer */}
           <svg preserveAspectRatio="none" viewBox="0 0 1000 300" className="w-full h-[300px] absolute bottom-0">
              <defs>
                <linearGradient id="areaGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#EDEDED" stopOpacity="0.2" />
                  <stop offset="100%" stopColor="#EDEDED" stopOpacity="0.0" />
                </linearGradient>
              </defs>
              <motion.path 
                initial={false}
                animate={{ d: `M0,300 L${pathData} L1000,300 Z` }}
                transition={{ type: 'spring', stiffness: 100, damping: 20 }}
                fill="url(#areaGradient)"
              />
              <motion.polyline 
                initial={false}
                animate={{ points: pathData }}
                transition={{ type: 'spring', stiffness: 100, damping: 20 }}
                fill="none"
                stroke="#EDEDED"
                strokeWidth={level === 2 ? 0.5 : 1}
                strokeOpacity={level === 2 ? 0.4 : 0.8}
              />
           </svg>

           {/* Edge Overlay */}
           <div className="absolute bottom-4 right-4 text-[10px] font-mono text-[#444444]">
             RENDER: HYBRID / MEM: 14.2MB
           </div>
        </div>

      </div>
    </motion.section>
  )
}
