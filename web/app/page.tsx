'use client';

import { useRef } from 'react';
import { motion, useInView } from 'framer-motion';
import ContinueWithGoogle from "./components/ContinueWithGoogle";
import { FallingPattern } from '@/components/ui/falling-pattern';
import { RadarSection } from './components/RadarSection';
import { HoverButton } from '@/components/ui/hover-button';
import { GooeyText } from '@/components/ui/gooey-text';

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
    title: "Anelo gets to work",
    description: "Anelo runs multiple times a day to grab the latest postings, identifies the best matches for your profile, tailors your resume for each one, and notifies you — so you're always first in line.",
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
            <HoverButton
              onClick={() => document.getElementById('waitlist')?.scrollIntoView({ behavior: 'smooth' })}
              backgroundColor="rgba(255,255,255,0.05)"
              glowColor="#9ca3af"
              textColor="#e5e7eb"
              hoverTextColor="#ffffff"
              className="!text-sm !py-2 !px-5 !rounded-full border border-white/10"
            >
              Try Anello
            </HoverButton>
          </div>
        </nav>

        {/* Radar — first thing visible */}
        <RadarSection />

        {/* Hero — reveals on scroll */}
        <section className="flex flex-col items-center justify-center px-6 py-28 text-center">
          <GooeyText
            texts={["Let jobs find you.", "Every single day.", "On autopilot."]}
            morphTime={1.2}
            cooldownTime={1.8}
            className="h-28 w-full"
            textClassName="font-extrabold tracking-tight text-white"
          />

          <FadeInSection delay={0.3}>
            <p className="text-lg sm:text-xl text-slate-400 max-w-xl mx-auto leading-relaxed mt-8 mb-10">
              Anelo scans the web, identifies the freshest job postings, and tailors your resume — every day, automatically.
            </p>
            <div id="waitlist" className="flex justify-center w-full">
              <ContinueWithGoogle />
            </div>
          </FadeInSection>
        </section>

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
