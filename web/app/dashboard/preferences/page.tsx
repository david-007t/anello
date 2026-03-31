export default function PreferencesPage() {
  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-slate-900">Job Preferences</h1>
        <p className="text-slate-500 mt-1 text-sm">
          Tell Anelo exactly what to look for.
        </p>
      </div>
      <div className="bg-white border border-slate-100 rounded-2xl p-6 max-w-xl space-y-5">
        {[
          { label: "Job title / role", placeholder: "e.g. Software Engineer, Product Manager" },
          { label: "Location", placeholder: "e.g. San Francisco, Remote" },
          { label: "Minimum salary (USD)", placeholder: "e.g. 120000" },
          { label: "Company types", placeholder: "e.g. Startup, Series B, FAANG" },
          { label: "Skills to highlight", placeholder: "e.g. React, Python, SQL" },
        ].map((field) => (
          <div key={field.label}>
            <label className="block text-sm font-medium text-slate-700 mb-1.5">{field.label}</label>
            <input
              type="text"
              placeholder={field.placeholder}
              className="w-full px-4 py-2.5 rounded-xl border border-slate-200 text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent"
            />
          </div>
        ))}
        <button className="w-full py-3 bg-brand-600 hover:bg-brand-700 text-white font-semibold text-sm rounded-xl transition">
          Save preferences
        </button>
      </div>
    </div>
  );
}
