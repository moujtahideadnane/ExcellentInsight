"use client"

import React, { useState, useEffect, useRef } from 'react'
import { motion, useInView, useAnimation } from 'framer-motion'
import { Terminal, Copy } from 'lucide-react'

const queries = {
  default: `❯ Processing: sales_report_Q4.xlsx

Extraction Phase:
- Identifying sheets and headers
- Mapping data types (Date, Currency)
- Calculating statistical distributions

Discovery Phase:
- Detecting Revenue and Margin patterns
- Identifying top performing categories
- Computing Year-over-Year growth`,
  adjusted: `❯ Processing: inventory_log.csv

Extraction Phase:
- Normalizing product SKUs
- Detecting warehouse locations
- Validating stock quantities

Discovery Phase:
- Identifying low-stock anomalies
- Mapping geographic distribution
- Calculating turnover velocity`
}

const responses = {
  default: `✨ Discovery Complete

Dashboard Configuration Generated:

1. KPI: Total Revenue
   → Target: 'Total Amount' in 'Sales'
   → Logic: SUM(Revenue)

2. KPI: Avg Margin
   → Target: 'Profit' / 'Revenue'
   → Logic: AVG(Profit_Margin)

3. Chart: Monthly Sales Growth
   → View: Bar Chart (Time-Series)

🚀 Pipeline completed in 1.8s`,
  adjusted: `✨ Discovery Complete

Dashboard Configuration Generated:

1. KPI: Stock Turnover
   → Target: 'Quantity' vs 'Date'
   → Evolution: +14.2%

2. KPI: Low Stock Alert
   → Threshold: < 50 units
   → Count: 12 SKUs flagged

3. Chart: Warehouse Distribution
   → View: Pie Chart (Categorical)

🚀 Pipeline completed in 2.1s`
}

export function EdgeTerminal() {
  const containerRef = useRef<HTMLDivElement>(null)
  const isInView = useInView(containerRef, { once: false, amount: 0.3 })
  const controls = useAnimation()
  
  const [isAdjusted, setIsAdjusted] = useState(false)
  const [responseStr, setResponseStr] = useState(responses.default)
  const [isFetching, setIsFetching] = useState(false)

  useEffect(() => {
    if (isInView) {
      controls.start({ opacity: 1, y: 0 })
    } else {
      controls.set({ opacity: 0, y: 20 })
    }
  }, [isInView, controls])

  const triggerRequest = (adjusted: boolean) => {
    if (isFetching) return
    setIsAdjusted(adjusted)
    setIsFetching(true)
    setResponseStr('') // Clear response instantly
    
    // Simulate network delay over global edge
    setTimeout(() => {
      setResponseStr(adjusted ? responses.adjusted : responses.default)
      setIsFetching(false)
    }, 600)
  }

  return (
    <motion.section 
      ref={containerRef}
      initial={{ opacity: 0, y: 20 }}
      animate={controls}
      className="py-32 px-6 md:px-12 max-w-7xl mx-auto border-t border-[#222222] relative"
    >
      <div className="mb-16 max-w-2xl">
        <div className="text-[10px] font-mono text-[#888888] py-1 px-2 border border-[#333333] rounded-[4px] w-fit mb-4">FEATURE III : AUTO-DISCOVERY</div>
        <h2 className="text-[32px] md:text-[48px] font-bold tracking-tight mb-4">Automated Data Discovery.</h2>
        <p className="text-[#888888] text-[16px] leading-relaxed">
          Upload your data and let our engine do the heavy lifting. We automatically identify key performance indicators, detect hidden patterns, and generate optimized visualizations in one click.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-px bg-[#333333] border border-[#333333] rounded-[6px] overflow-hidden relative">
        
        {/* Glowing Network Line separating panels */}
        <div className="hidden lg:block absolute left-1/2 top-0 bottom-0 w-px bg-[#333333] z-10">
           <motion.div 
             animate={{ y: ['-100%', '200%'] }} 
             transition={{ repeat: Infinity, duration: 2, ease: "linear" }}
             className="w-full h-32 bg-gradient-to-b from-transparent via-[#EDEDED] to-transparent opacity-50"
           />
        </div>

        {/* Request Pane */}
        <div className="bg-[#0A0A0A] p-6 lg:p-8 flex flex-col gap-4">
          <div className="items-center justify-between text-[#888888] text-sm font-mono border-b border-[#222222] pb-4 hidden lg:flex">
            <span className="flex items-center gap-2"><Terminal className="h-4 w-4" /> Processing Pipeline</span>
            <div className="flex gap-2">
              <button
                onClick={() => triggerRequest(false)}
                className={`px-3 py-1 text-[10px] rounded-[4px] transition-colors border ${!isAdjusted ? 'bg-[#222222] border-[#444444] text-white' : 'bg-transparent border-[#222222] text-[#888888] hover:text-white'}`}
              >
                Sales Data
              </button>
              <button
                onClick={() => triggerRequest(true)}
                className={`px-3 py-1 text-[10px] rounded-[4px] transition-colors border ${isAdjusted ? 'bg-[#222222] border-[#444444] text-white' : 'bg-transparent border-[#222222] text-[#888888] hover:text-white'}`}
              >
                Inventory
              </button>
            </div>
          </div>
          <pre className="text-[#EDEDED] text-[12px] font-mono whitespace-pre-wrap leading-loose">
            <motion.div
              key={isAdjusted ? 'b' : 'a'}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.3 }}
            >
              {isAdjusted ? queries.adjusted : queries.default}
            </motion.div>
          </pre>
        </div>

        {/* Response Pane */}
        <div className="bg-[#000000] p-6 lg:p-8 flex flex-col gap-4">
          <div className="items-center justify-between text-[#888888] text-sm font-mono border-b border-[#222222] pb-4 hidden lg:flex">
            <span className="flex items-center gap-2">System Output</span>
             {isFetching ? (
                <div className="text-[10px] text-[#F5A623] animate-pulse">SYSTEM THINKING...</div>
             ) : (
               <Copy className="h-4 w-4 cursor-pointer hover:text-white transition-colors" />
             )}
          </div>
          <pre className="text-[#888888] text-[12px] font-mono whitespace-pre-wrap leading-loose relative">
            {/* The actual response */}
            <motion.div
              key={responseStr}
              initial={{ opacity: 0, filter: 'blur(4px)' }}
              animate={{ opacity: 1, filter: 'blur(0px)' }}
              transition={{ duration: 0.4 }}
              className="text-[#EDEDED]"
            >
              {responseStr.split('\n').map((line, i) => (
                <div key={i} className={line.includes('✨') ? 'text-[#00E5FF]' : line.includes('🚀') || line.includes('⚠️') ? 'text-[#F5A623]' : ''}>
                  {line}
                </div>
              ))}
            </motion.div>
            
            {/* Syntax highlight simulation lines */}
            {isFetching && (
               <div className="absolute inset-0 flex flex-col gap-3 pt-2">
                 {[1,2,3,4,5].map(i => (
                   <motion.div 
                     key={i} 
                     className="max-w-[80%] h-3 bg-[#111111] rounded-[2px]"
                     animate={{ opacity: [0.3, 0.7, 0.3] }}
                     transition={{ repeat: Infinity, duration: 0.8, delay: i * 0.1 }}
                   />
                 ))}
               </div>
            )}
          </pre>
        </div>

      </div>
    </motion.section>
  )
}
