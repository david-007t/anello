"use client";
import { motion } from "framer-motion";
import { twMerge } from "tailwind-merge";
import React, { useState, useEffect } from "react";

export const Circle = ({ className, children, idx, ...rest }: any) => {
  return (
    <motion.div
      {...rest}
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ delay: idx * 0.1, duration: 0.2 }}
      className={twMerge(
        "absolute inset-0 left-1/2 top-1/2 h-10 w-10 -translate-x-1/2 -translate-y-1/2 transform rounded-full border border-neutral-200",
        className
      )}
    />
  );
};

export const Radar = ({ className }: { className?: string }) => {
  const circles = new Array(8).fill(1);
  const [clock, setClock] = useState({ h: 0, m: 0, s: 0 });

  useEffect(() => {
    const update = () => {
      const now = new Date();
      setClock({ h: now.getHours(), m: now.getMinutes(), s: now.getSeconds() });
    };
    update();
    const id = setInterval(update, 1000);
    return () => clearInterval(id);
  }, []);

  const cx = 20, cy = 20;
  const hand = (deg: number, len: number) => {
    const r = (deg * Math.PI) / 180;
    return { x2: cx + len * Math.sin(r), y2: cy - len * Math.cos(r) };
  };
  const secDeg = (clock.s / 60) * 360;
  const minDeg = (clock.m / 60) * 360 + (clock.s / 60) * 6;
  const hrDeg  = ((clock.h % 12) / 12) * 360 + (clock.m / 60) * 30;
  const sec = hand(secDeg, 16);
  const min = hand(minDeg, 13);
  const hr  = hand(hrDeg, 9);

  return (
    <div
      className={twMerge(
        "relative flex h-20 w-20 items-center justify-center rounded-full",
        className
      )}
    >
      <style>{`
        @keyframes radar-spin {
          from { transform: rotate(20deg); }
          to   { transform: rotate(380deg); }
        }
        .animate-radar-spin {
          animation: radar-spin 10s linear infinite;
        }
      `}</style>
      {/* Rotating sweep line */}
      <div
        style={{ transformOrigin: "right center" }}
        className="animate-radar-spin absolute right-1/2 top-1/2 z-40 flex h-[5px] w-[400px] items-end justify-center overflow-hidden bg-transparent"
      >
        <div className="relative z-40 h-[1px] w-full bg-gradient-to-r from-transparent via-sky-500 to-transparent" />
      </div>
      {/* Analog clock hands */}
      <div className="absolute z-50 flex items-center justify-center">
        <svg width="40" height="40" viewBox="0 0 40 40">
          {/* hour */}
          <line x1={cx} y1={cy} x2={hr.x2} y2={hr.y2} stroke="rgba(255,255,255,0.7)" strokeWidth="2.5" strokeLinecap="round" />
          {/* minute */}
          <line x1={cx} y1={cy} x2={min.x2} y2={min.y2} stroke="rgba(255,255,255,0.55)" strokeWidth="1.5" strokeLinecap="round" />
          {/* second */}
          <line x1={cx} y1={cy} x2={sec.x2} y2={sec.y2} stroke="rgba(255,255,255,0.35)" strokeWidth="0.75" strokeLinecap="round" />
          {/* center dot */}
          <circle cx={cx} cy={cy} r="1.5" fill="rgba(255,255,255,0.6)" />
        </svg>
      </div>
      {/* Concentric circles */}
      {circles.map((_, idx) => (
        <Circle
          style={{
            height: `${(idx + 1) * 5}rem`,
            width: `${(idx + 1) * 5}rem`,
            border: `1px solid rgba(71, 85, 105, ${1 - (idx + 1) * 0.1})`,
          }}
          key={`circle-${idx}`}
          idx={idx}
        />
      ))}
    </div>
  );
};

export const IconContainer = ({
  icon,
  text,
  delay,
  visible = true,
}: {
  icon?: React.ReactNode;
  text?: string;
  delay?: number;
  visible?: boolean;
}) => {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={visible ? { opacity: 1, scale: 1 } : { opacity: 0, scale: 0.95 }}
      transition={{ duration: 0.4, delay: delay ?? 0 }}
      className="relative z-50 flex flex-col items-center justify-center space-y-2"
    >
      <div className="flex h-12 w-12 items-center justify-center rounded-2xl border border-white/10 bg-white/5 backdrop-blur-sm shadow-inner">
        {icon || (
          <svg className="h-8 w-8 text-slate-600" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" clipRule="evenodd" />
          </svg>
        )}
      </div>
      <div className="hidden rounded-md px-2 py-1 md:block">
        <div className="text-center text-xs font-bold text-slate-400">
          {text || "Web Development"}
        </div>
      </div>
    </motion.div>
  );
};
