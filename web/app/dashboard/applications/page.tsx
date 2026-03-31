export default function ApplicationsPage() {
  return (
    <div className="p-8 max-w-5xl">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-slate-900">Applications</h1>
        <p className="text-slate-500 mt-1 text-sm">
          Every application Anelo has sent on your behalf.
        </p>
      </div>

      {/* Empty state */}
      <div className="bg-white border border-slate-100 rounded-2xl">
        {/* Table header */}
        <div className="grid grid-cols-5 gap-4 px-5 py-3 border-b border-slate-100">
          {["Company", "Role", "ATS", "Resume Version", "Status"].map((h) => (
            <p key={h} className="text-xs font-semibold text-slate-400 uppercase tracking-wide">{h}</p>
          ))}
        </div>

        {/* Empty state */}
        <div className="py-20 text-center">
          <svg className="w-10 h-10 text-slate-200 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
          </svg>
          <p className="text-sm font-semibold text-slate-400">No applications yet</p>
          <p className="text-xs text-slate-300 mt-1">
            Upload your resume and set preferences to get started
          </p>
        </div>
      </div>
    </div>
  );
}
