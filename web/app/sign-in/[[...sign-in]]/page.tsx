'use client';

import Link from 'next/link';
import { SignIn } from "@clerk/nextjs";
import { FallingPattern } from '@/components/ui/falling-pattern';
import { clerkAuthAppearance } from '@/lib/clerk-auth-appearance';

export default function SignInPage() {
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
      <div className="relative z-10 min-h-screen flex flex-col items-center justify-center px-4">
        <div className="text-center mb-8">
          <Link href="/" className="text-xl font-black tracking-tight text-white hover:opacity-80 transition-opacity">
            anelo
          </Link>
        </div>
        <SignIn
          appearance={clerkAuthAppearance}
        />
      </div>
    </div>
  );
}
