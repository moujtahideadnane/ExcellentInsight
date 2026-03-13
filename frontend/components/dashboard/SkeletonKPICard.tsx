"use client"

import React from 'react'
import { motion } from 'framer-motion'

export default function SkeletonKPICard() {
  return (
    <div className="relative p-5 rounded-[6px] bg-[#0A0A0A] border border-[#333333] overflow-hidden">
      <div className="flex justify-between items-start mb-4">
        <div className="space-y-2">
          {/* Title skeleton */}
          <motion.div 
            animate={{ opacity: [0.3, 0.6, 0.3] }}
            transition={{ duration: 1.5, repeat: Infinity, ease: "easeInOut" }}
            className="h-3 w-24 bg-[#222222] rounded-[2px]" 
          />
          {/* Subtitle skeleton */}
          <motion.div 
            animate={{ opacity: [0.3, 0.6, 0.3] }}
            transition={{ duration: 1.5, repeat: Infinity, ease: "easeInOut", delay: 0.2 }}
            className="h-2 w-16 bg-[#222222] rounded-[2px]" 
          />
        </div>
        {/* Icon skeleton */}
        <motion.div 
          animate={{ opacity: [0.3, 0.6, 0.3] }}
          transition={{ duration: 1.5, repeat: Infinity, ease: "easeInOut", delay: 0.4 }}
          className="h-8 w-8 bg-[#222222] rounded-[4px]" 
        />
      </div>

      {/* Main value skeleton */}
      <div className="flex items-baseline gap-2 mb-6">
        <motion.div 
          animate={{ opacity: [0.3, 0.6, 0.3] }}
          transition={{ duration: 1.5, repeat: Infinity, ease: "easeInOut", delay: 0.6 }}
          className="h-10 w-32 bg-[#222222] rounded-[4px]" 
        />
        <motion.div 
          animate={{ opacity: [0.3, 0.6, 0.3] }}
          transition={{ duration: 1.5, repeat: Infinity, ease: "easeInOut", delay: 0.8 }}
          className="h-4 w-12 bg-[#222222] rounded-[2px]" 
        />
      </div>

      {/* Footer skeletons */}
      <div className="flex gap-3">
        <motion.div 
          animate={{ opacity: [0.3, 0.6, 0.3] }}
          transition={{ duration: 1.5, repeat: Infinity, ease: "easeInOut", delay: 1.0 }}
          className="h-4 w-20 bg-[#222222] rounded-[2px]" 
        />
        <motion.div 
          animate={{ opacity: [0.3, 0.6, 0.3] }}
          transition={{ duration: 1.5, repeat: Infinity, ease: "easeInOut", delay: 1.2 }}
          className="h-4 w-24 bg-[#222222] rounded-[2px]" 
        />
      </div>
      
      {/* Subtle shimmer effect */}
      <motion.div
        className="absolute inset-0 bg-gradient-to-r from-transparent via-white/[0.03] to-transparent -translate-x-full"
        animate={{ x: ["100%", "-100%"] }}
        transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
      />
    </div>
  )
}
