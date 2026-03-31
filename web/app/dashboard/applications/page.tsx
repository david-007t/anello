export default function ApplicationsPage() {
  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-slate-900">Applications</h1>
        <p className="text-slate-500 mt-1 text-sm">
          Every application Anelo has submitted on your behalf.
        </p>
      </div>
      <div className="bg-white border border-slate-100 rounded-2xl overflow-hidden">
        <div className="grid grid-cols-5 px-5 py-3 border-b border-slate-100 bg-slate-50 text-xs font-semibold text-slate-400 uppercase tracking-wide">
          <span className="col-span-2">Role</span>
          <span>Company</span>
          <span>Status</span>
          <span>Date</span>
        </div>
        <div className="px-5 py-12 text-center">
          <p className="text-sm text-slate-400">No applications yet. Anelo will start applying once your resume and preferences are set.</p>
        </div>
      </div>
    </div>
  );
}
