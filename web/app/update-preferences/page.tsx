'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useUser } from '@clerk/nextjs';
import { motion } from 'framer-motion';
import { FallingPattern } from '@/components/ui/falling-pattern';
import { HoverButton } from '@/components/ui/hover-button';

interface PrefsData {
  current_role_title?: string;
  ideal_job_title_1?: string;
  role?: string;
}

const steps = [
  {
    number: '01',
    name: 'The Anelo Vision',
    description: 'Welcome',
    hasData: false,
  },
  {
    number: '02',
    name: 'Current Self',
    description: 'Who you are today',
    hasData: true,
    dataKey: 'current_role_title' as keyof PrefsData,
    fallback: 'Not set yet',
  },
  {
    number: '03',
    name: 'Future Self',
    description: 'Who you want to become',
    hasData: true,
    dataKey: 'role' as keyof PrefsData,
    fallback: 'Not set yet',
  },
  {
    number: '04',
    name: 'Digest Preview',
    description: 'Your personalized preview',
    hasData: false,
  },
  {
    number: '05',
    name: 'Confirmation',
    description: 'All set',
    hasData: false,
  },
];

export default function UpdatePreferencesPage() {
  const router = useRouter();
  const { isLoaded, isSignedIn } = useUser();
  const [prefs, setPrefs] = useState<PrefsData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!isLoaded) return;
    if (!isSignedIn) {
      router.push('/sign-in');
      return;
    }
    fetch('/api/preferences')
      .then((r) => r.json())
      .then(({ data }) => {
        setPrefs(data ?? {});
        setLoading(false);
      })
      .catch(() => {
        setPrefs({});
        setLoading(false);
      });
  }, [isLoaded, isSignedIn, router]);

  if (!isLoaded) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center">
        <div className="w-6 h-6 border-2 border-white/20 border-t-white rounded-full animate-spin" />
      </div>
    );
  }

  if (!isSignedIn) return null;

  function getSummary(step: typeof steps[number]): string | null {
    if (!step.hasData || !prefs) return null;
    const val = prefs[step.dataKey as keyof PrefsData];
    return (typeof val === 'string' && val.trim()) ? val.trim() : step.fallback ?? 'Not set yet';
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
          ) : (
            <motion.div
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4, ease: 'easeOut' }}
            >
              <div className="mb-8">
                <h1 className="text-3xl font-bold text-white mb-2">Update your Anelo.</h1>
                <p className="text-slate-400 text-sm">Choose a step to edit.</p>
              </div>

              <div className="space-y-3">
                {steps.map((step, i) => {
                  const summary = getSummary(step);
                  return (
                    <HoverButton
                      key={step.number}
                      onClick={() => router.push(`/onboarding?mode=edit&step=${i + 1}`)}
                      backgroundColor="rgba(255,255,255,0.03)"
                      glowColor="#9ca3af"
                      textColor="#e5e7eb"
                      hoverTextColor="#ffffff"
                      className="!rounded-xl border border-white/10 w-full !py-0 !px-0"
                    >
                      <div className="flex items-center gap-4 px-5 py-4 w-full text-left">
                        <span className="text-xs font-mono text-white/30 shrink-0 w-7">{step.number}</span>
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-semibold text-white">{step.name}</p>
                          {summary !== null && (
                            <p className="text-xs text-white/40 truncate mt-0.5">{summary}</p>
                          )}
                        </div>
                        <span className="text-white/30 text-base shrink-0">&rarr;</span>
                      </div>
                    </HoverButton>
                  );
                })}
              </div>

              <div className="mt-8 text-center">
                <a
                  href="/onboarding?mode=edit&step=1"
                  className="text-sm text-white/40 hover:text-white/60 transition-colors"
                >
                  Start from the beginning
                </a>
              </div>
            </motion.div>
          )}
        </div>
      </div>
    </div>
  );
}
