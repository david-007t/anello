import { currentUser } from "@clerk/nextjs/server";

export default async function DashboardPage() {
  const user = await currentUser();

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-slate-900">
          Welcome back{user?.firstName ? `, ${user.firstName}` : ""} 👋
        </h1>
        <p className="text-slate-500 mt-1 text-sm">
          Here&apos;s what Anelo is doing for you today.
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
        {[
          { label: "Applications sent", value: "—", sub: "this month" },
          { label: "Jobs in digest", value: "—", sub: "today" },
          { label: "Responses", value: "—", sub: "total" },
        ].map((stat) => (
          <div key={stat.label} className="bg-white border border-slate-100 rounded-2xl p-5">
            <p className="text-xs text-slate-400 font-medium uppercase tracking-wide mb-1">{stat.label}</p>
            <p className="text-3xl font-black text-slate-900">{stat.value}</p>
            <p className="text-xs text-slate-400 mt-0.5">{stat.sub}</p>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="bg-white border border-slate-100 rounded-2xl p-6">
          <h2 className="font-semibold text-slate-900 mb-1">Resume</h2>
          <p className="text-sm text-slate-400 mb-4">Upload your master resume to get started.</p>
          <a href="/dashboard/resume" className="inline-flex items-center gap-2 text-sm font-semibold text-brand-600 hover:text-brand-700">
            Upload resume →
          </a>
        </div>
        <div className="bg-white border border-slate-100 rounded-2xl p-6">
          <h2 className="font-semibold text-slate-900 mb-1">Job preferences</h2>
          <p className="text-sm text-slate-400 mb-4">Tell Anelo what roles and locations to target.</p>
          <a href="/dashboard/preferences" className="inline-flex items-center gap-2 text-sm font-semibold text-brand-600 hover:text-brand-700">
            Set preferences →
          </a>
        </div>
      </div>
    </div>
  );
}
