"use client"

import React from 'react'
import { Terminal, ShieldCheck, Zap, Server } from 'lucide-react'
import { motion } from 'framer-motion'
import Link from 'next/link'
import Image from 'next/image'
import PageTransition from '@/components/layout/PageTransition'

export default function AuthLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <div className="min-h-screen w-full flex relative overflow-hidden bg-[#000000]">
      {/* Left panel | branding */}
      <div className="hidden lg:flex max-w-[480px] w-full flex-col justify-between p-12 relative overflow-hidden border-r border-[#333333] bg-[#111111]">
        
        {/* Vercel Edge subtle grid background instead of glowing orbs */}
        <div className="absolute inset-0 pointer-events-none opacity-20"
             style={{ backgroundImage: 'radial-gradient(circle at 2px 2px, #333333 1px, transparent 0)', backgroundSize: '32px 32px' }} />

        {/* Logo */}
        <div className="relative z-10">
          <Link href="/" className="flex items-center gap-3 decoration-0 group">
            <div className="h-8 w-8 relative rounded-[4px] flex items-center justify-center bg-[#EDEDED] group-hover:bg-[#FFFFFF] transition-colors overflow-hidden">
               <Image src="/logo3.png" alt="ExcellentInsight Logo" fill className="object-contain p-1" />
            </div>
            <span className="font-semibold text-[16px] tracking-tight text-[#EDEDED] group-hover:text-[#FFFFFF]">
              ExcellentInsight
            </span>
          </Link>
        </div>

        {/* Central message */}
        <div className="relative z-10">
          <div className="mb-12">
            <div className="inline-flex items-center gap-2 px-2 py-1 rounded-[4px] bg-[#000000] border border-[#333333] mb-6">
              <Terminal className="h-3 w-3 text-[#888888]" />
              <span className="text-[10px] font-mono text-[#888888]">v2.4.0-stable</span>
            </div>
            <h2 className="text-[40px] font-bold text-[#EDEDED] leading-[1.1] tracking-tighter mb-4">
              Access the <br />
              <span className="text-[#888888]">intelligence engine.</span>
            </h2>
            <p className="text-[14px] leading-relaxed text-[#888888] max-w-sm">
              Authenticate to deploy, manage, and scale your data analysis pipelines securely.
            </p>
          </div>

          {/* Feature list */}
          <div className="space-y-4 mb-12">
            {[
              { icon: Zap, text: 'Instant inferencing at the Edge' },
              { icon: Server, text: 'Distributed WebGL rendering' },
              { icon: ShieldCheck, text: 'SOC2 Type II strict isolation' },
            ].map((item, i) => (
               <motion.div
                key={i}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.2 + (i * 0.1) }}
                className="flex items-center gap-3 text-[#888888] text-[13px] font-medium"
              >
                <div className="h-5 w-5 rounded-[4px] border border-[#333333] bg-[#000000] flex items-center justify-center shrink-0">
                  <item.icon className="h-3 w-3 text-[#EDEDED]" />
                </div>
                {item.text}
              </motion.div>
            ))}
          </div>

          {/* Testimonial mini - Minimalist */}
          <div className="p-4 rounded-[6px] bg-[#000000] border border-[#333333]">
            <p className="text-[12px] text-[#888888] leading-relaxed mb-3">
              &quot;The latency from raw CSV drop to a queryable GraphQL endpoint with live charts is essentially zero. It&apos;s the standard.&quot;
            </p>
            <div className="flex items-center gap-2">
              <div className="h-6 w-6 rounded-[2px] bg-[#333333]" />
              <span className="text-[10px] font-mono text-[#888888] uppercase tracking-wider">Enterprise Customer</span>
            </div>
          </div>
        </div>

        {/* Bottom */}
        <div className="relative z-10 text-[10px] font-mono uppercase tracking-widest text-[#333333]">
           REGION: GLOBAL_EDGE | LATENCY: {'<'}50ms
        </div>
      </div>

      {/* Right panel | form content */}
      <div className="flex-1 flex flex-col relative bg-[#000000]">
        {/* Mobile Header */}
        <div className="lg:hidden p-6 flex justify-between items-center border-b border-[#333333]">
          <Link href="/" className="flex items-center gap-2">
            <div className="h-6 w-6 relative rounded-[4px] bg-[#EDEDED] flex items-center justify-center overflow-hidden">
              <Image src="/logo3.png" alt="ExcellentInsight Logo" fill className="object-contain p-0.5" />
            </div>
            <span className="font-semibold text-[14px] text-[#EDEDED] tracking-tight">ExcellentInsight</span>
          </Link>
        </div>

        <div className="flex-1 flex flex-col items-center justify-center p-4 sm:p-6 lg:p-12 w-full">
          <div className="relative z-10 w-full max-w-[400px]">
            <PageTransition>
              {children}
            </PageTransition>
          </div>
        </div>
      </div>
    </div>
  )
}
