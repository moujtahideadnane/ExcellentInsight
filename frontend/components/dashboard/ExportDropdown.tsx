"use client"

import React, { useState } from 'react'
import { Download, FileText, Table, Loader2, ChevronDown } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import { toast } from 'sonner'
import api from '@/lib/api'

interface ExportDropdownProps {
  jobId: string
}

type ExportFormat = 'pdf' | 'excel'

export default function ExportDropdown({ jobId }: ExportDropdownProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [isExporting, setIsExporting] = useState(false)

  const handleExport = async (format: ExportFormat) => {
    setIsExporting(true)
    setIsOpen(false)

    try {
      const endpoint = format === 'pdf' ? `/dashboard/${jobId}/export/pdf` : `/dashboard/${jobId}/export/excel`
      const extension = format === 'pdf' ? 'pdf' : 'xlsx'

      // Use the authorized api instance with responseType 'blob'
      const response = await api.get(endpoint, {
        responseType: 'blob'
      })

      // Get blob from response (it's already a blob because of responseType)
      const blob = response.data

      // Create download link
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `dashboard_${jobId}.${extension}`
      document.body.appendChild(link)
      link.click()

      // Cleanup
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)

      toast.success(`Dashboard exported as ${format.toUpperCase()}`)
    } catch (error) {
      console.error('Export failed:', error)
      toast.error(`Failed to export dashboard as ${format.toUpperCase()}`)
    } finally {
      setIsExporting(false)
    }
  }

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        disabled={isExporting}
        className="flex items-center gap-2 h-8 px-3 rounded-[4px] bg-ve-btn-primary text-ve-btn-text text-[11px] font-medium hover:bg-ve-btn-hover transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        title="Export dashboard"
      >
        {isExporting ? (
          <>
            <Loader2 className="h-3.5 w-3.5 animate-spin" />
            Exporting...
          </>
        ) : (
          <>
            <Download className="h-3.5 w-3.5" />
            Export
            <ChevronDown className="h-3 w-3" />
          </>
        )}
      </button>

      <AnimatePresence>
        {isOpen && !isExporting && (
          <>
            {/* Backdrop to close dropdown */}
            <div
              className="fixed inset-0 z-10"
              onClick={() => setIsOpen(false)}
            />

            {/* Dropdown menu */}
            <motion.div
              initial={{ opacity: 0, y: -8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              transition={{ duration: 0.15 }}
              className="absolute right-0 mt-2 w-48 bg-ve-surface border border-ve-border rounded-[4px] shadow-lg overflow-hidden z-20"
            >
              <div className="py-1">
                <button
                  onClick={() => handleExport('pdf')}
                  className="w-full flex items-center gap-3 px-4 py-2.5 text-[11px] text-ve-text hover:bg-ve-border-subtle transition-colors"
                >
                  <FileText className="h-4 w-4 text-ve-error" />
                  <div className="flex flex-col items-start">
                    <span className="font-medium">Export as PDF</span>
                    <span className="text-[9px] text-ve-muted font-mono">Portable Document</span>
                  </div>
                </button>

                <div className="h-px bg-ve-border my-1" />

                <button
                  onClick={() => handleExport('excel')}
                  className="w-full flex items-center gap-3 px-4 py-2.5 text-[11px] text-ve-text hover:bg-ve-border-subtle transition-colors"
                >
                  <Table className="h-4 w-4 text-emerald-500" />
                  <div className="flex flex-col items-start">
                    <span className="font-medium">Export as Excel</span>
                    <span className="text-[9px] text-ve-muted font-mono">Spreadsheet Format</span>
                  </div>
                </button>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </div>
  )
}
