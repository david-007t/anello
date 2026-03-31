import { currentUser } from "@clerk/nextjs/server";
import Link from "next/link";

const quickActions = [
  { href: "/dashboard/resume", label: "Upload Resume", desc: "Add your master resume", icon: "📄" },
  { href: "/dashboard/preferences", label: "Set Preferences", desc: "Role, location, salary", icon: "⚙️" },
  { href: "/dashboard/digest", label: "View Digest", desc: "Today's job matches", icon: "📬" },
  { href: "/dashboard/applications", label: "Applications", desc: "Track your pipeline", icon: "📊" },
];

const stats = [
  { label: "Jobs Matched", value: "—" },
  { label: "Applications Sent", value: "—" },
  { label: "Resumes Tailored", value: "—" },
  { label: "Interviews", value: "—" },
];

export default async function DashboardPage() {
  const user = await currentUser();

  return (
    <div className="p-8 max-w-5xl">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-slate-900">
          Good morning{user?.firstName ? `, ${user.firstName}` : ""} 👋
        </h1>
        <p className="text-slate-500 mt-1 text-sm">
          Here&apos;s what Anelo has been doing for you.
        </p>
      </div>

      {/* Setup banner — shown until resume + prefs set */}
      <div className="mb-8 bg-brand-50 border border-brand-100 rounded-2xl p-5 flex items-start gap-4">
        <div className="w-8 h-8 rounded-full bg-brand-100 flex items-center justify-center shrink-0 mt-0.5">
          <svg className="w-4 h-4 text-brand-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>
        <div className="flex-1">
          <p className="text-sm font-semibold text-brand-900 mb-1">Finish setting up your account</p>
          <p className="text-sm text-brand-700 mb-3">
            Upload your resume and set your job preferences so Anelo can start finding and applying to jobs for you.
          </p>
          <div className="flex gap-3">
            <Link href="/dashboard/resume" className="text-sm font-semibold text-white bg-brand-600 hover:bg-brand-700 px-4 py-1.5 rounded-lg transition">
              Upload Resume
            </Link>
            <Link href="/dashboard/preferences" className="text-sm font-semibold text-brand-700 hover:text-brand-900 px-4 py-1.5 rounded-lg border border-brand-200 hover:border-brand-300 transition">
              Set Preferences
            </Link>
          </div>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        {stats.map((s) => (
          <div key={s.label} className="bg-white rounded-2xl border border-slate-100 p-5">
            <p className="text-2xl font-black text-slate-900">{s.value}</p>
            <p className="text-xs text-slate-400 mt-1">{s.label}</p>
          </div>
        ))}
      </div>

      {/* Quick actions */}
      <div>
        <h2 className="text-sm font-semibold text-slate-500 uppercase tracking-wide mb-4">Quick Actions</h2>
        <div className="grid sm:grid-cols-2 gap-3">
          {quickActions.map((a) => (
            <Link
              key={a.href}
              href={a.href}
              className="flex items-center gap-4 bg-white border border-slate-100 hover:border-brand-100 hover:shadow-sm rounded-2xl p-5 transition group"
            >
              <span className="text-2xl">{a.icon}</span>
              <div>
                <p className="text-sm font-semibold text-slate-900 group-hover:text-brand-600 transition">{a.label}</p>
                <p className="text-xs text-slate-400">{a.desc}</p>
              </div>
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
}
