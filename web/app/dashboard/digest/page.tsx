export default function DigestPage() {
  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-slate-900">Job Digest</h1>
        <p className="text-slate-500 mt-1 text-sm">
          Your daily curated job matches. Set preferences to start receiving jobs.
        </p>
      </div>
      <div className="bg-white border border-slate-100 rounded-2xl p-12 text-center max-w-xl">
        <svg className="w-10 h-10 text-slate-200 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
        </svg>
        <p className="text-sm font-medium text-slate-700 mb-1">No digest yet</p>
        <p className="text-xs text-slate-400">Your first digest will arrive once preferences are set.</p>
      </div>
    </div>
  );
}
