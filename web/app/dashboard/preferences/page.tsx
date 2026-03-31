"use client";

import { useState } from "react";

const JOB_TYPES = ["Full-time", "Part-time", "Contract", "Remote", "Hybrid", "On-site"];
const EXPERIENCE_LEVELS = ["Entry", "Mid", "Senior", "Staff", "Principal", "Director+"];

export default function PreferencesPage() {
  const [form, setForm] = useState({
    title: "",
    location: "",
    salaryMin: "",
    salaryMax: "",
    jobTypes: [] as string[],
    experienceLevel: "",
    industries: "",
    excludeCompanies: "",
  });
  const [status, setStatus] = useState<"idle" | "saving" | "saved" | "error">("idle");

  function toggleJobType(type: string) {
    setForm((f) => ({
      ...f,
      jobTypes: f.jobTypes.includes(type)
        ? f.jobTypes.filter((t) => t !== type)
        : [...f.jobTypes, type],
    }));
  }

  async function handleSave(e: React.FormEvent) {
    e.preventDefault();
    setStatus("saving");
    const res = await fetch("/api/preferences", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(form),
    });
    setStatus(res.ok ? "saved" : "error");
    if (res.ok) setTimeout(() => setStatus("idle"), 3000);
  }

  return (
    <div className="p-8 max-w-2xl">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-slate-900">Job Preferences</h1>
        <p className="text-slate-500 mt-1 text-sm">
          Tell Anelo what you&apos;re looking for. These settings drive every job match and application.
        </p>
      </div>

      <form onSubmit={handleSave} className="space-y-6">
        {/* Target role */}
        <div>
          <label className="block text-sm font-semibold text-slate-700 mb-2">Target Job Title</label>
          <input
            type="text"
            placeholder="e.g. Software Engineer, Product Manager"
            value={form.title}
            onChange={(e) => setForm({ ...form, title: e.target.value })}
            className="w-full px-4 py-2.5 rounded-xl border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent"
          />
        </div>

        {/* Location */}
        <div>
          <label className="block text-sm font-semibold text-slate-700 mb-2">Preferred Location</label>
          <input
            type="text"
            placeholder="e.g. San Francisco, CA or Remote"
            value={form.location}
            onChange={(e) => setForm({ ...form, location: e.target.value })}
            className="w-full px-4 py-2.5 rounded-xl border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent"
          />
        </div>

        {/* Salary */}
        <div>
          <label className="block text-sm font-semibold text-slate-700 mb-2">Salary Range (USD/year)</label>
          <div className="flex gap-3">
            <input
              type="number"
              placeholder="Min"
              value={form.salaryMin}
              onChange={(e) => setForm({ ...form, salaryMin: e.target.value })}
              className="flex-1 px-4 py-2.5 rounded-xl border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent"
            />
            <input
              type="number"
              placeholder="Max"
              value={form.salaryMax}
              onChange={(e) => setForm({ ...form, salaryMax: e.target.value })}
              className="flex-1 px-4 py-2.5 rounded-xl border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent"
            />
          </div>
        </div>

        {/* Job types */}
        <div>
          <label className="block text-sm font-semibold text-slate-700 mb-2">Job Type</label>
          <div className="flex flex-wrap gap-2">
            {JOB_TYPES.map((type) => (
              <button
                key={type}
                type="button"
                onClick={() => toggleJobType(type)}
                className={`px-3 py-1.5 rounded-lg text-sm font-medium border transition ${
                  form.jobTypes.includes(type)
                    ? "bg-brand-600 text-white border-brand-600"
                    : "bg-white text-slate-600 border-slate-200 hover:border-brand-300"
                }`}
              >
                {type}
              </button>
            ))}
          </div>
        </div>

        {/* Experience level */}
        <div>
          <label className="block text-sm font-semibold text-slate-700 mb-2">Experience Level</label>
          <div className="flex flex-wrap gap-2">
            {EXPERIENCE_LEVELS.map((level) => (
              <button
                key={level}
                type="button"
                onClick={() => setForm({ ...form, experienceLevel: level })}
                className={`px-3 py-1.5 rounded-lg text-sm font-medium border transition ${
                  form.experienceLevel === level
                    ? "bg-brand-600 text-white border-brand-600"
                    : "bg-white text-slate-600 border-slate-200 hover:border-brand-300"
                }`}
              >
                {level}
              </button>
            ))}
          </div>
        </div>

        {/* Industries */}
        <div>
          <label className="block text-sm font-semibold text-slate-700 mb-2">Target Industries</label>
          <input
            type="text"
            placeholder="e.g. Fintech, Healthcare, SaaS"
            value={form.industries}
            onChange={(e) => setForm({ ...form, industries: e.target.value })}
            className="w-full px-4 py-2.5 rounded-xl border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent"
          />
        </div>

        {/* Exclude companies */}
        <div>
          <label className="block text-sm font-semibold text-slate-700 mb-2">Exclude Companies</label>
          <input
            type="text"
            placeholder="Companies to skip, comma-separated"
            value={form.excludeCompanies}
            onChange={(e) => setForm({ ...form, excludeCompanies: e.target.value })}
            className="w-full px-4 py-2.5 rounded-xl border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent"
          />
        </div>

        <button
          type="submit"
          disabled={status === "saving"}
          className="w-full py-3 bg-brand-600 hover:bg-brand-700 text-white font-semibold rounded-xl transition disabled:opacity-60"
        >
          {status === "saving" ? "Saving…" : status === "saved" ? "Saved ✓" : "Save Preferences"}
        </button>
      </form>
    </div>
  );
}
