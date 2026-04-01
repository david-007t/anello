import { currentUser } from "@clerk/nextjs/server";
import { supabaseAdmin } from "@/lib/supabase";

export default async function ApplicationsPage() {
  const user = await currentUser();
  const userId = user?.id ?? null;

  let applications: Array<{
    id: string;
    role: string;
    company: string;
    job_url: string | null;
    status: string;
    applied_at: string;
  }> = [];

  if (userId) {
    const { data } = await supabaseAdmin()
      .from("applications")
      .select("*")
      .eq("user_id", userId)
      .order("applied_at", { ascending: false });
    applications = data ?? [];
  }

  const statusBadge = (status: string) => {
    const base = "inline-block px-2 py-0.5 rounded-full text-xs font-medium";
    switch (status) {
      case "applied":
        return `${base} bg-blue-100 text-blue-700`;
      case "interviewing":
        return `${base} bg-green-100 text-green-700`;
      case "rejected":
        return `${base} bg-red-100 text-red-700`;
      case "offer":
        return `${base} bg-purple-100 text-purple-700`;
      default:
        return `${base} bg-slate-100 text-slate-600`;
    }
  };

  const formatDate = (ts: string) => {
    return new Date(ts).toLocaleDateString("en-US", { month: "short", day: "numeric" });
  };

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
        {applications.length === 0 ? (
          <div className="px-5 py-12 text-center">
            <p className="text-sm text-slate-400">No applications yet. Anelo will start applying once your resume and preferences are set.</p>
          </div>
        ) : (
          applications.map((app) => (
            <div
              key={app.id}
              className="grid grid-cols-5 px-5 py-4 border-b border-slate-100 text-sm text-slate-700 hover:bg-slate-50"
            >
              <span className="col-span-2">
                {app.job_url ? (
                  <a href={app.job_url} target="_blank" rel="noopener noreferrer" className="hover:underline text-slate-900">
                    {app.role}
                  </a>
                ) : (
                  app.role
                )}
              </span>
              <span>{app.company}</span>
              <span>
                <span className={statusBadge(app.status)}>{app.status}</span>
              </span>
              <span>{formatDate(app.applied_at)}</span>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
