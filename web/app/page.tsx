'use client';

import { useRef } from 'react';
import { motion, useInView } from 'framer-motion';
import WaitlistForm from "./components/WaitlistForm";
import { FallingPattern } from '@/components/ui/falling-pattern';
import { RadarSection } from './components/RadarSection';
import { HoverButton } from '@/components/ui/hover-button';

const features = [
  {
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
      </svg>
    ),
    title: "Daily Job Digest",
    description: "Every morning, Anelo sends you a curated list of jobs matched to your skills, preferences, and salary target.",
  },
  {
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
      </svg>
    ),
    title: "AI Resume Tailoring",
    description: "Your resume is automatically rewritten and optimized for every single job before it's sent — no copy-paste, no templates.",
  },
  {
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M13 10V3L4 14h7v7l9-11h-7z" />
      </svg>
    ),
    title: "Auto-Apply",
    description: "Anelo submits your applications across Greenhouse, Lever, Workday, and more — including custom screening questions.",
  },
  {
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
      </svg>
    ),
    title: "Application Tracker",
    description: "A clean dashboard showing every application — status, role, company, ATS type, and which resume version was sent.",
  },
];

const steps = [
  {
    step: "01",
    title: "Upload your resume",
    description: "Drop in your master resume. Anelo learns your skills, experience, and voice.",
  },
  {
    step: "02",
    title: "Set your preferences",
    description: "Tell Anelo what you're looking for: role, location, salary, and company types.",
  },
  {
    step: "03",
    title: "Anelo does the rest",
    description: "Every morning, fresh jobs. Every application, a tailored resume. All on autopilot.",
  },
];

function FadeInSection({ children, delay = 0 }: { children: React.ReactNode; delay?: number }) {
  const ref = useRef<HTMLDivElement>(null);
  const isInView = useInView(ref, { once: false, amount: 0.2 });
  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, y: 32 }}
      animate={isInView ? { opacity: 1, y: 0 } : { opacity: 0, y: 32 }}
      transition={{ duration: 0.5, delay, ease: 'easeOut' }}
    >
      {children}
    </motion.div>
  );
}

export default function HomePage() {
  return (
    <div className="min-h-screen text-white">
      <FallingPattern
        color="rgba(255,255,255,0.3)"
        backgroundColor="#000000"
        duration={120}
        blurIntensity="1em"
        density={1}
        className="fixed inset-0 z-0"
      />
      <div className="relative z-10">
        {/* Nav */}
        <nav className="sticky top-0 z-50 border-b border-white/10 bg-black/80 backdrop-blur-md">
          <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
            <span className="text-xl font-black tracking-tight text-white">anelo</span>
            <HoverButton onClick={() => document.getElementById('waitlist')?.scrollIntoView({ behavior: 'smooth' })}>
              Join Waitlist
            </HoverButton>
          </div>
        </nav>

        {/* Hero */}
        <section className="flex flex-col items-center justify-center px-6 pt-28 pb-20 text-center">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-white/10 border border-white/20 text-white/80 text-xs font-medium mb-8">
            <span className="w-1.5 h-1.5 rounded-full bg-white animate-pulse" />
            Now accepting early access
          </div>
          <h1 className="text-5xl sm:text-6xl lg:text-8xl font-extrabold tracking-tight text-white leading-[1.05] mb-6">
            Let jobs<br />find you.
          </h1>
          <p className="text-lg sm:text-xl text-slate-400 max-w-xl mx-auto leading-relaxed mb-10">
            Anelo scans the web, tailors your resume, and auto-applies — every day, on autopilot.
          </p>
          <div id="waitlist" className="flex justify-center w-full">
            <WaitlistForm />
          </div>
        </section>

        {/* Radar section */}
        <RadarSection />

        {/* How it works */}
        <section className="py-14">
          <div className="max-w-6xl mx-auto px-6">
            <FadeInSection>
              <div className="text-center mb-12">
                <h2 className="text-3xl sm:text-4xl font-bold text-white mb-3">How it works</h2>
                <p className="text-slate-400 text-base max-w-xl mx-auto">Three steps. Then sit back.</p>
              </div>
            </FadeInSection>
            <div className="grid md:grid-cols-3 gap-10">
              {steps.map((s, i) => (
                <FadeInSection key={s.step} delay={i * 0.1}>
                  <span className="text-7xl font-black text-white/10 select-none leading-none block mb-4">{s.step}</span>
                  <h3 className="text-lg font-semibold text-white mb-2">{s.title}</h3>
                  <p className="text-slate-400 text-sm leading-relaxed">{s.description}</p>
                </FadeInSection>
              ))}
            </div>
          </div>
        </section>

        {/* Features */}
        <section className="py-14">
          <div className="max-w-6xl mx-auto px-6">
            <FadeInSection>
              <div className="text-center mb-12">
                <h2 className="text-3xl sm:text-4xl font-bold text-white mb-3">Everything you need to land a job</h2>
                <p className="text-slate-400 text-base max-w-xl mx-auto">Anelo handles the entire funnel so you can focus on interviews.</p>
              </div>
            </FadeInSection>
            <div className="grid sm:grid-cols-2 gap-6">
              {features.map((f, i) => (
                <FadeInSection key={f.title} delay={i * 0.1}>
                  <div className="p-6 rounded-2xl border border-white/10 bg-white/5 hover:border-white/20 transition h-full">
                    <div className="w-10 h-10 rounded-xl bg-white/5 text-white flex items-center justify-center mb-4">
                      {f.icon}
                    </div>
                    <h3 className="font-semibold text-white mb-2">{f.title}</h3>
                    <p className="text-sm text-slate-400 leading-relaxed">{f.description}</p>
                  </div>
                </FadeInSection>
              ))}
            </div>
          </div>
        </section>

        {/* Footer */}
        <footer className="border-t border-white/10 py-8">
          <div className="max-w-6xl mx-auto px-6 flex flex-col sm:flex-row items-center justify-between gap-4">
            <span className="text-sm font-black text-white">anelo</span>
            <p className="text-xs text-slate-500">© {new Date().getFullYear()} Anelo. All rights reserved.</p>
            <a href="mailto:hello@anelo.io" className="text-xs text-slate-500 hover:text-slate-300 transition">Contact</a>
          </div>
        </footer>
      </div>
    </div>
  );
}
