"use client";

import { useEffect, useState } from "react";

export default function PreferencesPage() {
  const [form, setForm] = useState<Record<string, string>>({});
  const [status, setStatus] = useState<"idle" | "loading" | "saving" | "saved" | "error">("loading");

  useEffect(() => {
    fetch("/api/preferences")
      .then((r) => r.json())
      .then(({ data }) => {
        if (data) setForm(data);
        setStatus("idle");
      })
      .catch(() => setStatus("idle"));
  }, []);

  function set(key: string, value: string) {
    setForm((f) => ({ ...f, [key]: value }));
  }

  async function handleSave(e: React.FormEvent) {
    e.preventDefault();
    setStatus("saving");
    try {
      const res = await fetch("/api/preferences", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(form),
      });
      setStatus(res.ok ? "saved" : "error");
      if (res.ok) setTimeout(() => setStatus("idle"), 2000);
    } catch {
      setStatus("error");
    }
  }

  const inputClass = "w-full px-4 py-2.5 rounded-xl border border-slate-200 text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-gray-700 focus:border-transparent disabled:opacity-50";
  const loading = status === "loading";

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-slate-900">Job Preferences</h1>
        <p className="text-slate-500 mt-1 text-sm">Tell Anelo exactly what to look for.</p>
      </div>

      <form onSubmit={handleSave} className="bg-white border border-slate-100 rounded-2xl p-6 max-w-xl space-y-5">

        {/* Target Roles */}
        <div>
          <label className="block text-sm font-semibold text-slate-700 mb-2">Target roles (up to 3)</label>
          <div className="space-y-2">
            {(["role", "role_2", "role_3"] as const).map((key, i) => (
              <input
                key={key}
                type="text"
                value={form[key] ?? ""}
                onChange={(e) => set(key, e.target.value)}
                placeholder={loading ? "Loading…" : i === 0 ? "Primary role, e.g. Product Manager" : `Role ${i + 1}, e.g. ${i === 1 ? "Technical Program Manager" : "Senior Data Engineer"}`}
                disabled={loading}
                className={inputClass}
              />
            ))}
          </div>
        </div>

        {/* Location */}
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1.5">Location</label>
          <input
            type="text"
            value={form.location ?? ""}
            onChange={(e) => set("location", e.target.value)}
            placeholder={loading ? "Loading…" : "e.g. San Francisco, Remote"}
            disabled={loading}
            className={inputClass}
          />
        </div>

        {/* Experience level */}
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1.5">Years of experience</label>
          <div className="flex items-center gap-3">
            <input
              type="number"
              min={0}
              value={form.experience_min ?? ""}
              onChange={(e) => set("experience_min", e.target.value)}
              placeholder="Min"
              disabled={loading}
              className={`${inputClass} w-28`}
            />
            <span className="text-sm text-slate-400">to</span>
            <input
              type="number"
              min={0}
              value={form.experience_max ?? ""}
              onChange={(e) => set("experience_max", e.target.value)}
              placeholder="Max"
              disabled={loading}
              className={`${inputClass} w-28`}
            />
            <span className="text-sm text-slate-400">years</span>
          </div>
        </div>

        {/* Salary */}
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1.5">Minimum salary (USD)</label>
          <input
            type="text"
            value={form.min_salary ?? ""}
            onChange={(e) => set("min_salary", e.target.value)}
            placeholder={loading ? "Loading…" : "e.g. 120000"}
            disabled={loading}
            className={inputClass}
          />
        </div>

        {/* Company types */}
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1.5">Company types</label>
          <input
            type="text"
            value={form.company_types ?? ""}
            onChange={(e) => set("company_types", e.target.value)}
            placeholder={loading ? "Loading…" : "e.g. Startup, Series B, FAANG"}
            disabled={loading}
            className={inputClass}
          />
        </div>

        {/* Skills */}
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1.5">Skills to highlight</label>
          <input
            type="text"
            value={form.skills ?? ""}
            onChange={(e) => set("skills", e.target.value)}
            placeholder={loading ? "Loading…" : "e.g. React, Python, SQL"}
            disabled={loading}
            className={inputClass}
          />
        </div>

        <button
          type="submit"
          disabled={loading || status === "saving"}
          className="w-full py-3 bg-gray-800 hover:bg-gray-900 text-white font-semibold text-sm rounded-xl transition disabled:opacity-50 cursor-pointer"
        >
          {status === "saving" ? "Saving…" : status === "saved" ? "Saved ✓" : "Save preferences"}
        </button>
        {status === "error" && <p className="text-sm text-red-500 text-center">Something went wrong. Try again.</p>}
      </form>
    </div>
  );
}
