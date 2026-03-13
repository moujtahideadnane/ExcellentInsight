// REFACTOR: [jobs-loading-skeleton]
export default function JobsLoading() {
  return (
    <div className="p-4 sm:p-6 lg:p-8 max-w-7xl w-full min-h-full">
      <div className="flex flex-col items-start gap-6 w-full animate-pulse">

        {/* Header skeleton — mirrors the actual page header */}
        <div className="mb-8 space-y-3">
          <div className="h-3 w-36 bg-[var(--bg-surface)] rounded-[2px]" />
          <div className="h-10 w-64 bg-[var(--bg-surface)] rounded-[4px]" />
          <div className="h-4 w-80 bg-[var(--bg-surface)] rounded-[2px]" />
        </div>

        {/* Actions bar skeleton */}
        <div className="flex items-center justify-between w-full mb-2">
          <div className="h-5 w-28 bg-[var(--bg-surface)] rounded-[2px]" />
          <div className="h-9 w-36 bg-[var(--bg-surface)] border border-[var(--border)] rounded-[4px]" />
        </div>

        {/* Job rows skeleton — matches card layout: icon + title/subtitle + badge + arrow */}
        <div className="grid grid-cols-1 gap-3 w-full">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <div
              key={i}
              className="flex items-center justify-between p-4 rounded-[4px] bg-[var(--bg)] border border-[var(--border)]"
              style={{ opacity: 1 - i * 0.1 }}
            >
              {/* Left: icon + text block */}
              <div className="flex items-center gap-4 min-w-0 flex-1">
                {/* File icon placeholder */}
                <div className="h-8 w-8 rounded-[4px] bg-[var(--bg-surface)] border border-[var(--border)] shrink-0" />

                {/* Text lines */}
                <div className="flex-1 space-y-2">
                  <div className="flex items-center gap-3">
                    <div className="h-4 w-40 bg-[var(--bg-surface)] rounded-[2px]" />
                    <div className="h-px w-3 bg-[var(--border)]" />
                    <div className="h-3 w-16 bg-[var(--bg-surface)] rounded-[2px]" />
                  </div>
                  <div className="flex items-center gap-3">
                    <div className="h-3 w-32 bg-[var(--bg-surface)] rounded-[2px]" />
                    <div className="h-px w-3 bg-[var(--border)]" />
                    <div className="h-3 w-20 bg-[var(--bg-surface)] rounded-[2px]" />
                  </div>
                </div>
              </div>

              {/* Right: status badge + arrow */}
              <div className="flex items-center gap-4 shrink-0">
                <div className="h-5 w-16 bg-[var(--bg-surface)] border border-[var(--border)] rounded-[2px]" />
                <div className="h-4 w-4 bg-[var(--bg-surface)] rounded-[2px]" />
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
