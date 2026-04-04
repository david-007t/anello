"use client";
import { useState } from "react";

interface TailorResult {
  resume_pdf_base64: string;
  cover_letter_pdf_base64: string;
  resume_filename: string;
  cover_letter_filename: string;
}

function downloadPdf(base64: string, filename: string) {
  const blob = new Blob(
    [Uint8Array.from(atob(base64), (c) => c.charCodeAt(0))],
    { type: "application/pdf" }
  );
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

export default function TailorButton({ jobId, jobNumber }: { jobId: string; jobNumber: number }) {
  const [state, setState] = useState<"idle" | "loading" | "done" | "error">("idle");
  const [result, setResult] = useState<TailorResult | null>(null);
  const [coverLoading, setCoverLoading] = useState(false);

  async function fetchTailor(): Promise<TailorResult | null> {
    if (result) return result;
    setState("loading");
    try {
      const res = await fetch("/api/tailor", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ job_id: jobId, job_number: jobNumber }),
      });
      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.error || "Failed");
      }
      const data: TailorResult = await res.json();
      setResult(data);
      setState("done");
      return data;
    } catch (e: unknown) {
      setState("error");
      setTimeout(() => setState("idle"), 4000);
      return null;
    }
  }

  async function handleResume() {
    const data = await fetchTailor();
    if (data) downloadPdf(data.resume_pdf_base64, data.resume_filename);
  }

  async function handleCoverLetter() {
    if (result) {
      downloadPdf(result.cover_letter_pdf_base64, result.cover_letter_filename);
      return;
    }
    setCoverLoading(true);
    const data = await fetchTailor();
    setCoverLoading(false);
    if (data) downloadPdf(data.cover_letter_pdf_base64, data.cover_letter_filename);
  }

  const tailorLabel =
    state === "loading" ? "Tailoring…" :
    state === "done" ? "Resume ✓" :
    state === "error" ? "Failed" :
    "Tailor Resume";

  const coverLabel = coverLoading ? "Generating…" : "Cover Letter";

  return (
    <div className="mt-2 flex items-center gap-2">
      <button
        onClick={handleResume}
        disabled={state === "loading" || coverLoading}
        className="text-xs font-medium px-3 py-1.5 rounded-lg bg-gray-100 text-gray-700 hover:bg-gray-200 disabled:opacity-50 transition-colors whitespace-nowrap"
      >
        {tailorLabel}
      </button>
      <button
        onClick={handleCoverLetter}
        disabled={state === "loading" || coverLoading}
        className="text-xs font-medium px-3 py-1.5 rounded-lg bg-slate-100 text-slate-600 hover:bg-slate-200 disabled:opacity-50 transition-colors whitespace-nowrap"
      >
        {coverLabel}
      </button>
    </div>
  );
}
