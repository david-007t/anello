'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useUser } from '@clerk/nextjs';
import { motion } from 'framer-motion';
import { FallingPattern } from '@/components/ui/falling-pattern';
import { HoverButton } from '@/components/ui/hover-button';

interface FormState {
  role: string;
  role_2: string;
  role_3: string;
  location: string;
  experience_min: string;
  experience_max: string;
  min_salary: string;
  company_types: string;
  skills: string;
}

const inputClass =
  'w-full px-4 py-3 rounded-xl bg-white/[0.08] border border-white/20 text-white placeholder-white/30 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent';

const labelClass = 'text-sm font-medium text-white/70 mb-1.5 block';

export default function OnboardingPage() {
  const router = useRouter();
  const { isLoaded, isSignedIn } = useUser();
  const [step, setStep] = useState<1 | 2>(1);
  const [submitting, setSubmitting] = useState(false);
  const [form, setForm] = useState<FormState>({
    role: '',
    role_2: '',
    role_3: '',
    location: '',
    experience_min: '',
    experience_max: '',
    min_salary: '',
    company_types: '',
    skills: '',
  });

  function set(key: keyof FormState, value: string) {
    setForm((f) => ({ ...f, [key]: value }));
  }

  async function handleSubmit() {
    setSubmitting(true);
    try {
      await fetch('/api/preferences', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form),
      });
    } catch {
      // proceed regardless
    }
    router.push('/dashboard');
  }

  if (!isLoaded) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center">
        <div className="w-6 h-6 border-2 border-white/20 border-t-white rounded-full animate-spin" />
      </div>
    );
  }

  if (!isSignedIn) {
    router.push('/sign-in');
    return null;
  }

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
          <div className="max-w-6xl mx-auto px-6 h-16 flex items-center">
            <a href="/" className="text-xl font-black tracking-tight text-white hover:opacity-80 transition-opacity">
              anelo
            </a>
          </div>
        </nav>

        {/* Content */}
        <div className="max-w-lg mx-auto px-6 py-16">
          {/* Step indicator */}
          <div className="flex items-center gap-4 mb-10">
            {/* Step 1 */}
            <div className="flex items-center gap-2">
              <div
                className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold transition-colors ${
                  step === 1 ? 'bg-white text-black' : 'bg-white/20 text-white/40'
                }`}
              >
                01
              </div>
              <span className={`text-sm font-medium transition-colors ${step === 1 ? 'text-white' : 'text-white/30'}`}>
                Target roles
              </span>
            </div>

            {/* Connector */}
            <div className="flex-1 h-px bg-white/10" />

            {/* Step 2 */}
            <div className="flex items-center gap-2">
              <div
                className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold transition-colors ${
                  step === 2 ? 'bg-white text-black' : 'bg-white/20 text-white/40'
                }`}
              >
                02
              </div>
              <span className={`text-sm font-medium transition-colors ${step === 2 ? 'text-white' : 'text-white/30'}`}>
                Filter noise
              </span>
            </div>
          </div>

          {/* Step counter */}
          <p className="text-xs text-white/40 mb-4">Step {step} of 2</p>

          {step === 1 && (
            <motion.div
              key="step-1"
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4, ease: 'easeOut' }}
            >
              <div className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-2xl p-8 space-y-6">
                <div>
                  <h1 className="text-3xl font-bold text-white mb-2">What are you targeting?</h1>
                  <p className="text-slate-400 text-sm">Tell Anelo what roles to hunt for.</p>
                </div>

                <div className="space-y-4">
                  <div>
                    <label className={labelClass}>Primary role</label>
                    <input
                      type="text"
                      value={form.role}
                      onChange={(e) => set('role', e.target.value)}
                      placeholder="e.g. Product Manager"
                      className={inputClass}
                    />
                  </div>
                  <div>
                    <label className={labelClass}>Role 2</label>
                    <input
                      type="text"
                      value={form.role_2}
                      onChange={(e) => set('role_2', e.target.value)}
                      placeholder="e.g. Technical Program Manager"
                      className={inputClass}
                    />
                  </div>
                  <div>
                    <label className={labelClass}>Role 3</label>
                    <input
                      type="text"
                      value={form.role_3}
                      onChange={(e) => set('role_3', e.target.value)}
                      placeholder="e.g. Senior Product Designer"
                      className={inputClass}
                    />
                  </div>
                  <div>
                    <label className={labelClass}>Location</label>
                    <input
                      type="text"
                      value={form.location}
                      onChange={(e) => set('location', e.target.value)}
                      placeholder="e.g. San Francisco, Remote"
                      className={inputClass}
                    />
                  </div>
                </div>

                <HoverButton
                  onClick={() => setStep(2)}
                  backgroundColor="rgba(255,255,255,0.05)"
                  glowColor="#9ca3af"
                  textColor="#e5e7eb"
                  hoverTextColor="#ffffff"
                  className="!text-base !py-3 !px-6 !rounded-xl border border-white/10 w-full"
                >
                  Continue →
                </HoverButton>
              </div>
            </motion.div>
          )}

          {step === 2 && (
            <motion.div
              key="step-2"
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4, ease: 'easeOut' }}
            >
              <div className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-2xl p-8 space-y-6">
                <div>
                  <h1 className="text-3xl font-bold text-white mb-2">Filter the noise.</h1>
                  <p className="text-slate-400 text-sm">Anelo will skip anything that doesn&apos;t match.</p>
                </div>

                <div className="space-y-4">
                  <div>
                    <label className={labelClass}>Years of experience</label>
                    <div className="flex items-center gap-3">
                      <input
                        type="number"
                        min={0}
                        value={form.experience_min}
                        onChange={(e) => set('experience_min', e.target.value)}
                        placeholder="Min"
                        className={`${inputClass} w-28`}
                      />
                      <span className="text-sm text-slate-400">to</span>
                      <input
                        type="number"
                        min={0}
                        value={form.experience_max}
                        onChange={(e) => set('experience_max', e.target.value)}
                        placeholder="Max"
                        className={`${inputClass} w-28`}
                      />
                      <span className="text-sm text-slate-400">years</span>
                    </div>
                  </div>

                  <div>
                    <label className={labelClass}>Minimum salary (USD)</label>
                    <input
                      type="text"
                      value={form.min_salary}
                      onChange={(e) => set('min_salary', e.target.value)}
                      placeholder="e.g. 120000"
                      className={inputClass}
                    />
                  </div>

                  <div>
                    <label className={labelClass}>Company types</label>
                    <input
                      type="text"
                      value={form.company_types}
                      onChange={(e) => set('company_types', e.target.value)}
                      placeholder="e.g. Startup, Series B, FAANG"
                      className={inputClass}
                    />
                  </div>

                  <div>
                    <label className={labelClass}>Skills to highlight</label>
                    <input
                      type="text"
                      value={form.skills}
                      onChange={(e) => set('skills', e.target.value)}
                      placeholder="e.g. React, Python, SQL"
                      className={inputClass}
                    />
                  </div>
                </div>

                <div className="flex flex-col gap-3">
                  <HoverButton
                    onClick={handleSubmit}
                    disabled={submitting}
                    backgroundColor="rgba(255,255,255,0.05)"
                    glowColor="#9ca3af"
                    textColor="#e5e7eb"
                    hoverTextColor="#ffffff"
                    className="!text-base !py-3 !px-6 !rounded-xl border border-white/10 w-full"
                  >
                    {submitting ? 'Starting…' : 'Start Anelo →'}
                  </HoverButton>
                  <button
                    onClick={() => setStep(1)}
                    className="text-sm text-white/40 hover:text-white/60 transition-colors text-center"
                  >
                    ← Back
                  </button>
                </div>
              </div>
            </motion.div>
          )}
        </div>
      </div>
    </div>
  );
}
