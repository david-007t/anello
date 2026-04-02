export const dynamic = "force-dynamic";

import { currentUser } from "@clerk/nextjs/server";
import { supabaseAdmin } from "@/lib/supabase";
import TailorButton from "./TailorButton";
import ApplyButton from "./ApplyButton";
import RunDigestButton from "./RunDigestButton";
import ClearDigestButton from "./ClearDigestButton";

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

interface GroupedJob {
  id: string;
  company: string;
  role: string;
  job_url: string;
  source: string;
  matched_at: string;
  applied: boolean;
  locations: string[];
  salaries: string[];
}

function formatDate(ts: string): string {
  return new Date(ts).toLocaleDateString("en-US", { month: "short", day: "numeric" });
}

function groupJobs(jobs: DigestJob[]): GroupedJob[] {
  const map = new Map<string, GroupedJob>();
  for (const job of jobs) {
    const key = `${(job.company ?? "").toLowerCase().trim()}|||${(job.role ?? "").toLowerCase().trim()}`;
    if (!map.has(key)) {
      map.set(key, {
        id: job.id,
        company: job.company,
        role: job.role,
        job_url: job.job_url,
        source: job.source,
        matched_at: job.matched_at,
        applied: job.applied,
        locations: job.location ? [job.location] : [],
        salaries: job.salary_range ? [job.salary_range] : [],
      });
    } else {
      const g = map.get(key)!;
      if (job.applied) g.applied = true;
      if (job.location && !g.locations.includes(job.location)) g.locations.push(job.location);
      if (job.salary_range && !g.salaries.includes(job.salary_range)) g.salaries.push(job.salary_range);
    }
  }
  return Array.from(map.values());
}

function detectAts(url: string): "greenhouse" | "lever" | "ashby" | "workable" | "workday" | "unknown" {
  if (!url) return "unknown";
  const u = url.toLowerCase();
  if (u.includes("boards.greenhouse.io") || u.includes("greenhouse.io/jobs")) return "greenhouse";
  if (u.includes("jobs.lever.co")) return "lever";
  if (u.includes("jobs.ashby.com")) return "ashby";
  if (u.includes("apply.workable.com")) return "workable";
  if (u.includes(".myworkdayjobs.com") || u.includes("workday.com")) return "workday";
  return "unknown";
}

function canAutoApply(url: string): boolean {
  const ats = detectAts(url);
  return ats === "greenhouse" || ats === "lever" || ats === "ashby" || ats === "workable";
}

function JobCard({ job, index, showApply }: { job: GroupedJob; index: number; showApply: boolean }) {
  return (
    <div className="bg-white border border-slate-100 rounded-2xl p-5 flex items-start gap-4">
      <span className="text-2xl font-black text-slate-300 select-none w-8 shrink-0 leading-none mt-0.5">
        {String(index + 1).padStart(2, "0")}
      </span>
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2 flex-wrap mb-1">
          <a
            href={job.job_url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-sm font-semibold text-indigo-600 hover:underline"
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
        {job.locations.length > 0 && (
          <p className="text-xs text-slate-400 mt-0.5">
            {job.locations.slice(0, 3).join(" · ")}
            {job.locations.length > 3 && ` +${job.locations.length - 3} more`}
          </p>
        )}
        {job.salaries.length > 0 && (
          <p className="text-xs text-slate-500 mt-0.5">
            {job.salaries.length === 1
              ? job.salaries[0]
              : (() => {
                  const nums = job.salaries
                    .flatMap((s) => s.replace(/[$,]/g, "").split("–").map(Number))
                    .filter(Boolean);
                  const lo = Math.min(...nums);
                  const hi = Math.max(...nums);
                  return lo === hi
                    ? `$${lo.toLocaleString()}`
                    : `$${lo.toLocaleString()}–$${hi.toLocaleString()}`;
                })()}
          </p>
        )}
        <div className="mt-2 flex items-center gap-2 flex-wrap">
          <TailorButton jobId={job.id} jobNumber={index + 1} />
          {showApply ? (
            <ApplyButton jobId={job.id} />
          ) : (
            <a
              href={job.job_url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-xs font-medium px-3 py-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-600 transition-colors whitespace-nowrap"
            >
              Open Job
            </a>
          )}
        </div>
      </div>
      <span className="text-xs text-slate-400 whitespace-nowrap mt-0.5 shrink-0">
        {formatDate(job.matched_at)}
      </span>
    </div>
  );
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
      .limit(100);
    if (error) console.error("[digest] supabase error:", error);
    jobs = data ?? [];
  }

  const grouped = groupJobs(jobs);
  const autoApplyJobs = grouped.filter((j) => canAutoApply(j.job_url));
  const manualJobs = grouped.filter((j) => !canAutoApply(j.job_url));

  return (
    <div className="p-8">
      <div className="mb-8 flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Job Digest</h1>
          <p className="text-slate-500 mt-1 text-sm">
            Your daily curated job matches. Set preferences to start receiving jobs.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <ClearDigestButton />
          <RunDigestButton />
        </div>
      </div>

      {grouped.length === 0 ? (
        <div className="bg-white border border-slate-100 rounded-2xl p-12 text-center max-w-xl">
          <svg className="w-10 h-10 text-slate-200 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
          </svg>
          <p className="text-sm font-medium text-slate-700 mb-1">No digest yet</p>
          <p className="text-xs text-slate-400">Your first digest will arrive once preferences are set.</p>
        </div>
      ) : (
        <div className="flex flex-col gap-8 max-w-2xl">
          {autoApplyJobs.length > 0 && (
            <section>
              <div className="flex items-center gap-2 mb-3">
                <h2 className="text-sm font-semibold text-slate-700">Auto-Apply</h2>
                <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-emerald-50 text-emerald-700">
                  {autoApplyJobs.length} job{autoApplyJobs.length !== 1 ? "s" : ""}
                </span>
              </div>
              <div className="flex flex-col gap-3">
                {autoApplyJobs.map((job, index) => (
                  <JobCard key={job.id} job={job} index={index} showApply={true} />
                ))}
              </div>
            </section>
          )}

          {manualJobs.length > 0 && (
            <section>
              <div className="flex items-center gap-2 mb-3">
                <h2 className="text-sm font-semibold text-slate-700">Apply Manually</h2>
                <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-slate-100 text-slate-500">
                  {manualJobs.length} job{manualJobs.length !== 1 ? "s" : ""}
                </span>
              </div>
              <div className="flex flex-col gap-3">
                {manualJobs.map((job, index) => (
                  <JobCard key={job.id} job={job} index={index} showApply={false} />
                ))}
              </div>
            </section>
          )}
        </div>
      )}
    </div>
  );
}
