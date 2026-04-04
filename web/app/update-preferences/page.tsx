'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useUser } from '@clerk/nextjs';
import { motion } from 'framer-motion';
import { FallingPattern } from '@/components/ui/falling-pattern';
import { HoverButton } from '@/components/ui/hover-button';

interface FormState {
  ideal_job_title_1: string;
  ideal_job_title_2: string;
  ideal_job_title_3: string;
  target_salary: string;
  desired_locations: string;
  work_life_balance: string;
  company_culture: string;
  skills_to_acquire: string;
  industry_domain: string;
  values_impact: string;
}

const inputClass =
  'w-full px-4 py-3 rounded-xl bg-white/[0.08] border border-white/20 text-white placeholder-white/30 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent disabled:opacity-50';

const labelClass = 'text-sm font-medium text-white/70 mb-1.5 block';
const textareaClass = `${inputClass} resize-none`;

type View = 'form' | 'confirmed';
type Status = 'loading' | 'idle' | 'saving' | 'error';

export default function UpdatePreferencesPage() {
  const router = useRouter();
  const { isLoaded, isSignedIn } = useUser();
  const [view, setView] = useState<View>('form');
  const [status, setStatus] = useState<Status>('loading');
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [form, setForm] = useState<FormState>({
    ideal_job_title_1: '',
    ideal_job_title_2: '',
    ideal_job_title_3: '',
    target_salary: '',
    desired_locations: '',
    work_life_balance: 'Prefer not to say',
    company_culture: '',
    skills_to_acquire: '',
    industry_domain: '',
    values_impact: '',
  });

  useEffect(() => {
    if (!isLoaded) return;
    if (!isSignedIn) {
      router.push('/sign-in');
      return;
    }
    fetch('/api/preferences')
      .then((r) => r.json())
      .then(({ data }) => {
        if (data) {
          setForm((f) => ({
            ...f,
            ideal_job_title_1: data.role ?? '',
            ideal_job_title_2: data.role_2 ?? '',
            ideal_job_title_3: data.role_3 ?? '',
            target_salary: data.min_salary ?? '',
            desired_locations: data.location ?? '',
            company_culture: data.company_types ?? '',
            skills_to_acquire: data.skills ?? '',
            work_life_balance: data.work_life_balance ?? 'Prefer not to say',
            industry_domain: data.industry_domain ?? '',
            values_impact: data.values_impact ?? '',
          }));
        }
        setStatus('idle');
      })
      .catch(() => {
        setStatus('idle');
      });
  }, [isLoaded, isSignedIn, router]);

  function set(key: keyof FormState, value: string) {
    setForm((f) => ({ ...f, [key]: value }));
    setFieldErrors((e) => {
      const next = { ...e };
      delete next[key];
      return next;
    });
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const nextErrors: Record<string, string> = {};
    if (!form.ideal_job_title_1.trim()) {
      nextErrors.ideal_job_title_1 = 'At least one ideal job title is required.';
    }
    if (Object.keys(nextErrors).length > 0) {
      setFieldErrors(nextErrors);
      return;
    }
    setFieldErrors({});
    setErrorMsg(null);
    setStatus('saving');
    try {
      const res = await fetch('/api/preferences', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          role: form.ideal_job_title_1,
          role_2: form.ideal_job_title_2,
          role_3: form.ideal_job_title_3,
          location: form.desired_locations,
          experience_max: '',
          min_salary: form.target_salary,
          company_types: form.company_culture,
          skills: form.skills_to_acquire,
          work_life_balance: form.work_life_balance,
          industry_domain: form.industry_domain,
          values_impact: form.values_impact,
        }),
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        setErrorMsg(body?.error ?? 'Could not save your preferences. Please try again.');
        setStatus('error');
        return;
      }
      setStatus('idle');
      setView('confirmed');
    } catch {
      setErrorMsg('Network error. Please check your connection and try again.');
      setStatus('error');
    }
  }

  if (!isLoaded) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center">
        <div className="w-6 h-6 border-2 border-white/20 border-t-white rounded-full animate-spin" />
      </div>
    );
  }

  if (!isSignedIn) return null;

  const loading = status === 'loading';

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
        <nav className="sticky top-0 z-50 border-b border-white/10 bg-black/80 backdrop-blur-md">
          <div className="max-w-6xl mx-auto px-6 h-16 flex items-center">
            <a href="/" className="text-xl font-black tracking-tight text-white hover:opacity-80 transition-opacity">
              anelo
            </a>
          </div>
        </nav>

        <div className="max-w-lg mx-auto px-6 py-16">
          {loading ? (
            <div className="flex items-center justify-center py-24">
              <div className="w-6 h-6 border-2 border-white/20 border-t-white rounded-full animate-spin" />
            </div>
          ) : view === 'confirmed' ? (
            <motion.div
              key="confirmed"
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4, ease: 'easeOut' }}
            >
              <div className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-2xl p-8 flex flex-col items-center text-center space-y-4">
                <div className="w-14 h-14 rounded-full bg-indigo-500/20 border border-indigo-500/40 flex items-center justify-center mb-2">
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                    <path d="M5 13l4 4L19 7" stroke="#6366f1" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                </div>
                <h1 className="text-3xl font-bold text-white">Your Anelo has been updated.</h1>
                <p className="text-slate-400 text-sm leading-relaxed">
                  Your next digest will reflect these changes.
                </p>
                <a
                  href="/dashboard"
                  className="text-sm text-white/50 hover:text-white/80 transition-colors mt-2"
                >
                  ← Back to dashboard
                </a>
              </div>
            </motion.div>
          ) : (
            <motion.div
              key="form"
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4, ease: 'easeOut' }}
            >
              <div className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-2xl p-8 space-y-6">
                <div>
                  <h1 className="text-3xl font-bold text-white mb-2">Update your Anelo.</h1>
                  <p className="text-slate-400 text-sm">Refine what you&apos;re looking for.</p>
                </div>

                <form onSubmit={handleSubmit} className="space-y-4">
                  <div>
                    <label htmlFor="ideal_job_title_1" className={labelClass}>Ideal job title 1 *</label>
                    <input
                      id="ideal_job_title_1"
                      type="text"
                      value={form.ideal_job_title_1}
                      onChange={(e) => set('ideal_job_title_1', e.target.value)}
                      placeholder="e.g. Head of Product"
                      disabled={status === 'saving'}
                      className={inputClass}
                      aria-required="true"
                    />
                    {fieldErrors.ideal_job_title_1 && (
                      <p className="text-red-400 text-xs mt-1">{fieldErrors.ideal_job_title_1}</p>
                    )}
                  </div>

                  <div>
                    <label htmlFor="ideal_job_title_2" className={labelClass}>Ideal job title 2</label>
                    <input
                      id="ideal_job_title_2"
                      type="text"
                      value={form.ideal_job_title_2}
                      onChange={(e) => set('ideal_job_title_2', e.target.value)}
                      placeholder="e.g. VP Engineering"
                      disabled={status === 'saving'}
                      className={inputClass}
                    />
                  </div>

                  <div>
                    <label htmlFor="ideal_job_title_3" className={labelClass}>Ideal job title 3</label>
                    <input
                      id="ideal_job_title_3"
                      type="text"
                      value={form.ideal_job_title_3}
                      onChange={(e) => set('ideal_job_title_3', e.target.value)}
                      placeholder="e.g. Chief of Staff"
                      disabled={status === 'saving'}
                      className={inputClass}
                    />
                  </div>

                  <div>
                    <label htmlFor="target_salary" className={labelClass}>Target salary</label>
                    <input
                      id="target_salary"
                      type="text"
                      value={form.target_salary}
                      onChange={(e) => set('target_salary', e.target.value)}
                      placeholder="e.g. 180000"
                      disabled={status === 'saving'}
                      className={inputClass}
                    />
                  </div>

                  <div>
                    <label htmlFor="desired_locations" className={labelClass}>Desired locations</label>
                    <input
                      id="desired_locations"
                      type="text"
                      value={form.desired_locations}
                      onChange={(e) => set('desired_locations', e.target.value)}
                      placeholder="e.g. New York, Remote"
                      disabled={status === 'saving'}
                      className={inputClass}
                    />
                  </div>

                  <div>
                    <label htmlFor="work_life_balance" className={labelClass}>Work-life balance</label>
                    <select
                      id="work_life_balance"
                      value={form.work_life_balance}
                      onChange={(e) => set('work_life_balance', e.target.value)}
                      disabled={status === 'saving'}
                      className={inputClass}
                    >
                      <option value="Prefer not to say">Prefer not to say</option>
                      <option value="Balanced (9-5)">Balanced (9-5)</option>
                      <option value="Flexible hours">Flexible hours</option>
                      <option value="Remote-first">Remote-first</option>
                      <option value="High-growth / hustle">High-growth / hustle</option>
                    </select>
                  </div>

                  <div>
                    <label htmlFor="company_culture" className={labelClass}>Company culture</label>
                    <input
                      id="company_culture"
                      type="text"
                      value={form.company_culture}
                      onChange={(e) => set('company_culture', e.target.value)}
                      placeholder="e.g. Startup, mission-driven, collaborative"
                      disabled={status === 'saving'}
                      className={inputClass}
                    />
                  </div>

                  <div>
                    <label htmlFor="skills_to_acquire" className={labelClass}>Skills to acquire</label>
                    <input
                      id="skills_to_acquire"
                      type="text"
                      value={form.skills_to_acquire}
                      onChange={(e) => set('skills_to_acquire', e.target.value)}
                      placeholder="e.g. Leadership, AI/ML, Go"
                      disabled={status === 'saving'}
                      className={inputClass}
                    />
                  </div>

                  <div>
                    <label htmlFor="industry_domain" className={labelClass}>Industry / domain</label>
                    <input
                      id="industry_domain"
                      type="text"
                      value={form.industry_domain}
                      onChange={(e) => set('industry_domain', e.target.value)}
                      placeholder="e.g. FinTech, Healthcare, SaaS"
                      disabled={status === 'saving'}
                      className={inputClass}
                    />
                  </div>

                  <div>
                    <label htmlFor="values_impact" className={labelClass}>Values &amp; impact</label>
                    <textarea
                      id="values_impact"
                      rows={3}
                      value={form.values_impact}
                      onChange={(e) => set('values_impact', e.target.value)}
                      placeholder="What kind of impact do you want to have? (optional)"
                      disabled={status === 'saving'}
                      className={textareaClass}
                    />
                  </div>

                  {errorMsg && (
                    <p className="text-red-400 text-sm text-center">{errorMsg}</p>
                  )}

                  <HoverButton
                    onClick={() => {}}
                    disabled={status === 'saving'}
                    backgroundColor="rgba(255,255,255,0.05)"
                    glowColor="#9ca3af"
                    textColor="#e5e7eb"
                    hoverTextColor="#ffffff"
                    className="!text-base !py-3 !px-6 !rounded-xl border border-white/10 w-full"
                  >
                    {status === 'saving' ? 'Saving\u2026' : 'Save changes \u2192'}
                  </HoverButton>
                </form>
              </div>
            </motion.div>
          )}
        </div>
      </div>
    </div>
  );
}
