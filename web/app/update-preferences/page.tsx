'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useUser } from '@clerk/nextjs';
import { motion } from 'framer-motion';
import { FallingPattern } from '@/components/ui/falling-pattern';
import { HoverButton } from '@/components/ui/hover-button';

const steps = [
  {
    number: '01',
    name: 'Digest Preview',
    description: 'Your personalized preview',
    targetStep: 4,
  },
  {
    number: '02',
    name: 'Confirmation',
    description: 'All set',
    targetStep: 5,
  },
];

export default function UpdatePreferencesPage() {
  const router = useRouter();
  const { isLoaded, isSignedIn } = useUser();

  useEffect(() => {
    if (!isLoaded) return;
    if (!isSignedIn) router.push('/sign-in');
  }, [isLoaded, isSignedIn, router]);

  if (!isLoaded) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center">
        <div className="w-6 h-6 border-2 border-white/20 border-t-white rounded-full animate-spin" />
      </div>
    );
  }

  if (!isSignedIn) return null;

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
              {steps.map((step) => (
                <HoverButton
                  key={step.number}
                  onClick={() => router.push(`/onboarding?mode=edit&step=${step.targetStep}`)}
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
                    </div>
                    <span className="text-white/30 text-base shrink-0">&rarr;</span>
                  </div>
                </HoverButton>
              ))}
            </div>

            <div className="mt-8 text-center">
              <a
                href="/onboarding?step=2"
                className="text-sm text-white/40 hover:text-white/60 transition-colors"
              >
                Start from the beginning
              </a>
            </div>
          </motion.div>
        </div>
      </div>
    </div>
  );
}
