'use client';

import { motion } from 'framer-motion';
import { useUser } from '@clerk/nextjs';
import { FallingPattern } from '@/components/ui/falling-pattern';

export default function AlreadySignedInPage() {
  const { user } = useUser();

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
            <div className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-2xl p-8 flex flex-col items-center text-center space-y-4">
              {/* Animated checkmark */}
              <motion.div
                initial={{ scale: 0.7, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                transition={{ duration: 0.4, delay: 0.15, ease: 'easeOut' }}
                className="w-14 h-14 rounded-full bg-indigo-500/20 border border-indigo-500/40 flex items-center justify-center mb-6"
              >
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                  <path d="M5 13l4 4L19 7" stroke="#6366f1" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
              </motion.div>

              <h1 className="text-3xl font-bold text-white">You&apos;re already in.</h1>

              <p className="text-slate-400 text-sm leading-relaxed text-center">
                Anelo is already working for you.<br />
                Check your email — we&apos;ll be in touch soon.
                {user?.primaryEmailAddress?.emailAddress && (
                  <>
                    <br />
                    <span className="text-white/50 text-xs mt-1 block">{user.primaryEmailAddress.emailAddress}</span>
                  </>
                )}
              </p>

              <a
                href="/update-preferences"
                className="text-sm text-white/50 hover:text-white/80 transition-colors mt-2"
              >
                Update your preferences →
              </a>

              <p className="text-xs text-white/25 mt-1">Tap anelo above to go back.</p>
            </div>
          </motion.div>
        </div>
      </div>
    </div>
  );
}
