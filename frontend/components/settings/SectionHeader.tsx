import React from 'react'

export function SectionHeader({ title, subtitle }: { title: string; subtitle: string }) {
  return (
    <div className="mb-8 border-b border-ve-border pb-6">
      <h2 className="text-[20px] font-semibold tracking-tight text-ve-text">{title}</h2>
      <p className="text-[12px] font-mono text-ve-muted mt-2">{subtitle}</p>
    </div>
  )
}
