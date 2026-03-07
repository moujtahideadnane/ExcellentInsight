export default function DashboardLoading() {
  return (
    <div className="flex-1 flex flex-col items-center justify-center py-20 px-4 animate-pulse">
      {/* Upload zone skeleton */}
      <div className="w-full max-w-2xl">
        <div className="h-8 w-48 bg-slate-100 rounded-full mx-auto mb-8" />
        <div className="h-[300px] rounded-[2.5rem] border-2 border-dashed border-slate-100 bg-white flex flex-col items-center justify-center gap-5">
          <div className="h-20 w-20 rounded-3xl bg-slate-100" />
          <div className="space-y-3 text-center">
            <div className="h-6 w-52 bg-slate-100 rounded-full mx-auto" />
            <div className="h-4 w-40 bg-slate-50 rounded-full mx-auto" />
          </div>
          <div className="flex gap-3 mt-4">
            <div className="h-5 w-20 bg-slate-100 rounded-full" />
            <div className="h-5 w-20 bg-slate-100 rounded-full" />
          </div>
        </div>
      </div>

      {/* Feature chips */}
      <div className="flex gap-4 mt-10">
        {[1, 2, 3].map((i) => (
          <div key={i} className="h-10 w-28 bg-slate-100 rounded-2xl" />
        ))}
      </div>
    </div>
  )
}
