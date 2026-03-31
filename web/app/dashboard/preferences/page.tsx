"use client";

import { useEffect, useState } from "react";

const fields = [
  { key: "role", label: "Job title / role", placeholder: "e.g. Software Engineer, Product Manager" },
  { key: "location", label: "Location", placeholder: "e.g. San Francisco, Remote" },
  { key: "min_salary", label: "Minimum salary (USD)", placeholder: "e.g. 120000" },
  { key: "company_types", label: "Company types", placeholder: "e.g. Startup, Series B, FAANG" },
  { key: "skills", label: "Skills to highlight", placeholder: "e.g. React, Python, SQL" },
];

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

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-slate-900">Job Preferences</h1>
        <p className="text-slate-500 mt-1 text-sm">Tell Anelo exactly what to look for.</p>
      </div>

      <form onSubmit={handleSave} className="bg-white border border-slate-100 rounded-2xl p-6 max-w-xl space-y-5">
        {fields.map((field) => (
          <div key={field.key}>
            <label className="block text-sm font-medium text-slate-700 mb-1.5">{field.label}</label>
            <input
              type="text"
              value={form[field.key] ?? ""}
              onChange={(e) => setForm((f) => ({ ...f, [field.key]: e.target.value }))}
              placeholder={status === "loading" ? "Loading…" : field.placeholder}
              disabled={status === "loading"}
              className="w-full px-4 py-2.5 rounded-xl border border-slate-200 text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent disabled:opacity-50"
            />
          </div>
        ))}
        <button
          type="submit"
          disabled={status === "loading" || status === "saving"}
          className="w-full py-3 bg-brand-600 hover:bg-brand-700 text-white font-semibold text-sm rounded-xl transition disabled:opacity-50 cursor-pointer"
        >
          {status === "saving" ? "Saving…" : status === "saved" ? "Saved ✓" : "Save preferences"}
        </button>
        {status === "error" && <p className="text-sm text-red-500 text-center">Something went wrong. Try again.</p>}
      </form>
    </div>
  );
}
