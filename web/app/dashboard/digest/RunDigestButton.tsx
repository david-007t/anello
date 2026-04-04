"use client";

import { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";

type PipelineStatus = "idle" | "running" | "complete" | "error";

interface StatusPayload {
  status: PipelineStatus;
  step: string;
  started_at: string | null;
  finished_at: string | null;
  error: string | null;
}

export default function RunDigestButton() {
  const [status, setStatus] = useState<PipelineStatus>("idle");
  const [step, setStep] = useState("");
  const router = useRouter();
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const hasSeenRunning = useRef(false);

  function stopPolling() {
    if (pollRef.current) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }
  }

  function startPolling() {
    stopPolling();
    hasSeenRunning.current = false;
    pollRef.current = setInterval(async () => {
      try {
        const res = await fetch("/api/pipeline-status");
        if (!res.ok) return;
        const data: StatusPayload = await res.json();

        if (data.status === "running") {
          hasSeenRunning.current = true;
        }

        setStatus(data.status);
        setStep(data.step ?? "");

        if (data.status === "complete") {
          // Only accept complete if we actually saw this run go through "running"
          // Guards against stale "complete" from a previous run
          if (!hasSeenRunning.current) return;
          stopPolling();
          setTimeout(() => {
            window.location.href = "/dashboard/digest";
          }, 2000);
        } else if (data.status === "error" || data.status === "idle") {
          stopPolling();
          if (data.status === "error") {
            setTimeout(() => {
              setStatus("idle");
              setStep("");
            }, 4000);
          }
        }
      } catch {
        // ignore transient fetch errors
      }
    }, 3000);
  }

  useEffect(() => () => stopPolling(), []);

  async function handleRun() {
    setStatus("running");
    setStep("Starting…");
    try {
      const res = await fetch("/api/run-digest", { method: "POST" });
      if (!res.ok) throw new Error(await res.text());
      startPolling();
    } catch {
      setStatus("error");
      setStep("Failed to start pipeline");
      setTimeout(() => {
        setStatus("idle");
        setStep("");
      }, 4000);
    }
  }

  const isRunning = status === "running";
  const isDone = status === "complete";
  const isError = status === "error";

  return (
    <div className="flex flex-col items-end gap-1.5">
      <button
        onClick={handleRun}
        disabled={isRunning || isDone}
        className={`px-4 py-2 rounded-xl text-sm font-semibold transition flex items-center gap-2 ${
          isRunning || isDone
            ? "bg-slate-100 text-slate-400 cursor-not-allowed"
            : isError
            ? "bg-red-500 text-white"
            : "bg-gray-800 hover:bg-gray-900 text-white"
        }`}
      >
        {isRunning && (
          <span className="w-3 h-3 border-2 border-slate-400 border-t-transparent rounded-full animate-spin" />
        )}
        {isDone ? "Done" : isError ? "Failed" : isRunning ? "Running…" : "Run Digest"}
      </button>

      {(isRunning || isDone || isError) && step && (
        <p className={`text-xs max-w-[220px] text-right leading-snug ${
          isError ? "text-red-500" : isDone ? "text-green-600" : "text-slate-400"
        }`}>
          {step}
        </p>
      )}
    </div>
  );
}
