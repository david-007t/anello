import { currentUser } from "@clerk/nextjs/server";
import { supabaseAdmin } from "@/lib/supabase";
import TailorButton from "./TailorButton";
import RunDigestButton from "./RunDigestButton";

interface DigestJob {
  id: string;
  user_id: string;
  company: string;
  role: string;
  job_url: string;
  location: string;
  salary_range: string | null;
  source: string;
  matched_at: string;
  applied: boolean;
}

function formatDate(ts: string): string {
  return new Date(ts).toLocaleDateString("en-US", { month: "short", day: "numeric" });
}

export default async function DigestPage() {
  const user = await currentUser();
  let jobs: DigestJob[] = [];

  if (user) {
    const { data, error } = await supabaseAdmin()
      .from("digest_jobs")
      .select("*")
      .eq("user_id", user.id)
      .order("matched_at", { ascending: false })
      .limit(50);
    if (error) console.error("[digest] supabase error:", error);
    jobs = data ?? [];
  }

  return (
    <div className="p-8">
      <div className="mb-8 flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Job Digest</h1>
          <p className="text-slate-500 mt-1 text-sm">
            Your daily curated job matches. Set preferences to start receiving jobs.
          </p>
        </div>
        <RunDigestButton />
      </div>

      {jobs.length === 0 ? (
        <div className="bg-white border border-slate-100 rounded-2xl p-12 text-center max-w-xl">
          <svg className="w-10 h-10 text-slate-200 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
          </svg>
          <p className="text-sm font-medium text-slate-700 mb-1">No digest yet</p>
          <p className="text-xs text-slate-400">Your first digest will arrive once preferences are set.</p>
        </div>
      ) : (
        <div className="flex flex-col gap-3 max-w-2xl">
          {jobs.map((job, index) => (
            <div key={job.id} className="bg-white border border-slate-100 rounded-2xl p-5 flex items-start gap-4">
              {/* Job number */}
              <span className="text-2xl font-black text-slate-100 select-none w-8 shrink-0 leading-none mt-0.5">
                {String(index + 1).padStart(2, "0")}
              </span>

              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2 flex-wrap mb-1">
                  <a
                    href={job.job_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-sm font-semibold text-indigo-600 hover:underline truncate"
                  >
                    {job.role}
                  </a>
                  {job.applied && (
                    <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-indigo-50 text-indigo-700">
                      Applied
                    </span>
                  )}
                  {job.source && (
                    <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-slate-100 text-slate-400 capitalize">
                      {job.source}
                    </span>
                  )}
                </div>
                <p className="text-sm text-slate-700 font-medium">{job.company}</p>
                <p className="text-xs text-slate-400 mt-0.5">{job.location}</p>
                {job.salary_range && (
                  <p className="text-xs text-slate-500 mt-0.5">{job.salary_range}</p>
                )}
                <TailorButton jobId={job.id} jobNumber={index + 1} />
              </div>

              <span className="text-xs text-slate-400 whitespace-nowrap mt-0.5 shrink-0">
                {formatDate(job.matched_at)}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
