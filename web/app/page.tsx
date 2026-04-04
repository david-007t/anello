'use client';

import { useRef, useEffect } from 'react';
import { useScroll, useTransform, motion } from 'framer-motion';
import { useAuth } from '@clerk/nextjs';
import { useRouter } from 'next/navigation';
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

export default function HomePage() {
  const { isSignedIn, isLoaded } = useAuth();
  const router = useRouter();
  const spacerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (isLoaded && isSignedIn) router.push('/already-signed-in');
  }, [isLoaded, isSignedIn]);

  // Track window scroll progress (0 = top, 1 = bottom of page)
  const { scrollYProgress } = useScroll();

  // Sequential fades — each section fully gone before the next appears
  // Radar: visible → fades out 0.25–0.35, then stays at 0 for the rest of the scroll
  const radarOpacity = useTransform(scrollYProgress, [0, 0.25, 0.35, 1.0], [1, 1, 0, 0]);
  // Belt-and-suspenders: also hide via visibility once opacity hits 0
  const radarVisibility = useTransform(radarOpacity, (v) => (v <= 0 ? 'hidden' : 'visible'));
  // Hero: fades in 0.35–0.44, holds, fades out 0.60–0.68
  const heroOpacity = useTransform(scrollYProgress, [0.35, 0.44, 0.60, 0.68], [0, 1, 1, 0]);
  // How It Works: fades in 0.68–0.77, holds to end
  const howOpacity = useTransform(scrollYProgress, [0.68, 0.77, 1.0], [0, 1, 1]);

  // Scroll hint fades out as user starts scrolling
  const hintOpacity = useTransform(scrollYProgress, [0, 0.08], [1, 0]);

  function scrollToHero() {
    if (!spacerRef.current) return;
    const scrollable = spacerRef.current.offsetHeight - window.innerHeight;
    window.scrollTo({ top: scrollable * 0.44, behavior: 'smooth' });
  }

  return (
    <div className="text-white" style={{ background: '#000' }}>
      <FallingPattern
        color="rgba(255,255,255,0.3)"
        backgroundColor="#000000"
        duration={120}
        blurIntensity="1em"
        density={1}
        className="fixed inset-0 z-0"
      />

      {/* Nav — fixed, always on top */}
      <nav className="fixed top-0 left-0 right-0 z-50 border-b border-white/10 bg-black/80 backdrop-blur-md">
        <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
          <span className="text-xl font-black tracking-tight text-white">anelo</span>
          <HoverButton
            onClick={scrollToHero}
            backgroundColor="rgba(255,255,255,0.05)"
            glowColor="#9ca3af"
            textColor="#e5e7eb"
            hoverTextColor="#ffffff"
            className="!text-sm !py-2 !px-5 !rounded-full border border-white/10"
          >
            Try Anelo
          </HoverButton>
        </div>
      </nav>

      {/* 300vh spacer — window scrolls through this, driving all animations */}
      <div ref={spacerRef} style={{ height: '300vh' }} className="relative z-10">
        {/* Sticky frame — stays fixed in viewport while page scrolls */}
        <div className="sticky top-0 h-screen overflow-hidden">

          {/* Section 1: Radar */}
          <motion.div
            style={{ opacity: radarOpacity, visibility: radarVisibility, pointerEvents: 'none' }}
            className="absolute inset-0 flex items-center justify-center pt-16"
          >
            <RadarSection />
            {/* Scroll hint */}
            <motion.div
              style={{ opacity: hintOpacity }}
              className="absolute bottom-20 left-1/2 -translate-x-1/2 flex flex-col items-center gap-2"
            >
              <span className="text-xs text-white/30 tracking-widest uppercase">scroll</span>
              <motion.svg
                width="16"
                height="16"
                viewBox="0 0 16 16"
                fill="none"
                animate={{ y: [0, 4, 0] }}
                transition={{ repeat: Infinity, duration: 1.4, ease: 'easeInOut' }}
              >
                <path d="M8 3v10M4 9l4 4 4-4" stroke="rgba(255,255,255,0.3)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
              </motion.svg>
            </motion.div>
          </motion.div>

          {/* Section 2: Hero */}
          <motion.div
            style={{ opacity: heroOpacity }}
            className="absolute inset-0 flex flex-col items-center justify-center px-6 text-center pt-16"
          >
            <GooeyText
              texts={["Let jobs find you.", "Every single day.", "On autopilot."]}
              morphTime={1.2}
              cooldownTime={1.8}
              className="h-28 w-full"
              textClassName="font-extrabold tracking-tight text-white"
            />
            <p className="text-lg sm:text-xl text-slate-400 max-w-xl mx-auto leading-relaxed mt-8 mb-10">
              Anelo scans the web, identifies the freshest job postings, and tailors your resume — every day, automatically.
            </p>
            <ContinueWithGoogle />
          </motion.div>

          {/* Section 3: How It Works */}
          <motion.div
            style={{ opacity: howOpacity, pointerEvents: 'none' }}
            className="absolute inset-0 flex items-center justify-center pt-16"
          >
            <div className="max-w-6xl mx-auto px-6 w-full">
              <div className="text-center mb-12">
                <h2 className="text-3xl sm:text-4xl font-bold text-white mb-3">How it works</h2>
                <p className="text-slate-400 text-base max-w-xl mx-auto">Three steps. Then sit back.</p>
              </div>
              <div className="grid md:grid-cols-3 gap-10">
                {steps.map((s) => (
                  <div key={s.step}>
                    <span className="text-7xl font-black text-white/10 select-none leading-none block mb-4">{s.step}</span>
                    <h3 className="text-lg font-semibold text-white mb-2">{s.title}</h3>
                    <p className="text-slate-400 text-sm leading-relaxed">{s.description}</p>
                  </div>
                ))}
              </div>
            </div>
          </motion.div>

        </div>
      </div>

      {/* Footer */}
      <footer className="relative z-10 border-t border-white/10 py-4 bg-black/60 backdrop-blur-md">
        <div className="max-w-6xl mx-auto px-6 flex items-center justify-between">
          <span className="text-sm font-black text-white">anelo</span>
          <p className="text-xs text-slate-500">© {new Date().getFullYear()} Anelo. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
}
