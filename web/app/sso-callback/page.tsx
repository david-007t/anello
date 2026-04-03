import { AuthenticateWithRedirectCallback } from '@clerk/nextjs';

export default function SSOCallbackPage() {
  return (
    <div className="min-h-screen bg-black flex items-center justify-center">
      <AuthenticateWithRedirectCallback />
    </div>
  );
}
