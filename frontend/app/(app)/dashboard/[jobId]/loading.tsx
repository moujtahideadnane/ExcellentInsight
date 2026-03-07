export default function JobDetailLoading() {
  return (
    <div className="p-6 md:p-10 space-y-8 animate-pulse">
      {/* Domain header skeleton */}
      <div className="card-elevated rounded-2xl p-6 flex items-center gap-5">
        <div className="h-14 w-14 rounded-2xl bg-slate-100" />
        <div className="space-y-2 flex-1">
          <div className="h-4 w-24 bg-slate-100 rounded-full" />
          <div className="h-7 w-48 bg-slate-100 rounded-full" />
        </div>
        <div className="flex gap-2">
          {[1, 2, 3].map((i) => <div key={i} className="h-8 w-20 bg-slate-100 rounded-xl" />)}
        </div>
      </div>

      {/* KPI grid skeleton */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="h-[220px] rounded-2xl bg-slate-100" />
        ))}
      </div>

      {/* Charts skeleton */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {[1, 2].map((i) => (
          <div key={i} className="card-elevated rounded-2xl p-6 space-y-4">
            <div className="h-5 w-36 bg-slate-100 rounded-full" />
            <div className="h-[200px] bg-slate-50 rounded-xl" />
          </div>
        ))}
      </div>

      {/* Insights skeleton */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {[1, 2, 3].map((i) => (
          <div key={i} className="h-[180px] rounded-2xl bg-slate-100" />
        ))}
      </div>
    </div>
  )
}
