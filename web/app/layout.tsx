import type { Metadata } from "next";
import { Geist } from "next/font/google";
import { ClerkProvider } from "@clerk/nextjs";
import "./globals.css";

const geist = Geist({
  variable: "--font-geist",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Anelo — Your jobs come to you.",
  description:
    "Anelo is an AI job agent that scans 8+ job boards daily, scores the best matches for your profile, and delivers a curated digest to your inbox every morning. Free during early access.",
  metadataBase: new URL("https://anelo.io"),
  alternates: {
    canonical: "https://anelo.io",
  },
  openGraph: {
    title: "Anelo — Your jobs come to you.",
    description:
      "AI-powered daily job digest. Anelo scans top job boards, scores matches for your profile, and sends you the best roles every morning.",
    url: "https://anelo.io",
    siteName: "Anelo",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "Anelo — Your jobs come to you.",
    description:
      "Wake up to a curated digest of your best-matched jobs — powered by AI. Free during early access.",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <ClerkProvider
      afterSignOutUrl="/"
      appearance={{
        elements: {
          formFieldRow: "hidden",
          formButtonPrimary: "hidden",
          dividerRow: "hidden",
          footerAction: "hidden",
          identifierInput: "hidden",
          formField: "hidden",
        },
      }}
    >
      <html lang="en" className={`${geist.variable} scroll-smooth`}>
        <body className="min-h-full antialiased">
          {children}
        </body>
      </html>
    </ClerkProvider>
  );
}
