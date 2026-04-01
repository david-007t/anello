"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

export default function ApplyButton({ jobId }: { jobId: string }) {
  const [state, setState] = useState<"idle" | "loading" | "done" | "error" | "unsupported">("idle");
  const [detail, setDetail] = useState("");
  const [validateReasons, setValidateReasons] = useState<string[]>([]);
  const router = useRouter();

  async function handleApply() {
    setState("loading");
    setDetail("");
    setValidateReasons([]);
    try {
      const res = await fetch("/api/apply", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ job_id: jobId }),
      });
      const data = await res.json();

      if (!res.ok) {
        if (res.status === 422) {
          const reasons: string[] = data.detail?.reasons ?? [];
          setState("error");
          setValidateReasons(reasons);
          setDetail(reasons[0] ?? "Validation failed");
        } else {
          setState("error");
          setDetail(data.error ?? "Apply failed");
        }
        setTimeout(() => { setState("idle"); setDetail(""); setValidateReasons([]); }, 5000);
        return;
      }

      if (data.validate_warnings?.length > 0) {
        console.warn("[ApplyButton] validate_warnings:", data.validate_warnings);
      }

      if (data.success) {
        setState("done");
        setDetail("Application submitted");
        router.refresh();
      } else if (data.ats === "workday" || data.ats === "unknown") {
        setState("unsupported");
        setDetail("Open job link to apply manually");
        setTimeout(() => { setState("idle"); setDetail(""); setValidateReasons([]); }, 6000);
      } else {
        setState("error");
        setDetail("Apply failed — try again or apply manually");
        setTimeout(() => { setState("idle"); setDetail(""); setValidateReasons([]); }, 5000);
      }
    } catch {
      setState("error");
      setDetail("Network error");
      setTimeout(() => { setState("idle"); setDetail(""); setValidateReasons([]); }, 5000);
    }
  }

  const styles: Record<string, string> = {
    idle: "bg-emerald-600 hover:bg-emerald-700 text-white",
    loading: "bg-slate-100 text-slate-400 cursor-not-allowed",
    done: "bg-emerald-100 text-emerald-700 cursor-default",
    error: "bg-red-100 text-red-600 cursor-default",
    unsupported: "bg-amber-100 text-amber-700 cursor-default",
  };

  const labels: Record<string, string> = {
    idle: "Easy Apply",
    loading: "Applying…",
    done: "Applied ✓",
    error: "Failed",
    unsupported: "Manual Only",
  };

  return (
    <div className="flex flex-col gap-1">
      <button
        onClick={state === "idle" ? handleApply : undefined}
        disabled={state === "loading"}
        className={`text-xs font-medium px-3 py-1.5 rounded-lg transition-colors whitespace-nowrap ${styles[state]}`}
      >
        {state === "loading" && (
          <span className="inline-block w-2.5 h-2.5 border-2 border-slate-400 border-t-transparent rounded-full animate-spin mr-1.5 align-middle" />
        )}
        {labels[state]}
      </button>
      {detail && (
        <p className={`text-xs max-w-[160px] leading-snug ${
          state === "done" ? "text-emerald-600" :
          state === "unsupported" ? "text-amber-600" : "text-red-500"
        }`}>
          {detail}
        </p>
      )}
      {validateReasons.length > 0 && (
        <ul className="text-xs max-w-[160px] leading-snug text-amber-600 list-disc pl-3">
          {validateReasons.map((reason, i) => (
            <li key={i}>{reason}</li>
          ))}
        </ul>
      )}
    </div>
  );
}
