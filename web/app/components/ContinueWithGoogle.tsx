'use client';

import { useSignUp, useAuth } from '@clerk/nextjs';
import { useRouter } from 'next/navigation';
import { useState } from 'react';

export default function ContinueWithGoogle() {
  const { isSignedIn } = useAuth();
  const { signUp } = useSignUp();
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  async function handleClick() {
    if (isSignedIn) {
      router.push('/already-signed-in');
      return;
    }
    if (!signUp) return;
    setLoading(true);
    setError('');

    const origin = window.location.origin;
    const { error: signUpError } = await signUp.sso({
      strategy: 'oauth_google',
      redirectUrl: `${origin}/sso-callback`,
      redirectCallbackUrl: `${origin}/already-signed-in`,
    });

    if (!signUpError) return; // redirect in progress

    setLoading(false);
    setError('Something went wrong. Try again.');
  }

  return (
    <div className="flex flex-col items-center gap-3">
      <button
        onClick={handleClick}
        disabled={loading}
        className="relative flex items-center gap-3 px-7 py-3.5 rounded-full border border-white/20 bg-white/5 backdrop-blur-sm text-white text-sm font-semibold hover:bg-white/10 hover:border-white/30 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer group"
      >
        {/* Google G icon */}
        {!loading && (
          <svg width="18" height="18" viewBox="0 0 18 18" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M17.64 9.2c0-.637-.057-1.251-.164-1.84H9v3.481h4.844c-.209 1.125-.843 2.078-1.796 2.717v2.258h2.908c1.702-1.567 2.684-3.874 2.684-6.615z" fill="#4285F4"/>
            <path d="M9 18c2.43 0 4.467-.806 5.956-2.184l-2.908-2.258c-.806.54-1.837.86-3.048.86-2.344 0-4.328-1.584-5.036-3.711H.957v2.332A8.997 8.997 0 0 0 9 18z" fill="#34A853"/>
            <path d="M3.964 10.707A5.41 5.41 0 0 1 3.682 9c0-.593.102-1.17.282-1.707V4.961H.957A8.996 8.996 0 0 0 0 9c0 1.452.348 2.827.957 4.039l3.007-2.332z" fill="#FBBC05"/>
            <path d="M9 3.58c1.321 0 2.508.454 3.44 1.345l2.582-2.58C13.463.891 11.426 0 9 0A8.997 8.997 0 0 0 .957 4.961L3.964 7.293C4.672 5.166 6.656 3.58 9 3.58z" fill="#EA4335"/>
          </svg>
        )}
        {loading && (
          <svg className="animate-spin" width="16" height="16" viewBox="0 0 16 16" fill="none">
            <circle cx="8" cy="8" r="6" stroke="rgba(255,255,255,0.3)" strokeWidth="2"/>
            <path d="M8 2a6 6 0 0 1 6 6" stroke="white" strokeWidth="2" strokeLinecap="round"/>
          </svg>
        )}
        <span>{loading ? 'Redirecting\u2026' : 'Continue with Google'}</span>
      </button>
      {error && <p className="text-xs text-red-400">{error}</p>}
      <p className="text-xs text-white/50">Free during early access · No credit card required</p>
    </div>
  );
}
