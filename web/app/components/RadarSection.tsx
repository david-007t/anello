'use client';

import { useRef } from 'react';
import { motion, useInView } from 'framer-motion';
import { Radar, IconContainer } from '@/components/ui/radar';
export function RadarSection() {
  const ref = useRef<HTMLElement>(null);
  const isInView = useInView(ref, { once: false, amount: 0.4 });

  return (
    <section ref={ref} className="min-h-screen flex flex-col items-center justify-center px-6 py-20">
      <motion.p
        initial={{ opacity: 0 }}
        animate={isInView ? { opacity: 1 } : { opacity: 0 }}
        transition={{ duration: 0.4, delay: 0.1 }}
        className="text-slate-500 text-xs mb-12 text-center uppercase tracking-widest"
      >
        Scanning the web
      </motion.p>

      <div className="relative flex items-center justify-center z-10 mb-14">
        {/* Radar — appears first */}
        <motion.div
          initial={{ opacity: 0, scale: 0.85 }}
          animate={isInView ? { opacity: 1, scale: 1 } : { opacity: 0, scale: 0.85 }}
          transition={{ duration: 0.6, delay: 0.2, ease: 'easeOut' }}
        >
          <Radar className="h-72 w-72 md:h-96 md:w-96" />
        </motion.div>

        {/* Top */}
        <div className="absolute -top-8 left-1/2 -translate-x-1/2">
          <IconContainer visible={isInView} delay={0.9} text="LinkedIn"
            icon={<svg className="h-6 w-6 text-sky-400" fill="currentColor" viewBox="0 0 24 24"><path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433a2.062 2.062 0 01-2.063-2.065 2.064 2.064 0 112.063 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z" /></svg>}
          />
        </div>

        {/* Top-right */}
        <div className="absolute top-4 right-0 translate-x-1/2 md:translate-x-full">
          <IconContainer visible={isInView} delay={1.05} text="Indeed"
            icon={<svg className="h-6 w-6 text-blue-400" fill="currentColor" viewBox="0 0 24 24"><path d="M12 0C5.373 0 0 5.373 0 12s5.373 12 12 12 12-5.373 12-12S18.627 0 12 0zm0 4a2 2 0 110 4 2 2 0 010-4zm3 15h-6v-1h1.5V11H9v-1h4.5v8H15v1z" /></svg>}
          />
        </div>

        {/* Right */}
        <div className="absolute right-0 top-1/2 -translate-y-1/2 translate-x-3/4 md:translate-x-full">
          <IconContainer visible={isInView} delay={1.2} text="Greenhouse"
            icon={<svg className="h-6 w-6 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" /></svg>}
          />
        </div>

        {/* Bottom-right */}
        <div className="absolute bottom-4 right-0 translate-x-1/2 md:translate-x-full">
          <IconContainer visible={isInView} delay={1.35} text="Lever"
            icon={<svg className="h-6 w-6 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>}
          />
        </div>

        {/* Bottom */}
        <div className="absolute -bottom-8 left-1/2 -translate-x-1/2">
          <IconContainer visible={isInView} delay={1.5} text="Workday"
            icon={<svg className="h-6 w-6 text-orange-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" /></svg>}
          />
        </div>

        {/* Bottom-left */}
        <div className="absolute bottom-4 left-0 -translate-x-1/2 md:-translate-x-full">
          <IconContainer visible={isInView} delay={1.65} text="Ashby"
            icon={<svg className="h-6 w-6 text-pink-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>}
          />
        </div>

        {/* Left */}
        <div className="absolute left-0 top-1/2 -translate-y-1/2 -translate-x-3/4 md:-translate-x-full">
          <IconContainer visible={isInView} delay={1.8} text="Wellfound"
            icon={<svg className="h-6 w-6 text-yellow-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" /></svg>}
          />
        </div>

        {/* Top-left */}
        <div className="absolute top-4 left-0 -translate-x-1/2 md:-translate-x-full">
          <IconContainer visible={isInView} delay={1.95} text="Rippling"
            icon={<svg className="h-6 w-6 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" /></svg>}
          />
        </div>
      </div>

    </section>
  );
}
