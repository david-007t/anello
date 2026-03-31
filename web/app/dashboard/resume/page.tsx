export default function ResumePage() {
  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-slate-900">Resume</h1>
        <p className="text-slate-500 mt-1 text-sm">
          Upload your master resume. Anelo will tailor it for every application.
        </p>
      </div>
      <div className="bg-white border-2 border-dashed border-slate-200 rounded-2xl p-12 text-center max-w-xl">
        <svg className="w-10 h-10 text-slate-300 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
        <p className="text-sm font-medium text-slate-700 mb-1">Drop your resume here</p>
        <p className="text-xs text-slate-400 mb-4">PDF or DOCX · Max 5MB</p>
        <button className="px-5 py-2.5 bg-brand-600 hover:bg-brand-700 text-white text-sm font-semibold rounded-xl transition cursor-pointer">
          Choose file
        </button>
      </div>
    </div>
  );
}
