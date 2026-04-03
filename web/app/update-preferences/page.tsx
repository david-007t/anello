'use client';

import { useEffect, useState } from 'react';
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
  'w-full px-4 py-3 rounded-xl bg-white/[0.08] border border-white/20 text-white placeholder-white/30 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent disabled:opacity-50';

const labelClass = 'text-sm font-medium text-white/70 mb-1.5 block';

export default function UpdatePreferencesPage() {
  const router = useRouter();
  const { isLoaded, isSignedIn } = useUser();
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
  const [status, setStatus] = useState<'loading' | 'idle' | 'saving' | 'saved' | 'error'>('loading');
  const [showBack, setShowBack] = useState(false);

  useEffect(() => {
    if (!isLoaded) return;
    if (!isSignedIn) {
      router.push('/');
      return;
    }
    fetch('/api/preferences')
      .then((r) => r.json())
      .then(({ data }) => {
        if (data) setForm(data);
        setStatus('idle');
      })
      .catch(() => setStatus('idle'));
  }, [isLoaded, isSignedIn, router]);

  function set(key: keyof FormState, value: string) {
    setForm((f) => ({ ...f, [key]: value }));
  }

  async function handleSave(e: React.FormEvent) {
    e.preventDefault();
    setStatus('saving');
    try {
      const res = await fetch('/api/preferences', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form),
      });
      if (res.ok) {
        setStatus('saved');
        setTimeout(() => setShowBack(true), 2000);
      } else {
        setStatus('error');
      }
    } catch {
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
        {/* Nav — logo only */}
        <nav className="sticky top-0 z-50 border-b border-white/10 bg-black/80 backdrop-blur-md">
          <div className="max-w-6xl mx-auto px-6 h-16 flex items-center">
            <a href="/" className="text-xl font-black tracking-tight text-white hover:opacity-80 transition-opacity">
              anelo
            </a>
          </div>
        </nav>

        {/* Content */}
        <div className="max-w-lg mx-auto px-6 py-16">
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, ease: 'easeOut' }}
          >
            <div className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-2xl p-8">
              <div className="mb-8">
                <h1 className="text-3xl font-bold text-white mb-2">Your preferences.</h1>
                <p className="text-slate-400 text-sm">Tell Anelo exactly what to look for.</p>
              </div>

              <form onSubmit={handleSave} className="space-y-5">
                {/* Target Roles */}
                <div>
                  <label className={labelClass}>Target roles (up to 3)</label>
                  <div className="space-y-2">
                    {(['role', 'role_2', 'role_3'] as const).map((key, i) => (
                      <input
                        key={key}
                        type="text"
                        value={form[key]}
                        onChange={(e) => set(key, e.target.value)}
                        placeholder={
                          loading
                            ? 'Loading…'
                            : i === 0
                            ? 'Primary role, e.g. Product Manager'
                            : `Role ${i + 1}, e.g. ${i === 1 ? 'Technical Program Manager' : 'Senior Data Engineer'}`
                        }
                        disabled={loading}
                        className={inputClass}
                      />
                    ))}
                  </div>
                </div>

                {/* Location */}
                <div>
                  <label className={labelClass}>Location</label>
                  <input
                    type="text"
                    value={form.location}
                    onChange={(e) => set('location', e.target.value)}
                    placeholder={loading ? 'Loading…' : 'e.g. San Francisco, Remote'}
                    disabled={loading}
                    className={inputClass}
                  />
                </div>

                {/* Experience */}
                <div>
                  <label className={labelClass}>Years of experience</label>
                  <div className="flex items-center gap-3">
                    <input
                      type="number"
                      min={0}
                      value={form.experience_min}
                      onChange={(e) => set('experience_min', e.target.value)}
                      placeholder="Min"
                      disabled={loading}
                      className={`${inputClass} w-28`}
                    />
                    <span className="text-sm text-slate-400">to</span>
                    <input
                      type="number"
                      min={0}
                      value={form.experience_max}
                      onChange={(e) => set('experience_max', e.target.value)}
                      placeholder="Max"
                      disabled={loading}
                      className={`${inputClass} w-28`}
                    />
                    <span className="text-sm text-slate-400">years</span>
                  </div>
                </div>

                {/* Salary */}
                <div>
                  <label className={labelClass}>Minimum salary (USD)</label>
                  <input
                    type="text"
                    value={form.min_salary}
                    onChange={(e) => set('min_salary', e.target.value)}
                    placeholder={loading ? 'Loading…' : 'e.g. 120000'}
                    disabled={loading}
                    className={inputClass}
                  />
                </div>

                {/* Company types */}
                <div>
                  <label className={labelClass}>Company types</label>
                  <input
                    type="text"
                    value={form.company_types}
                    onChange={(e) => set('company_types', e.target.value)}
                    placeholder={loading ? 'Loading…' : 'e.g. Startup, Series B, FAANG'}
                    disabled={loading}
                    className={inputClass}
                  />
                </div>

                {/* Skills */}
                <div>
                  <label className={labelClass}>Skills to highlight</label>
                  <input
                    type="text"
                    value={form.skills}
                    onChange={(e) => set('skills', e.target.value)}
                    placeholder={loading ? 'Loading…' : 'e.g. React, Python, SQL'}
                    disabled={loading}
                    className={inputClass}
                  />
                </div>

                <HoverButton
                  type="submit"
                  disabled={loading || status === 'saving'}
                  backgroundColor="rgba(255,255,255,0.05)"
                  glowColor="#9ca3af"
                  textColor="#e5e7eb"
                  hoverTextColor="#ffffff"
                  className="!text-base !py-3 !px-6 !rounded-xl border border-white/10 w-full"
                >
                  {status === 'saving' ? 'Saving…' : status === 'saved' ? 'Saved ✓' : 'Save preferences'}
                </HoverButton>

                {status === 'error' && (
                  <p className="text-sm text-red-400 text-center">Something went wrong. Try again.</p>
                )}

                {showBack && (
                  <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ duration: 0.4 }}
                    className="text-center"
                  >
                    <a href="/" className="text-sm text-white/40 hover:text-white/60 transition-colors">
                      ← Back to anelo.io
                    </a>
                  </motion.div>
                )}
              </form>
            </div>
          </motion.div>
        </div>
      </div>
    </div>
  );
}
