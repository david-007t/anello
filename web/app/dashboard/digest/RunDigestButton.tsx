"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

export default function RunDigestButton() {
  const [state, setState] = useState<"idle" | "loading" | "done" | "error">("idle");
  const router = useRouter();

  async function handleRun() {
    setState("loading");
    try {
      const res = await fetch("/api/run-digest", { method: "POST" });
      if (!res.ok) throw new Error(await res.text());
      setState("done");
      // Refresh page after a short delay so new jobs appear
      setTimeout(() => {
        router.refresh();
        setState("idle");
      }, 1500);
    } catch {
      setState("error");
      setTimeout(() => setState("idle"), 3000);
    }
  }

  const labels = {
    idle: "Run Digest",
    loading: "Running…",
    done: "Done — refreshing",
    error: "Failed — try again",
  };

  const styles = {
    idle: "bg-brand-600 hover:bg-brand-700 text-white",
    loading: "bg-slate-200 text-slate-400 cursor-not-allowed",
    done: "bg-green-500 text-white cursor-not-allowed",
    error: "bg-red-500 text-white cursor-not-allowed",
  };

  return (
    <button
      onClick={handleRun}
      disabled={state !== "idle"}
      className={`px-4 py-2 rounded-xl text-sm font-semibold transition ${styles[state]}`}
    >
      {state === "loading" && (
        <span className="inline-block w-3 h-3 border-2 border-slate-400 border-t-transparent rounded-full animate-spin mr-2 align-middle" />
      )}
      {labels[state]}
    </button>
  );
}
