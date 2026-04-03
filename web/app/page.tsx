import WaitlistForm from "./components/WaitlistForm";
import { GradientDots } from '@/components/ui/gradient-dots';
import { Radar, IconContainer } from "@/components/ui/radar";

const features = [
  {
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
      </svg>
    ),
    title: "Daily Job Digest",
    description:
      "Every morning, Anelo sends you a curated list of jobs matched to your skills, preferences, and salary target.",
  },
  {
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
      </svg>
    ),
    title: "AI Resume Tailoring",
    description:
      "Your resume is automatically rewritten and optimized for every single job before it's sent — no copy-paste, no templates.",
  },
  {
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M13 10V3L4 14h7v7l9-11h-7z" />
      </svg>
    ),
    title: "Auto-Apply",
    description:
      "Anelo submits your applications across Greenhouse, Lever, Workday, and more — including custom screening questions.",
  },
  {
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
      </svg>
    ),
    title: "Application Tracker",
    description:
      "A clean dashboard showing every application — status, role, company, ATS type, and which resume version was sent.",
  },
];

const steps = [
  {
    step: "01",
    title: "Upload your resume",
    description:
      "Drop in your master resume. Anelo learns your skills, experience, and voice.",
  },
  {
    step: "02",
    title: "Set your preferences",
    description:
      "Tell Anelo what you're looking for: role, location, salary, and company types.",
  },
  {
    step: "03",
    title: "Anelo does the rest",
    description:
      "Every morning, fresh jobs. Every application, a tailored resume. All on autopilot.",
  },
];

const plans = [
  {
    name: "Free Trial",
    price: "$0",
    period: "14 days",
    description: "See what Anelo can do — no card required.",
    features: [
      "10 job applications",
      "Daily job digest",
      "AI resume tailoring",
      "Application tracker",
    ],
    cta: "Join Waitlist",
    highlight: false,
  },
  {
    name: "Starter",
    price: "$30",
    period: "per month",
    description: "For active job seekers ready to move fast.",
    features: [
      "30 applications / month",
      "Daily job digest",
      "AI resume tailoring",
      "Auto-apply (Greenhouse, Lever)",
      "Application tracker",
      "Email support",
    ],
    cta: "Join Waitlist",
    highlight: true,
  },
  {
    name: "Pro",
    price: "Coming soon",
    period: "",
    description: "Unlimited applications, priority support, and more.",
    features: [
      "Unlimited applications",
      "All Starter features",
      "Multi-resume variants",
      "Cover letter generation",
      "Priority support",
    ],
    cta: "Join Waitlist",
    highlight: false,
  },
];

export default function HomePage() {
  return (
    <div className="min-h-screen text-white">
      <GradientDots
        duration={20}
        colorCycleDuration={8}
        backgroundColor="#000000"
        className="fixed inset-0 z-0"
      />
      <div className="relative z-10">
      {/* Nav */}
      <nav className="sticky top-0 z-50 border-b border-white/10 bg-black/80 backdrop-blur-md">
        <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
          <span className="text-xl font-black tracking-tight text-white">
            anelo
          </span>
          <a
            href="#waitlist"
            className="px-4 py-2 text-sm font-semibold text-white bg-brand-600 hover:bg-brand-700 rounded-lg transition"
          >
            Join Waitlist
          </a>
        </div>
      </nav>

      {/* Hero */}
      <section className="relative min-h-screen flex flex-col items-center justify-center px-6 overflow-hidden">
        {/* Headline */}
        <div className="text-center mb-12 z-10">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-white/10 border border-white/20 text-white/80 text-xs font-medium mb-8">
            <span className="w-1.5 h-1.5 rounded-full bg-white animate-pulse" />
            Now accepting early access
          </div>
          <h1 className="text-5xl sm:text-6xl lg:text-7xl font-extrabold tracking-tight text-white leading-[1.1] mb-6">
            Your jobs{" "}
            <span className="text-brand-400">come to you.</span>
          </h1>
          <p className="text-lg sm:text-xl text-slate-400 max-w-2xl mx-auto leading-relaxed">
            Anelo scans the web, tailors your resume, and auto-applies — every day, on autopilot.
          </p>
        </div>

        {/* Radar + orbiting job icons */}
        <div className="relative flex items-center justify-center z-10 mb-14">
          <Radar className="h-72 w-72 md:h-96 md:w-96" />

          {/* Top */}
          <div className="absolute -top-8 left-1/2 -translate-x-1/2">
            <IconContainer
              delay={0.3}
              text="LinkedIn"
              icon={
                <svg className="h-6 w-6 text-sky-400" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433a2.062 2.062 0 01-2.063-2.065 2.064 2.064 0 112.063 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z" />
                </svg>
              }
            />
          </div>

          {/* Top-right */}
          <div className="absolute top-4 right-0 translate-x-1/2 md:translate-x-full">
            <IconContainer
              delay={0.5}
              text="Indeed"
              icon={
                <svg className="h-6 w-6 text-blue-400" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M12 0C5.373 0 0 5.373 0 12s5.373 12 12 12 12-5.373 12-12S18.627 0 12 0zm0 4a2 2 0 110 4 2 2 0 010-4zm3 15h-6v-1h1.5V11H9v-1h4.5v8H15v1z" />
                </svg>
              }
            />
          </div>

          {/* Right */}
          <div className="absolute right-0 top-1/2 -translate-y-1/2 translate-x-3/4 md:translate-x-full">
            <IconContainer
              delay={0.7}
              text="Greenhouse"
              icon={
                <svg className="h-6 w-6 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
                </svg>
              }
            />
          </div>

          {/* Bottom-right */}
          <div className="absolute bottom-4 right-0 translate-x-1/2 md:translate-x-full">
            <IconContainer
              delay={0.9}
              text="Lever"
              icon={
                <svg className="h-6 w-6 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
              }
            />
          </div>

          {/* Bottom */}
          <div className="absolute -bottom-8 left-1/2 -translate-x-1/2">
            <IconContainer
              delay={1.1}
              text="Workday"
              icon={
                <svg className="h-6 w-6 text-orange-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                </svg>
              }
            />
          </div>

          {/* Bottom-left */}
          <div className="absolute bottom-4 left-0 -translate-x-1/2 md:-translate-x-full">
            <IconContainer
              delay={1.3}
              text="Ashby"
              icon={
                <svg className="h-6 w-6 text-pink-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              }
            />
          </div>

          {/* Left */}
          <div className="absolute left-0 top-1/2 -translate-y-1/2 -translate-x-3/4 md:-translate-x-full">
            <IconContainer
              delay={1.5}
              text="Wellfound"
              icon={
                <svg className="h-6 w-6 text-yellow-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
                </svg>
              }
            />
          </div>

          {/* Top-left */}
          <div className="absolute top-4 left-0 -translate-x-1/2 md:-translate-x-full">
            <IconContainer
              delay={1.7}
              text="Rippling"
              icon={
                <svg className="h-6 w-6 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
              }
            />
          </div>
        </div>

        {/* CTA */}
        <div className="flex justify-center z-10" id="waitlist">
          <WaitlistForm />
        </div>
      </section>

      {/* How it works */}
      <section className="py-20">
        <div className="max-w-6xl mx-auto px-6">
          <div className="text-center mb-14">
            <h2 className="text-3xl sm:text-4xl font-bold text-white mb-3">
              How it works
            </h2>
            <p className="text-slate-400 text-base max-w-xl mx-auto">
              Three steps. Then sit back.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-10">
            {steps.map((s) => (
              <div key={s.step}>
                <span className="text-7xl font-black text-white/10 select-none leading-none block mb-4">
                  {s.step}
                </span>
                <h3 className="text-lg font-semibold text-white mb-2">
                  {s.title}
                </h3>
                <p className="text-slate-400 text-sm leading-relaxed">
                  {s.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="py-20">
        <div className="max-w-6xl mx-auto px-6">
          <div className="text-center mb-14">
            <h2 className="text-3xl sm:text-4xl font-bold text-white mb-3">
              Everything you need to land a job
            </h2>
            <p className="text-slate-400 text-base max-w-xl mx-auto">
              Anelo handles the entire funnel so you can focus on interviews.
            </p>
          </div>

          <div className="grid sm:grid-cols-2 gap-6">
            {features.map((f) => (
              <div
                key={f.title}
                className="p-6 rounded-2xl border border-white/10 bg-white/5 hover:border-white/20 transition"
              >
                <div className="w-10 h-10 rounded-xl bg-white/10 text-white flex items-center justify-center mb-4">
                  {f.icon}
                </div>
                <h3 className="font-semibold text-white mb-2">{f.title}</h3>
                <p className="text-sm text-slate-400 leading-relaxed">
                  {f.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Pricing */}
      <section className="py-20">
        <div className="max-w-6xl mx-auto px-6">
          <div className="text-center mb-14">
            <h2 className="text-3xl sm:text-4xl font-bold text-white mb-3">
              Simple pricing
            </h2>
            <p className="text-slate-400 text-base max-w-xl mx-auto">
              Start free. Upgrade when you&apos;re ready.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-6">
            {plans.map((p) => (
              <div
                key={p.name}
                className={`rounded-2xl p-7 border flex flex-col ${
                  p.highlight
                    ? "bg-brand-600 border-brand-600 text-white shadow-xl"
                    : "bg-white/5 border-white/10"
                }`}
              >
                <div className="mb-6">
                  <p
                    className={`text-sm font-semibold mb-1 ${
                      p.highlight ? "text-brand-100" : "text-brand-400"
                    }`}
                  >
                    {p.name}
                  </p>
                  <div className="flex items-baseline gap-1 mb-2">
                    <span
                      className={`text-4xl font-black ${
                        p.highlight ? "text-white" : "text-white"
                      }`}
                    >
                      {p.price}
                    </span>
                    {p.period && (
                      <span
                        className={`text-sm ${
                          p.highlight ? "text-brand-100" : "text-slate-400"
                        }`}
                      >
                        /{p.period}
                      </span>
                    )}
                  </div>
                  <p
                    className={`text-sm ${
                      p.highlight ? "text-brand-100" : "text-slate-400"
                    }`}
                  >
                    {p.description}
                  </p>
                </div>

                <ul className="space-y-3 mb-8 flex-1">
                  {p.features.map((feat) => (
                    <li key={feat} className="flex items-center gap-2.5 text-sm">
                      <svg
                        className={`w-4 h-4 shrink-0 ${
                          p.highlight ? "text-brand-200" : "text-brand-400"
                        }`}
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2.5}
                          d="M5 13l4 4L19 7"
                        />
                      </svg>
                      <span
                        className={p.highlight ? "text-white" : "text-slate-300"}
                      >
                        {feat}
                      </span>
                    </li>
                  ))}
                </ul>

                <a
                  href="#waitlist"
                  className={`block text-center py-3 px-6 rounded-xl font-semibold text-sm transition ${
                    p.highlight
                      ? "bg-white text-brand-600 hover:bg-brand-50"
                      : "bg-brand-600 text-white hover:bg-brand-700"
                  }`}
                >
                  {p.cta}
                </a>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Bottom CTA */}
      <section className="py-20">
        <div className="max-w-2xl mx-auto px-6 text-center">
          <h2 className="text-3xl sm:text-4xl font-bold text-white mb-4">
            Stop applying. Start getting offers.
          </h2>
          <p className="text-slate-400 mb-10 text-base leading-relaxed">
            Join the waitlist and be first to access Anelo when we launch.
          </p>
          <div className="flex justify-center">
            <WaitlistForm />
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-white/10 py-8">
        <div className="max-w-6xl mx-auto px-6 flex flex-col sm:flex-row items-center justify-between gap-4">
          <span className="text-sm font-black text-white">anelo</span>
          <p className="text-xs text-slate-500">
            © {new Date().getFullYear()} Anelo. All rights reserved.
          </p>
          <a
            href="mailto:hello@anelo.io"
            className="text-xs text-slate-500 hover:text-slate-300 transition"
          >
            Contact
          </a>
        </div>
      </footer>
      </div>
    </div>
  );
}
