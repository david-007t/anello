import WaitlistForm from "./components/WaitlistForm";
import { DottedSurface } from '@/components/dotted-surface';

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
    <div className="min-h-screen bg-black text-white">
      <DottedSurface />
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
      <section className="max-w-6xl mx-auto px-6 pt-24 pb-20 text-center">
        <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-white/10 border border-white/20 text-white/80 text-xs font-medium mb-8">
          <span className="w-1.5 h-1.5 rounded-full bg-white animate-pulse" />
          Now accepting early access
        </div>

        <h1 className="text-5xl sm:text-6xl lg:text-7xl font-extrabold tracking-tight text-white leading-[1.1] mb-6">
          Your jobs{" "}
          <span className="text-brand-400">come to you.</span>
        </h1>

        <p className="text-lg sm:text-xl text-slate-400 max-w-2xl mx-auto mb-10 leading-relaxed">
          Anelo is an AI job agent that finds relevant openings, tailors your
          resume for each one, and submits applications — automatically, every
          day.
        </p>

        <div className="flex justify-center" id="waitlist">
          <WaitlistForm />
        </div>
      </section>

      {/* How it works */}
      <section className="bg-white/5 border-y border-white/10 py-20">
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
      <section className="bg-white/5 border-y border-white/10 py-20">
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
  );
}
