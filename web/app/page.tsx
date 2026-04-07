'use client';

import { useRef, useEffect, useState } from 'react';
import { useScroll, useTransform, motion } from 'framer-motion';
import { useAuth } from '@clerk/nextjs';
import { useRouter } from 'next/navigation';
import ContinueWithGoogle from "./components/ContinueWithGoogle";
import WaitlistForm from "./components/WaitlistForm";
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
    title: "Wake up to your daily digest",
    description: "Anelo runs multiple times a day, grabs the freshest postings, and scores each one against your profile. The best matches land in your inbox every morning — so you're always first in line.",
  },
];

// ── Social proof ──────────────────────────────────────────────────────────────
// Replace placeholder stats and testimonials with real data once available.

const stats = [
  { value: "8+", label: "Job boards scanned daily" },
  { value: "1 email", label: "Per day — no noise" },
  { value: "Free", label: "During early access" },
];

const testimonials = [
  {
    quote: "I stopped refreshing LinkedIn every hour. Anelo just sends me the good stuff.",
    name: "Jordan M.",
    role: "Product Designer",
  },
  {
    quote: "Got a recruiter call within 48 hours of signing up. The matching is surprisingly accurate.",
    name: "Priya K.",
    role: "Software Engineer",
  },
  {
    quote: "Finally a job search tool that doesn't make me feel like I'm doing it wrong.",
    name: "Marcus T.",
    role: "Marketing Manager",
  },
];

// ── FAQ ───────────────────────────────────────────────────────────────────────

const faqs = [
  {
    q: "Is it free?",
    a: "Yes — Anelo is free during early access. No credit card required.",
  },
  {
    q: "What job boards do you cover?",
    a: "We scan LinkedIn, Indeed, Greenhouse, Lever, Workday, Ashby, Wellfound, and Rippling — with more platforms being added regularly.",
  },
  {
    q: "Will you spam me?",
    a: "Never. You get one daily digest email with only the best matches for your profile. You can pause or unsubscribe at any time.",
  },
  {
    q: "Do you auto-apply to jobs without my approval?",
    a: "No. Right now Anelo sends you a curated digest so you stay in full control of every application. Auto-apply is on our roadmap and will always require your explicit opt-in.",
  },
  {
    q: "How does relevance scoring work?",
    a: "Anelo scores each posting against your resume, target role, experience level, and preferences — surfacing the roles most likely to lead to interviews.",
  },
];

function FAQItem({
  q,
  a,
  open,
  onToggle,
  isLast,
}: {
  q: string;
  a: string;
  open: boolean;
  onToggle: () => void;
  isLast?: boolean;
}) {
  return (
    <div className={isLast ? undefined : "border-b border-white/10"}>
      <button
        onClick={onToggle}
        className="w-full flex items-center justify-between py-3 text-left gap-4 cursor-pointer"
      >
        <span className="text-sm font-medium text-white">{q}</span>
        <span
          className="text-white/40 shrink-0 text-xl leading-none transition-transform duration-200"
          style={{ transform: open ? 'rotate(45deg)' : 'rotate(0deg)' }}
        >
          +
        </span>
      </button>
      <div
        style={{
          maxHeight: open ? '200px' : '0px',
          overflow: 'hidden',
          transition: 'max-height 0.25s ease',
        }}
      >
        <p className="pb-4 text-sm text-slate-400 leading-relaxed">{a}</p>
      </div>
    </div>
  );
}

// ── Page ──────────────────────────────────────────────────────────────────────

export default function HomePage() {
  const { isSignedIn, isLoaded } = useAuth();
  const router = useRouter();
  const spacerRef = useRef<HTMLDivElement>(null);
  const [openFaqIndex, setOpenFaqIndex] = useState<number | null>(null);

  useEffect(() => {
    if (isLoaded && isSignedIn) router.push('/already-signed-in');
  }, [isLoaded, isSignedIn]);

  // Track scroll progress relative to the spacer element so that content
  // outside the spacer (footer) doesn't affect animation keyframe positions.
  const { scrollYProgress } = useScroll({
    target: spacerRef,
    offset: ['start start', 'end end'],
  });

  // ── Scene opacities ────────────────────────────────────────────────────────
  // Spacer is 500vh → ~400vh of scroll travel. Six scenes fit across 0→1.
  // Each scene gets ~1/6 of the range; transitions take ~15% of each share.
  // Existing scene content and visual logic are unchanged — only keyframe
  // positions shift to accommodate three new scenes after "How it works".

  // Scene 1: Radar — visible at start, fades out by 0.165
  const radarOpacity = useTransform(scrollYProgress, [0, 0.10, 0.165, 1.0], [1, 1, 0, 0]);
  const radarVisibility = useTransform(radarOpacity, (v) => (v <= 0 ? 'hidden' : 'visible'));

  // Scene 2: Hero — fades in after radar, fades out before How It Works
  const heroOpacity = useTransform(scrollYProgress, [0.165, 0.21, 0.295, 0.33], [0, 1, 1, 0]);

  // Scene 3: How It Works — now has a fade-out so Scene 4 can follow
  const howOpacity = useTransform(scrollYProgress, [0.33, 0.37, 0.455, 0.50], [0, 1, 1, 0]);

  // Scene 4: Stats + Testimonials
  const statsOpacity = useTransform(scrollYProgress, [0.50, 0.54, 0.625, 0.665], [0, 1, 1, 0]);

  // Scene 5: Inbox Preview (hover-reveal card inside)
  const inboxOpacity = useTransform(scrollYProgress, [0.665, 0.705, 0.79, 0.83], [0, 1, 1, 0]);
  const inboxPointerEvents = useTransform(inboxOpacity, (v) => (v > 0.1 ? 'auto' : 'none'));

  // Scene 6: FAQ — stays fully visible at end of scroll
  const faqOpacity = useTransform(scrollYProgress, [0.83, 0.87, 1.0], [0, 1, 1]);
  const faqPointerEvents = useTransform(faqOpacity, (v) => (v > 0.1 ? 'auto' : 'none'));

  // Scroll hint — fades immediately
  const hintOpacity = useTransform(scrollYProgress, [0, 0.04], [1, 0]);

  function scrollToHero() {
    if (!spacerRef.current) return;
    const scrollable = spacerRef.current.offsetHeight - window.innerHeight;
    window.scrollTo({ top: scrollable * 0.21, behavior: 'smooth' });
  }

  function scrollToHowItWorks() {
    if (!spacerRef.current) return;
    const scrollable = spacerRef.current.offsetHeight - window.innerHeight;
    window.scrollTo({ top: scrollable * 0.40, behavior: 'smooth' });
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

      {/* 500vh spacer — window scrolls through this, driving all animations */}
      <div ref={spacerRef} style={{ height: '500vh' }} className="relative z-10">
        {/* Sticky frame — stays fixed in viewport while page scrolls */}
        <div className="sticky top-0 h-screen overflow-hidden">

          {/* Scene 1: Radar */}
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

          {/* Scene 2: Hero */}
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
              Anelo scans 8+ job boards daily, scores the best matches for your profile, and delivers a curated digest to your inbox — every morning.
            </p>
            <ContinueWithGoogle />
            <button
              onClick={scrollToHowItWorks}
              className="mt-5 text-sm text-white/40 hover:text-white/70 transition-colors cursor-pointer underline-offset-4 hover:underline"
            >
              See how it works ↓
            </button>
            {/* Email capture — alternative for users not ready for Google OAuth.
                Hidden on very small viewports to prevent overflow in the sticky container. */}
            <div className="hidden sm:block mt-8 w-full max-w-md">
              <div className="flex items-center gap-3 mb-6">
                <div className="flex-1 h-px bg-white/10" />
                <span className="text-xs text-white/30 uppercase tracking-widest">or join the waitlist</span>
                <div className="flex-1 h-px bg-white/10" />
              </div>
              <WaitlistForm />
            </div>
          </motion.div>

          {/* Scene 3: How It Works */}
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

          {/* Scene 4: Stats + Testimonials */}
          <motion.div
            style={{ opacity: statsOpacity, pointerEvents: 'none' }}
            className="absolute inset-0 flex items-center justify-center pt-16"
          >
            <div className="max-w-6xl mx-auto px-6 w-full">
              {/* Stat block */}
              <div className="grid grid-cols-3 gap-6 mb-16 text-center">
                {stats.map((s) => (
                  <div key={s.label}>
                    <p className="text-4xl sm:text-5xl font-black text-white mb-2">{s.value}</p>
                    <p className="text-sm text-slate-500">{s.label}</p>
                  </div>
                ))}
              </div>
              {/* Testimonial cards */}
              <div className="grid sm:grid-cols-3 gap-6">
                {testimonials.map((t) => (
                  <div
                    key={t.name}
                    className="border border-white/10 bg-white/5 backdrop-blur-sm rounded-2xl p-6"
                  >
                    <p className="text-sm text-slate-300 leading-relaxed mb-5">"{t.quote}"</p>
                    <div>
                      <p className="text-sm font-semibold text-white">{t.name}</p>
                      <p className="text-xs text-slate-500">{t.role}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </motion.div>

          {/* Scene 5: Inbox Preview
              The email card is hidden by default and revealed on hover via CSS transitions.
              No JS needed — opacity + translateY with group-hover. */}
          <motion.div
            style={{ opacity: inboxOpacity, pointerEvents: inboxPointerEvents }}
            className="absolute inset-0 flex items-center justify-center pt-16"
          >
            <div className="max-w-4xl mx-auto px-6 w-full">
              {/* group: hovering anywhere in this container reveals the card */}
              <div className="group">
                <h2 className="text-3xl sm:text-4xl font-bold text-white mb-4 text-center">Your inbox, upgraded</h2>
                <p className="text-slate-400 text-base max-w-xl mx-auto mb-10 text-center">
                  Every morning you get a short, scannable email with the roles most likely to fit — ranked by relevance, not recency.
                </p>
                {/* Card: hidden by default, fades in on hover */}
                {/* TODO: Replace this mock with a real screenshot of the daily digest email */}
                <div
                  className="opacity-0 translate-y-2 group-hover:opacity-100 group-hover:translate-y-0 transition-all duration-300 ease-out border border-white/10 bg-white/5 backdrop-blur-sm rounded-2xl overflow-hidden max-w-2xl mx-auto"
                >
                  {/* Email header */}
                  <div className="border-b border-white/10 px-6 py-4 flex items-center gap-3">
                    <div className="w-8 h-8 rounded-full bg-white/10 flex items-center justify-center shrink-0">
                      <span className="text-xs font-black text-white">a</span>
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-xs font-semibold text-white">Anelo · Your daily digest</p>
                      <p className="text-xs text-slate-500 truncate">3 new matches · Tuesday, April 7</p>
                    </div>
                    <span className="text-xs text-slate-600 shrink-0">8:02 AM</span>
                  </div>
                  {/* Job matches */}
                  <div className="divide-y divide-white/5">
                    {[
                      { title: "Senior Product Designer", company: "Linear", location: "Remote · US", score: 97, tag: "Top match" },
                      { title: "Product Designer", company: "Notion", location: "San Francisco, CA", score: 91, tag: "Strong fit" },
                      { title: "Design Systems Designer", company: "Figma", location: "Remote · US", score: 84, tag: "Good fit" },
                    ].map((job) => (
                      <div key={job.title} className="px-6 py-4 flex items-start justify-between gap-4">
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-semibold text-white">{job.title}</p>
                          <p className="text-xs text-slate-400 mt-0.5">{job.company} · {job.location}</p>
                        </div>
                        <div className="shrink-0 text-right">
                          <span className="inline-block px-2 py-0.5 rounded-full border border-white/10 text-xs text-slate-400">{job.tag}</span>
                          <p className="text-xs text-slate-600 mt-1">{job.score}% match</p>
                        </div>
                      </div>
                    ))}
                  </div>
                  {/* Email footer */}
                  <div className="border-t border-white/10 px-6 py-3 flex items-center justify-between">
                    <span className="text-xs text-slate-600">anelo.io</span>
                    <span className="text-xs text-slate-600">Unsubscribe · Manage preferences</span>
                  </div>
                </div>
              </div>
            </div>
          </motion.div>

          {/* Scene 6: FAQ
              All questions visible at once. One-at-a-time accordion with max-height transition.
              Panel is sized to fit comfortably within viewport height. */}
          <motion.div
            style={{ opacity: faqOpacity, pointerEvents: faqPointerEvents }}
            className="absolute inset-0 flex items-center justify-center pt-16"
          >
            <div className="max-w-2xl mx-auto px-6 w-full">
              <h2 className="text-2xl font-bold text-white mb-6 text-center">
                Frequently asked
              </h2>
              <div className="border border-white/10 bg-white/5 backdrop-blur-sm rounded-2xl px-6 py-2 max-w-2xl mx-auto">
                {faqs.map((f, i) => (
                  <FAQItem
                    key={f.q}
                    q={f.q}
                    a={f.a}
                    open={openFaqIndex === i}
                    onToggle={() => setOpenFaqIndex(openFaqIndex === i ? null : i)}
                    isLast={i === faqs.length - 1}
                  />
                ))}
              </div>
            </div>
          </motion.div>

        </div>
      </div>

      {/* ── Footer — outside the scroll-jacked area, always at bottom ─────── */}
      <footer className="relative z-10 border-t border-white/10 py-8 bg-black/60 backdrop-blur-md">
        <div className="max-w-6xl mx-auto px-6 flex flex-col sm:flex-row items-center justify-between gap-4">
          <span className="text-sm font-black text-white">anelo</span>
          <div className="flex items-center gap-6 text-xs text-slate-500">
            <a href="/privacy" className="hover:text-white/70 transition-colors">Privacy Policy</a>
            <a href="/terms" className="hover:text-white/70 transition-colors">Terms of Service</a>
            <a href="mailto:hello@anelo.io" className="hover:text-white/70 transition-colors">hello@anelo.io</a>
          </div>
          <p className="text-xs text-slate-500">© {new Date().getFullYear()} Anelo. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
}
