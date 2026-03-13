"use client"

import React, { useState } from 'react'
import { Share2, Link2, Copy, Check, X, Loader2, Clock, Eye } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import { toast } from 'sonner'
import api from '@/lib/api'

interface ShareButtonProps {
  jobId: string
}

interface ShareData {
  id: string
  share_token: string
  share_url: string
  expires_at: string | null
  is_active: boolean
  view_count: number
  created_at: string
}

export default function ShareButton({ jobId }: ShareButtonProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [shares, setShares] = useState<ShareData[]>([])
  const [copiedToken, setCopiedToken] = useState<string | null>(null)
  const [origin, setOrigin] = useState('')

  React.useEffect(() => {
    setOrigin(window.location.origin)
  }, [])

  const fetchShares = async () => {
    try {
      setIsLoading(true)
      const response = await api.get(`/shares/dashboard/${jobId}`)
      setShares(response.data.shares || [])
    } catch (error) {
      console.error('Failed to fetch shares:', error)
      toast.error('Failed to load share links')
    } finally {
      setIsLoading(false)
    }
  }

  const handleOpen = async () => {
    setIsOpen(true)
    await fetchShares()
  }

  const createShare = async (expiresInDays?: number) => {
    try {
      setIsLoading(true)
      const response = await api.post(`/shares/dashboard/${jobId}`, {
        expires_in_days: expiresInDays || null,
      })

      const newShare = response.data
      setShares([newShare, ...shares])

      // Auto-copy the new link
      copyToClipboard(newShare.share_token, newShare.share_url)

      toast.success('Share link created!')
    } catch (error) {
      console.error('Failed to create share:', error)
      toast.error('Failed to create share link')
    } finally {
      setIsLoading(false)
    }
  }

  const revokeShare = async (shareId: string) => {
    try {
      await api.delete(`/shares/${shareId}`)
      setShares(shares.filter(s => s.id !== shareId))
      toast.success('Share link revoked')
    } catch (error) {
      console.error('Failed to revoke share:', error)
      toast.error('Failed to revoke share link')
    }
  }

  const copyToClipboard = async (token: string, shareUrl: string) => {
    const fullUrl = `${origin}${shareUrl}`
    try {
      await navigator.clipboard.writeText(fullUrl)
      setCopiedToken(token)
      setTimeout(() => setCopiedToken(null), 2000)
      toast.success('Link copied to clipboard!')
    } catch (err) {
      console.error('Clipboard error:', err)
      toast.error('Failed to copy link. Please copy it manually.')
    }
  }

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    })
  }

  return (
    <>
      <button
        onClick={handleOpen}
        className="flex items-center justify-center h-8 w-8 rounded-[4px] border border-ve-border hover:bg-ve-surface transition-colors text-ve-muted hover:text-ve-text"
        title="Share dashboard"
        aria-label="Share dashboard"
      >
        <Share2 className="h-4 w-4" />
      </button>

      <AnimatePresence>
        {isOpen && (
          <>
            {/* Backdrop */}
            <div
              className="fixed inset-0 bg-black/60 z-40 backdrop-blur-sm"
              onClick={() => setIsOpen(false)}
            />

            {/* Modal */}
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              transition={{ duration: 0.2 }}
              className="fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-full max-w-lg bg-ve-surface border border-ve-border rounded-[6px] shadow-2xl z-50 max-h-[80vh] overflow-hidden flex flex-col"
            >
              {/* Header */}
              <div className="flex items-center justify-between p-5 border-b border-ve-border">
                <div className="flex items-center gap-3">
                  <div className="h-8 w-8 rounded-[4px] bg-ve-blue-muted border border-ve-blue-border flex items-center justify-center">
                    <Link2 className="h-4 w-4 text-ve-blue" />
                  </div>
                  <div>
                    <h2 className="text-[14px] font-semibold text-ve-text">Share Dashboard</h2>
                    <p className="text-[10px] text-ve-muted font-mono">Create and manage shareable links</p>
                  </div>
                </div>
                <button
                  onClick={() => setIsOpen(false)}
                  className="h-6 w-6 rounded-[4px] hover:bg-ve-border-subtle flex items-center justify-center text-ve-muted hover:text-ve-text transition-colors"
                  aria-label="Close dialog"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>

              {/* Content */}
              <div className="flex-1 overflow-y-auto p-5 space-y-4">
                {/* Create new share buttons */}
                <div className="space-y-2">
                  <label className="text-[10px] font-mono uppercase tracking-widest text-ve-muted">
                    Create New Link
                  </label>
                  <div className="flex gap-2">
                    <button
                      onClick={() => createShare()}
                      disabled={isLoading}
                      className="flex-1 px-3 py-2 rounded-[4px] bg-ve-blue hover:bg-blue-700 text-white text-[11px] font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {isLoading ? (
                        <Loader2 className="h-3.5 w-3.5 animate-spin mx-auto" />
                      ) : (
                        'Never Expires'
                      )}
                    </button>
                    <button
                      onClick={() => createShare(7)}
                      disabled={isLoading}
                      className="flex-1 px-3 py-2 rounded-[4px] bg-ve-border-subtle hover:bg-ve-border text-ve-text text-[11px] font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      7 Days
                    </button>
                    <button
                      onClick={() => createShare(30)}
                      disabled={isLoading}
                      className="flex-1 px-3 py-2 rounded-[4px] bg-ve-border-subtle hover:bg-ve-border text-ve-text text-[11px] font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      30 Days
                    </button>
                  </div>
                </div>

                {/* Existing shares */}
                {shares.length > 0 && (
                  <div className="space-y-2">
                    <label className="text-[10px] font-mono uppercase tracking-widest text-ve-muted">
                      Active Links ({shares.filter(s => s.is_active).length})
                    </label>
                    <div className="space-y-2">
                      {shares.map((share) => (
                        <div
                          key={share.id}
                          className={`p-3 rounded-[4px] border ${
                            share.is_active
                              ? 'bg-ve-skeleton border-ve-border'
                              : 'bg-red-950 border-ve-error-border opacity-60'
                          }`}
                        >
                          <div className="flex items-start justify-between gap-2 mb-2">
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center gap-2 mb-1">
                                <span className={`px-1.5 py-0.5 rounded-[2px] text-[8px] font-mono uppercase tracking-wider ${
                                  share.is_active
                                    ? 'bg-emerald-500/10 text-emerald-500 border border-emerald-500/30'
                                    : 'bg-ve-error/10 text-ve-error border border-ve-error/30'
                                }`}>
                                  {share.is_active ? 'Active' : 'Revoked'}
                                </span>
                                {share.expires_at && (
                                  <span className="flex items-center gap-1 text-[9px] text-ve-muted">
                                    <Clock className="h-3 w-3" />
                                    Expires {formatDate(share.expires_at)}
                                  </span>
                                )}
                              </div>
                              <div className="flex items-center gap-1 text-[9px] text-ve-muted">
                                <Eye className="h-3 w-3" />
                                {share.view_count} views • Created {formatDate(share.created_at)}
                              </div>
                            </div>

                            {share.is_active && (
                              <div className="flex gap-1">
                                <button
                                  onClick={() => copyToClipboard(share.share_token, share.share_url)}
                                  className="h-7 w-7 rounded-[4px] bg-ve-border-subtle hover:bg-ve-border flex items-center justify-center text-ve-text transition-colors"
                                  title="Copy link"
                                >
                                  {copiedToken === share.share_token ? (
                                    <Check className="h-3.5 w-3.5 text-emerald-500" />
                                  ) : (
                                    <Copy className="h-3.5 w-3.5" />
                                  )}
                                </button>
                                <button
                                  onClick={() => revokeShare(share.id)}
                                  className="h-7 w-7 rounded-[4px] bg-ve-error-bg hover:bg-red-950 border border-ve-error-border hover:border-ve-error flex items-center justify-center text-ve-error transition-colors"
                                  title="Revoke link"
                                >
                                  <X className="h-3.5 w-3.5" />
                                </button>
                              </div>
                            )}
                          </div>

                          {share.is_active && (
                            <div className="mt-2 p-2 rounded-[4px] bg-ve-bg border border-ve-border">
                              <code className="text-[9px] text-ve-muted font-mono break-all">
                                {origin}{share.share_url}
                              </code>
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {shares.length === 0 && !isLoading && (
                  <div className="py-8 text-center">
                    <Link2 className="h-8 w-8 mx-auto mb-2 text-ve-border" />
                    <p className="text-[11px] text-ve-muted font-mono">No share links yet</p>
                    <p className="text-[9px] text-ve-dimmed font-mono mt-1">Create one to get started</p>
                  </div>
                )}
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </>
  )
}
