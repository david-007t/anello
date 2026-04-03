'use client';

import { SignIn } from "@clerk/nextjs";
import { FallingPattern } from '@/components/ui/falling-pattern';

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
          <a href="/" className="text-xl font-black tracking-tight text-white hover:opacity-80 transition-opacity">
            anelo
          </a>
        </div>
        <SignIn
          appearance={{
            variables: {
              colorBackground: '#0d0d0d',
              colorInputBackground: 'rgba(255,255,255,0.08)',
              colorInputText: '#ffffff',
              colorText: '#ffffff',
              colorTextSecondary: '#94a3b8',
              colorPrimary: '#6366f1',
              colorDanger: '#ef4444',
              borderRadius: '12px',
              colorNeutral: '#ffffff',
            },
            elements: {
              card: {
                backgroundColor: 'rgba(255,255,255,0.05)',
                backdropFilter: 'blur(12px)',
                border: '1px solid rgba(255,255,255,0.1)',
                boxShadow: 'none',
              },
            },
          }}
        />
      </div>
    </div>
  );
}
