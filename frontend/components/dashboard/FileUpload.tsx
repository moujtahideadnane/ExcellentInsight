"use client"

import React, { useState, useCallback } from 'react'
import { Upload, File as FileIcon, X, AlertCircle, Loader2, Database } from 'lucide-react'
import { cn } from '@/lib/utils'
import api from '@/lib/api'
import { motion, AnimatePresence } from 'framer-motion'

interface FileUploadProps {
  onUploadSuccess: (jobId: string) => void
}

export default function FileUpload({ onUploadSuccess }: FileUploadProps) {
  const [isDragging, setIsDragging] = useState(false)
  const [file, setFile] = useState<File | null>(null)
  const [isUploading, setIsUploading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const onDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }, [])

  const onDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
  }, [])

  const handleFile = (selectedFile: File) => {
    const validExtensions = ['.xlsx', '.xls', '.csv']
    const extension = selectedFile.name.substring(selectedFile.name.lastIndexOf('.')).toLowerCase()

    if (!validExtensions.includes(extension)) {
      setError("ERR_FORMAT_INVALID: Supported types match [.xlsx, .xls, .csv]")
      return
    }

    if (selectedFile.size > 100 * 1024 * 1024) {
      setError("ERR_SIZE_EXCEEDED: Maximum allocation is 100MB per chunk.")
      return
    }

    setFile(selectedFile)
    setError(null)
  }

  const onDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
    const droppedFile = e.dataTransfer.files[0]
    if (droppedFile) handleFile(droppedFile)
  }, [])

  const onFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0]
    if (selectedFile) handleFile(selectedFile)
  }

  const uploadFile = async () => {
    if (!file) return
    setIsUploading(true)
    setError(null)

    const formData = new FormData()
    formData.append('file', file)

    try {
      const response = await api.post('/upload', formData)
      onUploadSuccess(response.data.job_id)
    } catch (err: unknown) {
      const e = err as { response?: { data?: { detail?: string } } }
      setError(e?.response?.data?.detail ?? "ERR_NETWORK: Connection refused or timed out.")
    } finally {
      setIsUploading(false)
    }
  }

  const fileSizeMb = file ? (file.size / 1024 / 1024).toFixed(2) : '0'

  return (
    <div className="w-full">
      <AnimatePresence mode="wait">
        {!file ? (
          <motion.div
            key="dropzone"
            initial={{ opacity: 0, y: 5 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.99 }}
            transition={{ duration: 0.2 }}
            onDragOver={onDragOver}
            onDragLeave={onDragLeave}
            onDrop={onDrop}
            onClick={() => document.getElementById('fileInput')?.click()}
            className={cn(
              "p-12 flex flex-col items-center justify-center text-center cursor-pointer transition-colors border border-dashed rounded-[6px] relative overflow-hidden group",
              isDragging 
                ? "border-ve-text bg-ve-surface" 
                : "border-ve-border bg-ve-bg hover:bg-ve-surface hover:border-ve-muted"
            )}
          >
            <input
              id="fileInput"
              type="file"
              className="hidden"
              accept=".xlsx,.xls,.csv"
              onChange={onFileChange}
            />

            <div className="mb-6 flex items-center justify-center transition-transform group-hover:scale-[1.02]">
              <Database className={cn("h-8 w-8 transition-colors duration-200", isDragging ? "text-ve-text" : "text-ve-muted")} />
            </div>

            <h3 className="text-[16px] font-semibold tracking-tight text-ve-text mb-2">
              {isDragging ? 'Initialize ingestion.' : 'Deploy dataset'}
            </h3>
            <p className="text-[13px] text-ve-muted font-medium max-w-sm">
              Drag and drop your schema or <span className="text-ve-text underline underline-offset-4 cursor-pointer">browse local registry</span>
            </p>
            
            <div className="mt-8 flex items-center justify-center gap-2">
              {['.xlsx', '.csv', '.xls'].map(ext => (
                <span key={ext} className="px-2 py-0.5 rounded-[4px] bg-ve-surface border border-ve-border text-[10px] font-mono text-ve-muted">
                  {ext}
                </span>
              ))}
            </div>
            
            {/* Vercel Edge corner accents */}
            <div className="absolute top-0 left-0 w-2 h-2 border-t border-l border-ve-border opacity-50" />
            <div className="absolute top-0 right-0 w-2 h-2 border-t border-r border-ve-border opacity-50" />
            <div className="absolute bottom-0 left-0 w-2 h-2 border-b border-l border-ve-border opacity-50" />
            <div className="absolute bottom-0 right-0 w-2 h-2 border-b border-r border-ve-border opacity-50" />
          </motion.div>
        ) : (
          <motion.div
            key="file-selected"
            initial={{ opacity: 0, y: 5 }}
            animate={{ opacity: 1, y: 0 }}
            className="rounded-[6px] border border-ve-border bg-ve-surface p-4 flex items-center justify-between gap-4"
          >
            <div className="flex items-center gap-4 min-w-0">
              <div className="h-10 w-10 shrink-0 bg-ve-elevated border border-ve-border rounded-[4px] flex items-center justify-center">
                <FileIcon className="h-5 w-5 text-ve-text" />
              </div>
              <div className="min-w-0 text-left">
                <p className="text-[14px] font-semibold text-ve-text truncate">{file.name}</p>
                <p className="text-[12px] font-mono text-ve-muted mt-0.5">{fileSizeMb} MB / READY_STATE</p>
              </div>
            </div>

            <div className="flex items-center gap-3 shrink-0">
              <button
                onClick={() => setFile(null)}
                disabled={isUploading}
                className="h-8 w-8 flex items-center justify-center rounded-[4px] border border-ve-border text-ve-muted hover:text-ve-text hover:bg-ve-elevated transition-colors disabled:opacity-50"
              >
                <X className="h-4 w-4" />
              </button>
              <button
                onClick={uploadFile}
                disabled={isUploading}
                className="h-8 px-4 rounded-[4px] bg-ve-btn-primary text-ve-btn-text text-[13px] font-medium hover:bg-ve-btn-hover transition-colors flex items-center gap-2 disabled:opacity-70"
              >
                {isUploading ? (
                  <>
                    <Loader2 className="h-3.5 w-3.5 animate-spin" />
                    <span>Processing</span>
                  </>
                ) : (
                  <>
                    <Upload className="h-3.5 w-3.5" />
                    <span>Deploy</span>
                  </>
                )}
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      <AnimatePresence>
        {error && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="overflow-hidden mt-4"
          >
            <div className="flex items-center gap-3 px-4 py-3 rounded-[4px] bg-ve-error-bg border border-ve-error-border">
              <AlertCircle className="h-4 w-4 shrink-0 text-ve-error" />
              <p className="text-[13px] font-mono text-ve-error">{error}</p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
