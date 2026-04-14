import type { NextConfig } from "next";

const securityHeaders = [
  { key: "X-Frame-Options", value: "DENY" },
  { key: "X-Content-Type-Options", value: "nosniff" },
  { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
  { key: "Permissions-Policy", value: "camera=(), microphone=(), geolocation=()" },
  {
    key: "Content-Security-Policy",
    value: [
      "default-src 'self'",
      "base-uri 'self'",
      "connect-src 'self' https://clerk.anelo.io https://vercel.live https://accounts.google.com https://www.google.com",
      "form-action 'self'",
      "frame-ancestors 'none'",
      "frame-src 'self' https://clerk.anelo.io https://accounts.google.com",
      "img-src 'self' data: blob: https:",
      "object-src 'none'",
      "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://clerk.anelo.io https://vercel.live https://accounts.google.com https://www.google.com https://apis.google.com",
      "style-src 'self' 'unsafe-inline'",
      "font-src 'self' data: https:",
      "upgrade-insecure-requests",
      "worker-src 'self' blob:",
    ].join("; "),
  },
];

const nextConfig: NextConfig = {
  async headers() {
    return [
      {
        source: "/:path*",
        headers: securityHeaders,
      },
    ];
  },
};

export default nextConfig;
