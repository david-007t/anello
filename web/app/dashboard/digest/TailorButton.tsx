"use client";
import { useState } from "react";

export default function TailorButton({ jobId }: { jobId: string }) {
  const [state, setState] = useState<"idle" | "loading" | "done" | "error">("idle");

  async function handleClick() {
    setState("loading");
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
      setState("done");
    } catch {
      setState("error");
    } finally {
      setTimeout(() => setState("idle"), 3000);
    }
  }

  return (
    <button
      onClick={handleClick}
      disabled={state === "loading"}
      className="mt-2 text-xs font-medium px-3 py-1.5 rounded-lg bg-indigo-50 text-indigo-700 hover:bg-indigo-100 disabled:opacity-50 transition-colors whitespace-nowrap"
    >
      {state === "loading" ? "Tailoring…" : state === "done" ? "Opened ✓" : state === "error" ? "Failed" : "Tailor Resume"}
    </button>
  );
}
