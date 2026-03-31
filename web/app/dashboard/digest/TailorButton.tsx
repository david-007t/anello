"use client";
import { useState } from "react";

export default function TailorButton({ jobId }: { jobId: string }) {
  const [tailorState, setTailorState] = useState<"idle" | "loading" | "done" | "error">("idle");
  const [coverState, setCoverState] = useState<"idle" | "loading" | "error">("idle");
  const [coverText, setCoverText] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  async function handleTailor() {
    setTailorState("loading");
    try {
      const res = await fetch("/api/tailor", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ job_id: jobId }),
      });
      if (!res.ok) throw new Error(await res.text());
      const { pdf_base64, filename } = await res.json();
      const blob = new Blob([Uint8Array.from(atob(pdf_base64), c => c.charCodeAt(0))], { type: "application/pdf" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = filename;
      a.click();
      URL.revokeObjectURL(url);
      setTailorState("done");
    } catch {
      setTailorState("error");
    } finally {
      setTimeout(() => setTailorState("idle"), 3000);
    }
  }

  async function handleCoverLetter() {
    setCoverState("loading");
    try {
      const res = await fetch("/api/cover-letter", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ job_id: jobId }),
      });
      if (!res.ok) throw new Error(await res.text());
      const { cover_letter } = await res.json();
      setCoverText(cover_letter);
      setCoverState("idle");
    } catch {
      setCoverState("error");
      setTimeout(() => setCoverState("idle"), 3000);
    }
  }

  function handleCopy() {
    if (coverText) {
      navigator.clipboard.writeText(coverText);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  }

  return (
    <>
      <div className="mt-2 flex items-center gap-2">
        <button
          onClick={handleTailor}
          disabled={tailorState === "loading"}
          className="text-xs font-medium px-3 py-1.5 rounded-lg bg-indigo-50 text-indigo-700 hover:bg-indigo-100 disabled:opacity-50 transition-colors whitespace-nowrap"
        >
          {tailorState === "loading" ? "Tailoring…" : tailorState === "done" ? "Downloaded ✓" : tailorState === "error" ? "Failed" : "Tailor Resume"}
        </button>

        <button
          onClick={handleCoverLetter}
          disabled={coverState === "loading"}
          className="text-xs font-medium px-3 py-1.5 rounded-lg bg-slate-100 text-slate-600 hover:bg-slate-200 disabled:opacity-50 transition-colors whitespace-nowrap"
        >
          {coverState === "loading" ? "Generating…" : coverState === "error" ? "Failed" : "Cover Letter"}
        </button>
      </div>

      {/* Cover letter modal */}
      {coverText && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
          <div className="bg-white rounded-2xl shadow-xl max-w-2xl w-full p-6 flex flex-col gap-4">
            <div className="flex items-center justify-between">
              <h2 className="text-base font-semibold text-slate-900">Cover Letter</h2>
              <button
                onClick={() => setCoverText(null)}
                className="text-slate-400 hover:text-slate-600 text-sm"
              >
                Close
              </button>
            </div>
            <textarea
              readOnly
              value={coverText}
              rows={12}
              className="w-full border border-slate-200 rounded-xl p-4 text-sm text-slate-700 resize-none focus:outline-none focus:ring-2 focus:ring-brand-300"
            />
            <button
              onClick={handleCopy}
              className="self-end px-4 py-2 text-sm font-semibold bg-brand-600 text-white rounded-xl hover:bg-brand-700 transition"
            >
              {copied ? "Copied ✓" : "Copy to clipboard"}
            </button>
          </div>
        </div>
      )}
    </>
  );
}
