export default function JobsLoading() {
  return (
    <div className="p-6 md:p-10 space-y-4 animate-pulse">
      {/* Header skeleton */}
      <div className="flex items-center justify-between mb-8">
        <div className="space-y-2">
          <div className="h-8 w-36 bg-slate-100 rounded-full" />
          <div className="h-4 w-56 bg-slate-100 rounded-full" />
        </div>
        <div className="h-10 w-32 bg-slate-100 rounded-2xl" />
      </div>

      {/* Job rows skeleton */}
      {[1, 2, 3, 4, 5].map((i) => (
        <div
          key={i}
          className="card-elevated rounded-2xl p-5 flex items-center gap-5"
          style={{ opacity: 1 - i * 0.12 }}
        >
          <div className="h-12 w-12 rounded-xl bg-slate-100 shrink-0" />
          <div className="flex-1 space-y-2">
            <div className="h-5 w-48 bg-slate-100 rounded-full" />
            <div className="h-3.5 w-32 bg-slate-50 rounded-full" />
          </div>
          <div className="h-6 w-16 bg-slate-100 rounded-full" />
          <div className="h-8 w-24 bg-slate-100 rounded-xl" />
        </div>
      ))}
    </div>
  )
}
