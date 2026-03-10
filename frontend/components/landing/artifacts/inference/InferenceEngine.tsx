"use client"

import React, { useState, useEffect, useRef } from 'react'
import { motion, useInView, useAnimation } from 'framer-motion'
import { BrainCircuit, Target, Sparkles } from 'lucide-react'

// Lightweight seeded random
function seededRandom(seed: number) {
  const x = Math.sin(seed) * 10000;
  return x - Math.floor(x);
}

// Generate a cluster of data points
function generateCluster(cx: number, cy: number, count: number, spread: number, isAnomaly = false, seedOffset = 0) {
  const points = []
  for (let i = 0; i < count; i++) {
    const angle = seededRandom(i + seedOffset) * Math.PI * 2
    const distance = Math.sqrt(seededRandom(i + seedOffset + 1000)) * spread
    const x = cx + Math.cos(angle) * distance
    const y = cy + Math.sin(angle) * distance
    points.push({ x: Number(x.toFixed(2)), y: Number(y.toFixed(2)), isAnomaly })
  }
  return points
}

const normalPoints = [
  ...generateCluster(20, 30, 40, 15, false, 100),
  ...generateCluster(70, 40, 50, 20, false, 200),
  ...generateCluster(40, 70, 30, 15, false, 300),
  ...generateCluster(85, 80, 40, 15, false, 400),
]

const anomalyPoints = generateCluster(30, 20, 25, 8, true, 500) // Tight little cluster of issues

export function InferenceEngine() {
  const containerRef = useRef<HTMLDivElement>(null)
  const isInView = useInView(containerRef, { once: false, amount: 0.3 })
  const controls = useAnimation()
  
  const [targetScanned, setTargetScanned] = useState(false)
  const [inferenceLogs, setInferenceLogs] = useState<string[]>([])
  const [insightReady, setInsightReady] = useState(false)

  useEffect(() => {
    if (isInView) {
      controls.start({ opacity: 1, y: 0 })
    } else {
      controls.set({ opacity: 0, y: 20 })
      setTargetScanned(false)
      setInferenceLogs([])
      setInsightReady(false)
    }
  }, [isInView, controls])

  const triggerScan = () => {
    if (targetScanned) return
    setTargetScanned(true)
    
    const sequence = [
      () => setInferenceLogs(prev => [...prev, "[AI] Scanning data for business metrics..."]),
      () => setInferenceLogs(prev => [...prev, "[AI] Identifying revenue, growth, and conversion patterns..."]),
      () => setInferenceLogs(prev => [...prev, "[AI] Detecting anomalies in Q4 performance..."]),
      () => setInferenceLogs(prev => [...prev, "[OK] Critical insight detected (confidence: 98.4%)"]),
      () => {
        setInsightReady(true)
      }
    ]

    sequence.forEach((fn, idx) => {
      setTimeout(fn, (idx + 1) * 600)
    })
  }

  return (
    <motion.section 
      ref={containerRef}
      initial={{ opacity: 0, y: 20 }}
      animate={controls}
      className="py-32 px-6 md:px-12 max-w-7xl mx-auto relative"
    >
      <div className="mb-16 max-w-2xl" id="use-cases">
        <div className="text-[10px] font-mono text-[#888888] py-1 px-2 border border-[#333333] rounded-[4px] w-fit mb-4">FEATURE IV : SMART KPIs</div>
        <h2 className="text-[32px] md:text-[48px] font-bold tracking-tight mb-4">Automatic KPI Detection.</h2>
        <p className="text-[#888888] text-[16px] leading-relaxed">
          Our AI doesn&apos;t just process numbers—it understands your business. Automatically detect key performance indicators, identify anomalies, and surface critical trends without manual configuration.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-px bg-[#333333] border border-[#333333] rounded-[6px] overflow-hidden relative">
        
        {/* Left: The Data Visualization */}
        <div className="bg-[#050505] p-6 lg:p-8 flex flex-col gap-4 relative min-h-[400px] lg:min-h-0">
          <div className="flex items-center justify-between text-[#888888] text-sm font-mono border-b border-[#222222] pb-4 z-10 relative">
            <span className="flex items-center gap-2"><Target className="h-4 w-4" /> Performance Data Cluster</span>
            <div className="flex items-center gap-2 text-[10px]">
              <span className="w-2 h-2 rounded-full bg-[#EDEDED]" /> Normal
              <span className="w-2 h-2 rounded-full bg-[#F5A623] ml-2" /> Anomaly
            </div>
          </div>

          <div className="flex-1 relative bg-[#000000] rounded-[4px] border border-[#222222] overflow-hidden flex items-center justify-center p-4">
            <div className="w-full h-full relative" style={{ maxWidth: '400px', maxHeight: '300px' }}>
              
              {/* Normal Data Points */}
              {normalPoints.map((p, i) => (
                <motion.div 
                  key={`n-${i}`}
                  className="absolute w-1.5 h-1.5 rounded-full bg-[#333333]"
                  style={{ left: `${p.x}%`, top: `${p.y}%` }}
                  animate={{ opacity: targetScanned ? 0.3 : 1 }}
                  transition={{ duration: 0.5 }}
                />
              ))}

              {/* Anomaly Data Points */}
              {anomalyPoints.map((p, i) => (
                <motion.div 
                  key={`a-${i}`}
                  className="absolute w-2 h-2 rounded-full bg-[#F5A623]"
                  style={{ left: `${p.x}%`, top: `${p.y}%` }}
                  animate={{ scale: targetScanned ? [1, 1.5, 1] : 1 }}
                  transition={{ repeat: targetScanned ? Infinity : 0, duration: 2, delay: i * 0.1 }}
                />
              ))}

              {/* Interaction Trigger Box */}
              <div
                className={`absolute w-[120px] h-[100px] border grid place-items-center cursor-pointer transition-all duration-300 ${targetScanned ? 'border-[#00E5FF] bg-[#00E5FF]/10 z-10' : 'border-[#444444] border-dashed hover:border-[#EDEDED] z-10'}`}
                style={{ left: '15%', top: '10%' }}
                onClick={triggerScan}
              >
                 {!targetScanned && (
                   <span className="text-[10px] font-mono bg-black/80 px-2 py-1 select-none pointer-events-none text-[#EDEDED]">ANALYZE CLUSTER</span>
                 )}
                 {targetScanned && (
                   <div className="absolute -top-6 left-0 text-[10px] font-mono text-[#00E5FF] bg-black px-1">ANALYZING...</div>
                 )}
              </div>

               {/* Scanning Laser */}
               {targetScanned && !insightReady && (
                 <motion.div 
                   animate={{ top: ['10%', '40%', '10%'] }}
                   transition={{ duration: 1.5, repeat: Infinity, ease: 'linear' }}
                   className="absolute left-[15%] w-[120px] h-px bg-[#00E5FF] shadow-[0_0_8px_#00E5FF]"
                 />
               )}
            </div>
          </div>
        </div>

        {/* Right: The Insight Stream */}
        <div className="bg-[#0A0A0A] p-6 lg:p-8 flex flex-col gap-4">
          <div className="flex items-center text-[#888888] text-sm font-mono border-b border-[#222222] pb-4">
            <span className="flex items-center gap-2"><BrainCircuit className="h-4 w-4" /> AI KPI Detection</span>
          </div>
          
          <div className="flex flex-col gap-6 relative h-full">
            {!targetScanned ? (
              <div className="absolute inset-0 flex items-center justify-center text-[#444444] font-mono text-[12px]">
                SELECT DATA CLUSTER TO ANALYZE...
              </div>
            ) : (
              <>
                <div className="flex flex-col gap-3 font-mono text-[11px] leading-relaxed relative z-10">
                  {inferenceLogs.map((log, i) => (
                    <motion.div 
                      key={i}
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      className={log.includes('[OK]') ? 'text-[#00E5FF]' : 'text-[#888888]'}
                    >
                      {log}
                    </motion.div>
                  ))}
                  {!insightReady && (
                    <motion.div animate={{ opacity: [1, 0] }} transition={{ repeat: Infinity, duration: 0.8 }} className="w-2 h-3 bg-[#EDEDED] mt-1" />
                  )}
                </div>

                {/* The Final Plain-English Insight */}
                {insightReady && (
                  <motion.div 
                    initial={{ opacity: 0, scale: 0.95, y: 10 }}
                    animate={{ opacity: 1, scale: 1, y: 0 }}
                    transition={{ type: 'spring', stiffness: 300, damping: 25 }}
                    className="mt-4 border border-[#333333] bg-[#111111] rounded-[6px] p-5 relative overflow-hidden group"
                  >
                    {/* Gloss highlight */}
                    <div className="absolute inset-0 bg-gradient-to-br from-white/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
                    
                    <div className="flex items-center gap-2 text-[#EDEDED] font-semibold text-[14px] mb-3">
                      <Sparkles className="h-4 w-4 text-[#F5A623]" /> KPI Alert Detected
                    </div>
                    <p className="text-[#888888] text-[13px] leading-relaxed">
                      This sales region shows <span className="text-white font-medium">47% lower conversion rates</span> compared to national average.
                      Analysis reveals strong correlation (0.91) with decreased customer follow-up frequency in Q4.
                    </p>

                    <div className="mt-4 pt-4 border-t border-[#222222] flex items-center justify-between">
                      <span className="text-[10px] font-mono text-[#444444]">AI CONFIDENCE: 98.4%</span>
                      <button className="text-[10px] font-mono bg-white text-black px-3 py-1.5 rounded-[4px] hover:bg-[#CCCCCC] transition-colors">
                        VIEW FULL INSIGHT
                      </button>
                    </div>
                  </motion.div>
                )}
              </>
            )}
          </div>
        </div>

      </div>
    </motion.section>
  )
}
