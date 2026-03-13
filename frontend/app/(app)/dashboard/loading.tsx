"use client"

import React from 'react'
import { motion } from 'framer-motion'
import { Terminal } from 'lucide-react'

export default function DashboardLoading() {
  return (
    <div className="flex-1 flex flex-col items-center justify-center py-20 px-4 bg-ve-bg">
      {/* Upload zone skeleton */}
      <div className="w-full max-w-2xl space-y-12">
        <div className="space-y-4">
          <div className="flex items-center justify-center gap-2 mb-6">
            <div className="h-8 w-8 rounded-[4px] bg-ve-surface border border-ve-border flex items-center justify-center">
              <Terminal className="h-4 w-4 text-ve-muted" />
            </div>
            <motion.div 
              animate={{ opacity: [0.3, 0.6, 0.3] }}
              transition={{ duration: 1.5, repeat: Infinity }}
              className="h-4 w-32 bg-ve-surface rounded-[2px]" 
            />
          </div>
          <div className="h-[320px] rounded-[6px] border border-dashed border-ve-border bg-ve-skeleton flex flex-col items-center justify-center gap-6 relative overflow-hidden">
             <motion.div 
               animate={{ scale: [0.95, 1.05, 0.95], opacity: [0.3, 0.6, 0.3] }}
               transition={{ duration: 2, repeat: Infinity }}
               className="h-16 w-16 rounded-full bg-ve-surface border border-ve-border" 
             />
             <div className="space-y-3 text-center px-6">
               <motion.div 
                 animate={{ opacity: [0.3, 0.6, 0.3] }}
                 transition={{ duration: 1.5, repeat: Infinity, delay: 0.2 }}
                 className="h-5 w-64 bg-ve-surface rounded-[2px] mx-auto" 
               />
               <motion.div 
                 animate={{ opacity: [0.3, 0.6, 0.3] }}
                 transition={{ duration: 1.5, repeat: Infinity, delay: 0.4 }}
                 className="h-3 w-48 bg-ve-surface rounded-[2px] mx-auto" 
               />
             </div>
             {/* Shimmer */}
             <motion.div
               className="absolute inset-0 bg-gradient-to-r from-transparent via-white/[0.02] to-transparent -translate-x-full"
               animate={{ x: ["100%", "-100%"] }}
               transition={{ duration: 3, repeat: Infinity, ease: "linear" }}
             />
          </div>
        </div>

        {/* Feature chips skeleton */}
        <div className="flex flex-wrap justify-center gap-4">
          {[1, 2, 3, 4].map((i) => (
            <motion.div 
              key={i} 
              animate={{ opacity: [0.2, 0.4, 0.2] }}
              transition={{ duration: 1.5, repeat: Infinity, delay: i * 0.1 }}
              className="h-9 w-32 bg-ve-surface border border-ve-border rounded-[4px]" 
            />
          ))}
        </div>
      </div>
    </div>
  )
}
