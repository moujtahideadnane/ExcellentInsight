"use client"

import React, { useState, useEffect, useRef } from 'react'
import { motion, useInView, useAnimation } from 'framer-motion'
import { FileText, CheckCircle2, AlertCircle } from 'lucide-react'

const rawData = `id,first_name,last_name,email,gender,ip_address,created_at,amount
1,Mabelle,Dorken,mdorken0@google.com.au,Female,203.220.198.8,2022-07-25T11:45:10Z,849.52
2,Phaedra,Vowell,pvowell1@t-online.de,Female,19.34.195.42,2023-01-12T08:22:04Z,120.00
3,Alfonso,Kuhn,akuhn2@state.gov,Male,145.89.200.1,2023-03-05T14:10:00Z,340.50
4,Correy,Brammer,cbrammer3@gizmodo.com,Male,88.134.56.23,2022-11-18T09:30:15Z,45.99
5,Dianemarie,MacGowan,dmacgowan4@psu.edu,Female,102.55.78.9,2023-05-20T16:05:40Z,999.99
6,Emmott,Burditt,eburditt5@google.cn,Male,210.15.89.44,2022-09-02T10:15:20Z,250.00`

const schemaResult = [
  { col: 'id', type: 'INT64', status: 'ok' },
  { col: 'first_name', type: 'VARCHAR', status: 'ok' },
  { col: 'last_name', type: 'VARCHAR', status: 'ok' },
  { col: 'email', type: 'VARCHAR', status: 'ok' },
  { col: 'gender', type: 'CATEGORY', status: 'ok' },
  { col: 'ip_address', type: 'INET', status: 'warn', note: 'Inferred' },
  { col: 'created_at', type: 'TIMESTAMP', status: 'ok' },
  { col: 'amount', type: 'FLOAT64', status: 'ok' },
]

export function ZeroSchemaMatrix() {
  const containerRef = useRef<HTMLDivElement>(null)
  const isInView = useInView(containerRef, { once: false, amount: 0.3 })
  const [isSynthesizing, setIsSynthesizing] = useState(false)
  const [synthesized, setSynthesized] = useState(false)
  const [logs, setLogs] = useState<string[]>([])
  const controls = useAnimation()

  useEffect(() => {
    if (!isInView) {
      // Reset if scrolled completely out of view to allow replay
      setIsSynthesizing(false)
      setSynthesized(false)
      setLogs([])
      controls.set({ opacity: 0, y: 20 })
    } else {
      controls.start({ opacity: 1, y: 0 })
    }
  }, [isInView, controls])

  const handleSynthesize = () => {
    if (isSynthesizing || synthesized) return
    setIsSynthesizing(true)

    const sequence = [
      () => setLogs(prev => [...prev, "[INFO] Uploading sales_data_Q4.xlsx..."]),
      () => setLogs(prev => [...prev, "[INFO] Reading Excel file (6 rows, 0.8KB)..."]),
      () => setLogs(prev => [...prev, "[OK]   File structure validated"]),
      () => setLogs(prev => [...prev, "[WARN] Auto-converting 'ip_address' to INET type"]),
      () => setLogs(prev => [...prev, "[OK]   AI schema detection complete in 1.2s"]),
      () => {
        setLogs(prev => [...prev, "[OK]   Detected 8 columns with data types."])
        setIsSynthesizing(false)
        setSynthesized(true)
      }
    ]

    sequence.forEach((fn, idx) => {
      setTimeout(fn, (idx + 1) * 300)
    })
  }

  return (
    <motion.section 
      ref={containerRef}
      initial={{ opacity: 0, y: 20 }}
      animate={controls}
      className="py-32 px-6 md:px-12 max-w-7xl mx-auto border-t border-[#222222] relative"
    >
      <div className="mb-16 max-w-2xl" id="features">
        <div className="text-[10px] font-mono text-[#888888] py-1 px-2 border border-[#333333] rounded-[4px] w-fit mb-4">FEATURE I : INTELLIGENT UPLOAD</div>
        <h2 className="text-[32px] md:text-[48px] font-bold tracking-tight mb-4">Zero-Schema File Upload.</h2>
        <p className="text-[#888888] text-[16px] leading-relaxed">
          Upload any Excel or CSV file without configuration. Our AI engine automatically detects column types, relationships between sheets, and data structures in seconds.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-px bg-[#333333] border border-[#333333] rounded-[6px] overflow-hidden">
        
        {/* Left: Raw Data / Terminal */}
        <div className="bg-[#000000] p-6 lg:p-8 flex flex-col gap-6 relative min-h-[400px]">
          <div className="flex items-center justify-between border-b border-[#222222] pb-4">
            <div className="flex items-center gap-2 text-[#888888] text-sm font-mono">
              <FileText className="h-4 w-4" />
              <span>sales_data_Q4.xlsx</span>
            </div>
            {!synthesized && (
              <button
                onClick={handleSynthesize}
                disabled={isSynthesizing}
                className="text-[12px] font-mono bg-white text-black px-3 py-1 rounded-[4px] hover:bg-[#CCCCCC] transition-colors disabled:opacity-50"
              >
                {isSynthesizing ? 'ANALYZING...' : 'ANALYZE FILE ->'}
              </button>
            )}
            {synthesized && (
               <div className="text-[12px] font-mono text-[#00E5FF] flex items-center gap-1">
                 <CheckCircle2 className="h-3.5 w-3.5" /> SCHEMA DETECTED
               </div>
            )}
          </div>

          <div className="relative flex-1 overflow-hidden">
            <motion.pre 
              animate={{ opacity: synthesized ? 0.2 : 1, filter: synthesized ? 'blur(4px)' : 'blur(0px)' }}
              transition={{ duration: 0.8 }}
              className="text-[#888888] text-[11px] font-mono whitespace-pre-wrap leading-relaxed absolute inset-0"
            >
              {rawData}
            </motion.pre>

            {/* Layout Shift: The Terminal Overlay */}
            {(isSynthesizing || synthesized) && (
              <motion.div 
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="absolute inset-0 bg-black/80 backdrop-blur-sm p-4 font-mono text-[12px] flex flex-col gap-2 border border-[#333333] rounded-[4px]"
              >
                {logs.map((log, i) => (
                  <motion.div 
                    key={i}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ type: 'spring', stiffness: 400, damping: 25 }}
                    className={log.includes('[OK]') ? 'text-[#EDEDED]' : log.includes('[WARN]') ? 'text-[#F5A623]' : 'text-[#888888]'}
                  >
                    {log}
                  </motion.div>
                ))}
                {isSynthesizing && (
                  <motion.div animate={{ opacity: [1, 0] }} transition={{ repeat: Infinity, duration: 0.8 }} className="w-2 h-3 bg-[#EDEDED] mt-1" />
                )}
              </motion.div>
            )}
          </div>
        </div>

        {/* Right: The Structured Layout */}
        <div className="bg-[#050505] p-6 lg:p-8 flex flex-col gap-6 min-h-[400px]">
           <div className="text-[#888888] text-sm font-mono border-b border-[#222222] pb-4">
             Auto-Detected Schema
           </div>

           <div className="flex-1 flex flex-col justify-center">
             {!synthesized ? (
               <div className="text-center text-[#444444] font-mono text-[12px]">
                 WAITING FOR FILE UPLOAD...
               </div>
             ) : (
               <div className="flex flex-col gap-2">
                 {schemaResult.map((col, i) => (
                   <motion.div 
                     key={col.col}
                     initial={{ opacity: 0, x: 20 }}
                     animate={{ opacity: 1, x: 0 }}
                     transition={{ delay: i * 0.05, type: 'spring', stiffness: 400, damping: 25 }}
                     className="flex items-center justify-between p-2 border border-[#222222] bg-[#111111] rounded-[4px] group hover:border-[#444444] transition-colors"
                   >
                      <span className="font-mono text-[12px] text-[#EDEDED] font-medium">{col.col}</span>
                      <div className="flex items-center gap-3">
                        {col.status === 'warn' && <AlertCircle className="h-3 w-3 text-[#F5A623]" />}
                        <span className="font-mono text-[10px] text-[#888888] bg-[#222222] px-2 py-0.5 rounded-[2px]">{col.type}</span>
                      </div>
                   </motion.div>
                 ))}
               </div>
             )}
           </div>
        </div>

      </div>
    </motion.section>
  )
}
