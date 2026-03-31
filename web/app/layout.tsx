import type { Metadata } from "next";
import { Geist } from "next/font/google";
import "./globals.css";

const geist = Geist({
  variable: "--font-geist",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Anello — Your jobs come to you.",
  description:
    "Anello is an AI job agent that finds, tailors your resume, and applies to jobs automatically. Set your preferences and let Anello handle the grind.",
  metadataBase: new URL("https://anello.io"),
  openGraph: {
    title: "Anello — Your jobs come to you.",
    description:
      "AI-powered job agent that finds, tailors, and applies to jobs for you.",
    url: "https://anello.io",
    siteName: "Anello",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "Anello — Your jobs come to you.",
    description: "AI-powered job agent that applies to jobs on your behalf.",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={`${geist.variable} scroll-smooth`}>
      <body className="min-h-full antialiased">{children}</body>
    </html>
  );
}
