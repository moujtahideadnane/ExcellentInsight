"use client"

import React from 'react'
import { Link2 } from 'lucide-react'
import { Relationship, Join } from '@/types/dashboard'

interface ConnectivitySectionProps {
  relationships?: Relationship[]
  joins?: Join[]
}

export default function ConnectivitySection({ relationships = [], joins = [] }: ConnectivitySectionProps) {
  if (relationships.length === 0 && joins.length === 0) return null

  return (
    <section className="no-print mt-12">
      <div className="flex items-center gap-4 mb-6">
        <h2 className="text-[10px] font-mono uppercase tracking-widest text-ve-muted whitespace-nowrap">Schema Dependencies</h2>
        <div className="flex-1 h-px bg-ve-border" />
      </div>
      <div className="flex flex-wrap gap-3">
        {relationships.map((rel, idx) => (
          <div key={`rel-${idx}`} className="flex items-center gap-4 px-4 py-3 rounded-[4px] bg-ve-bg border border-ve-border hover:border-ve-muted transition-colors">
            <div className="text-right">
              <div className="text-[9px] font-mono text-ve-muted uppercase tracking-widest mb-0.5">{rel.from_sheet}</div>
              <div className="text-[12px] font-mono text-ve-text">{rel.from_col}</div>
            </div>
            <div className="flex items-center gap-1 text-ve-border">
              <div className="h-px w-4 bg-current" />
              <div className="h-1.5 w-1.5 rounded-[1px] bg-ve-btn-primary" />
              <div className="h-px w-4 bg-current" />
            </div>
            <div>
              <div className="text-[9px] font-mono text-ve-muted uppercase tracking-widest mb-0.5">{rel.to_sheet}</div>
              <div className="text-[12px] font-mono text-ve-text">{rel.to_col}</div>
            </div>
          </div>
        ))}
        {joins.map((join, idx) => (
          <div key={`join-${idx}`} className="flex items-center gap-3 px-4 py-3 rounded-[4px] bg-ve-surface border border-ve-blue-border border-dashed">
            <Link2 className="h-3.5 w-3.5 text-ve-blue" />
            <div>
              <div className="text-[9px] font-mono text-ve-blue uppercase tracking-widest mb-0.5">Runtime Link</div>
              <div className="text-[12px] font-mono text-ve-text">{join.left_sheet} × {join.right_sheet}</div>
            </div>
          </div>
        ))}
      </div>
    </section>
  )
}
