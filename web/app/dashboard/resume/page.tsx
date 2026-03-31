"use client";

import { useState } from "react";

export default function ResumePage() {
  const [dragging, setDragging] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [status, setStatus] = useState<"idle" | "uploading" | "success" | "error">("idle");

  function handleDrop(e: React.DragEvent) {
    e.preventDefault();
    setDragging(false);
    const f = e.dataTransfer.files[0];
    if (f) setFile(f);
  }

  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const f = e.target.files?.[0];
    if (f) setFile(f);
  }

  async function handleUpload() {
    if (!file) return;
    setStatus("uploading");

    const form = new FormData();
    form.append("resume", file);

    const res = await fetch("/api/resume/upload", { method: "POST", body: form });
    setStatus(res.ok ? "success" : "error");
  }

  return (
    <div className="p-8 max-w-2xl">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-slate-900">Resume</h1>
        <p className="text-slate-500 mt-1 text-sm">
          Upload your master resume. Anello will use this as the base for every tailored application.
        </p>
      </div>

      {/* Upload zone */}
      <div
        onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={handleDrop}
        className={`border-2 border-dashed rounded-2xl p-10 text-center transition cursor-pointer ${
          dragging ? "border-brand-400 bg-brand-50" : "border-slate-200 hover:border-brand-300 hover:bg-slate-50"
        }`}
        onClick={() => document.getElementById("resume-input")?.click()}
      >
        <input
          id="resume-input"
          type="file"
          accept=".pdf,.doc,.docx"
          className="hidden"
          onChange={handleFileChange}
        />
        <svg className="w-10 h-10 text-slate-300 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
        {file ? (
          <div>
            <p className="font-semibold text-slate-800">{file.name}</p>
            <p className="text-xs text-slate-400 mt-1">{(file.size / 1024).toFixed(0)} KB</p>
          </div>
        ) : (
          <div>
            <p className="font-semibold text-slate-700">Drop your resume here</p>
            <p className="text-sm text-slate-400 mt-1">or click to browse · PDF, DOC, DOCX</p>
          </div>
        )}
      </div>

      {file && status !== "success" && (
        <button
          onClick={handleUpload}
          disabled={status === "uploading"}
          className="mt-4 w-full py-3 bg-brand-600 hover:bg-brand-700 text-white font-semibold rounded-xl transition disabled:opacity-60"
        >
          {status === "uploading" ? "Uploading…" : "Upload Resume"}
        </button>
      )}

      {status === "success" && (
        <div className="mt-4 flex items-center gap-3 bg-green-50 border border-green-100 rounded-xl px-4 py-3">
          <svg className="w-5 h-5 text-green-500 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
          <p className="text-sm font-medium text-green-700">Resume uploaded successfully.</p>
        </div>
      )}

      {status === "error" && (
        <p className="mt-4 text-sm text-red-500 text-center">Upload failed. Please try again.</p>
      )}

      {/* Tips */}
      <div className="mt-8 bg-slate-50 rounded-2xl p-5 border border-slate-100">
        <p className="text-sm font-semibold text-slate-700 mb-3">Tips for best results</p>
        <ul className="space-y-2 text-sm text-slate-500">
          <li className="flex items-start gap-2">
            <span className="text-brand-500 mt-0.5">•</span>
            Use a PDF for most consistent parsing
          </li>
          <li className="flex items-start gap-2">
            <span className="text-brand-500 mt-0.5">•</span>
            Include all skills, tools, and technologies you know
          </li>
          <li className="flex items-start gap-2">
            <span className="text-brand-500 mt-0.5">•</span>
            Quantify achievements where possible — Anelo uses these in tailoring
          </li>
        </ul>
      </div>
    </div>
  );
}
