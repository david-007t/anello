"use client";

import { useEffect, useRef, useState } from "react";

interface TailoredResume {
  name: string;
  url: string | null;
  created_at: string;
}

export default function ResumePage() {
  const inputRef = useRef<HTMLInputElement>(null);
  const [current, setCurrent] = useState<string | null>(null);
  const [status, setStatus] = useState<"idle" | "loading" | "uploading" | "done" | "error">("loading");
  const [error, setError] = useState("");
  const [tailored, setTailored] = useState<TailoredResume[]>([]);
  const [coverLetters, setCoverLetters] = useState<TailoredResume[]>([]);
  const [tailoredLoading, setTailoredLoading] = useState(true);

  useEffect(() => {
    fetch("/api/resume")
      .then((r) => r.json())
      .then(({ data }) => {
        if (data?.file_name) setCurrent(data.file_name);
        setStatus("idle");
      })
      .catch(() => setStatus("idle"));

    loadTailored();
  }, []);

  function loadTailored() {
    setTailoredLoading(true);
    fetch("/api/tailored-resumes")
      .then((r) => r.json())
      .then(({ resumes, cover_letters }) => {
        setTailored(resumes ?? []);
        setCoverLetters(cover_letters ?? []);
      })
      .catch(() => { setTailored([]); setCoverLetters([]); })
      .finally(() => setTailoredLoading(false));
  }

  async function handleDelete(name: string) {
    const res = await fetch("/api/tailored-resumes", {
      method: "DELETE",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name }),
    });
    if (res.ok) loadTailored();
  }

  async function handleFile(file: File) {
    setStatus("uploading");
    setError("");
    const form = new FormData();
    form.append("resume", file);

    try {
      const res = await fetch("/api/resume/upload", { method: "POST", body: form });
      const data = await res.json();
      if (res.ok) {
        setCurrent(file.name);
        setStatus("done");
        setTimeout(() => setStatus("idle"), 2000);
      } else {
        setError(data.error || "Upload failed.");
        setStatus("error");
      }
    } catch {
      setError("Upload failed. Try again.");
      setStatus("error");
    }
  }

  function handleChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (file) handleFile(file);
  }

  function handleDrop(e: React.DragEvent) {
    e.preventDefault();
    const file = e.dataTransfer.files?.[0];
    if (file) handleFile(file);
  }

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-slate-900">Resume</h1>
        <p className="text-slate-500 mt-1 text-sm">
          Upload your master resume. Anelo will tailor it for every application.
        </p>
      </div>

      <div
        onDrop={handleDrop}
        onDragOver={(e) => e.preventDefault()}
        onClick={() => inputRef.current?.click()}
        className="bg-white border-2 border-dashed border-slate-200 hover:border-gray-400 rounded-2xl p-12 text-center max-w-xl cursor-pointer transition"
      >
        <input ref={inputRef} type="file" accept=".pdf,.doc,.docx" className="hidden" onChange={handleChange} />

        <svg className="w-10 h-10 text-slate-300 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>

        {status === "uploading" ? (
          <p className="text-sm font-medium text-slate-700">Uploading…</p>
        ) : status === "done" ? (
          <p className="text-sm font-medium text-gray-800">Uploaded ✓</p>
        ) : (
          <>
            <p className="text-sm font-medium text-slate-700 mb-1">
              {current ? `Current: ${current}` : "Drop your resume here"}
            </p>
            <p className="text-xs text-slate-400 mb-4">PDF or DOCX · Max 5MB</p>
            <span className="px-5 py-2.5 bg-gray-800 hover:bg-gray-900 text-white text-sm font-semibold rounded-xl transition">
              {current ? "Replace file" : "Choose file"}
            </span>
          </>
        )}

        {status === "error" && <p className="mt-3 text-sm text-red-500">{error}</p>}
      </div>

      {/* Tailored Resumes */}
      <div className="mt-10 max-w-xl">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-base font-semibold text-slate-900">Tailored Resumes</h2>
          {!tailoredLoading && (
            <span className="text-xs text-slate-400">{tailored.length} / 3 saved</span>
          )}
        </div>

        {tailoredLoading ? (
          <p className="text-sm text-slate-400">Loading…</p>
        ) : tailored.length === 0 ? (
          <div className="bg-white border border-slate-100 rounded-2xl p-6 text-center">
            <p className="text-sm text-slate-400">No tailored resumes yet. Use "Tailor Resume" on a job in your digest.</p>
          </div>
        ) : (
          <div className="flex flex-col gap-2">
            {tailored.map((r) => (
              <div key={r.name} className="bg-white border border-slate-100 rounded-2xl px-5 py-4 flex items-center justify-between gap-4">
                <span className="text-sm text-slate-700 truncate">{r.name}</span>
                <div className="flex items-center gap-3 shrink-0">
                  {r.url && (
                    <a
                      href={r.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-xs font-medium text-gray-800 hover:text-gray-900"
                    >
                      Download
                    </a>
                  )}
                  <button
                    onClick={() => handleDelete(r.name)}
                    className="text-xs font-medium text-red-500 hover:text-red-700"
                  >
                    Delete
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Cover Letters */}
      <div className="mt-8 max-w-xl">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-base font-semibold text-slate-900">Cover Letters</h2>
          {!tailoredLoading && (
            <span className="text-xs text-slate-400">{coverLetters.length} saved</span>
          )}
        </div>

        {tailoredLoading ? (
          <p className="text-sm text-slate-400">Loading…</p>
        ) : coverLetters.length === 0 ? (
          <div className="bg-white border border-slate-100 rounded-2xl p-6 text-center">
            <p className="text-sm text-slate-400">No cover letters yet. Use "Cover Letter" on a job in your digest.</p>
          </div>
        ) : (
          <div className="flex flex-col gap-2">
            {coverLetters.map((r) => (
              <div key={r.name} className="bg-white border border-slate-100 rounded-2xl px-5 py-4 flex items-center justify-between gap-4">
                <span className="text-sm text-slate-700 truncate">{r.name}</span>
                <div className="flex items-center gap-3 shrink-0">
                  {r.url && (
                    <a href={r.url} target="_blank" rel="noopener noreferrer" className="text-xs font-medium text-gray-800 hover:text-gray-900">
                      Download
                    </a>
                  )}
                  <button onClick={() => handleDelete(r.name)} className="text-xs font-medium text-red-500 hover:text-red-700">
                    Delete
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
