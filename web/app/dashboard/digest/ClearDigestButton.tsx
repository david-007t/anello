"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

export default function ClearDigestButton() {
  const [state, setState] = useState<"idle" | "loading" | "done" | "error">("idle");
  const router = useRouter();

  async function handleClear() {
    if (!confirm("Clear all jobs from your digest?")) return;
    setState("loading");
    try {
      const res = await fetch("/api/clear-digest", { method: "POST" });
      if (!res.ok) throw new Error();
      setState("done");
      setTimeout(() => {
        router.refresh();
        setState("idle");
      }, 800);
    } catch {
      setState("error");
      setTimeout(() => setState("idle"), 3000);
    }
  }

  return (
    <button
      onClick={handleClear}
      disabled={state !== "idle"}
      className={`px-4 py-2 rounded-xl text-sm font-semibold transition ${
        state === "idle"
          ? "bg-white border border-slate-200 text-slate-500 hover:border-red-300 hover:text-red-500"
          : state === "loading"
          ? "bg-slate-100 text-slate-400 cursor-not-allowed"
          : state === "done"
          ? "bg-white border border-slate-200 text-green-500 cursor-not-allowed"
          : "bg-white border border-red-200 text-red-500 cursor-not-allowed"
      }`}
    >
      {state === "loading" ? "Clearing…" : state === "done" ? "Cleared" : state === "error" ? "Failed" : "Clear Digest"}
    </button>
  );
}
