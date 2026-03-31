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
    "Anelo is an AI job agent that finds, tailors your resume, and applies to jobs automatically. Set your preferences and let Anelo handle the grind.",
  metadataBase: new URL("https://anelo.io"),
  openGraph: {
    title: "Anelo — Your jobs come to you.",
    description:
      "AI-powered job agent that finds, tailors, and applies to jobs for you.",
    url: "https://anelo.io",
    siteName: "Anelo",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "Anelo — Your jobs come to you.",
    description: "AI-powered job agent that applies to jobs on your behalf.",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <ClerkProvider afterSignOutUrl="/">
      <html lang="en" className={`${geist.variable} scroll-smooth`}>
        <body className="min-h-full antialiased">{children}</body>
      </html>
    </ClerkProvider>
  );
}
