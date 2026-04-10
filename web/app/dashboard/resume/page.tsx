"use client";

import { useEffect, useRef, useState } from "react";

export default function ResumePage() {
  const inputRef = useRef<HTMLInputElement>(null);
  const [current, setCurrent] = useState<string | null>(null);
  const [status, setStatus] = useState<"idle" | "loading" | "uploading" | "done" | "error">("loading");
  const [error, setError] = useState("");

  useEffect(() => {
    fetch("/api/resume")
      .then((r) => r.json())
      .then(({ data }) => {
        if (data?.file_name) setCurrent(data.file_name);
        setStatus("idle");
      })
      .catch(() => setStatus("idle"));
  }, []);

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
          Upload your master resume. Anelo uses it to understand your background and improve digest matching.
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
    </div>
  );
}
