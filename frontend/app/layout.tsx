import type { Metadata } from "next";
import "./globals.css";
import React from "react";
import { Toaster } from "sonner";
import { Geist, Geist_Mono } from "next/font/google";
import CursorIntelligence from "@/components/design-system/CursorIntelligence";
import ErrorBoundary from "@/components/ErrorBoundary"; // REFACTOR: [global-error-boundary]

const geistSans = Geist({
  variable: "--font-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-mono",
  subsets: ["latin"],
});

const APP_URL = process.env.NEXT_PUBLIC_APP_URL || "https://excellentinsight.app";

export const metadata: Metadata = {
  metadataBase: new URL(APP_URL),
  title: {
    default: "ExcellentInsight | AI-Powered Spreadsheet Intelligence",
    template: "%s | ExcellentInsight",
  },
  description:
    "Upload any Excel or CSV file and get a complete AI-powered intelligence dashboard in under 1 minute. Zero configuration, instant insights.",
  keywords: [
    "excel analysis",
    "AI dashboard",
    "data visualization",
    "business intelligence",
    "spreadsheet analytics",
    "KPI automation",
  ],
  authors: [{ name: "ExcellentInsight" }],
  creator: "ExcellentInsight",
  openGraph: {
    type: "website",
    locale: "en_US",
    url: APP_URL,
    title: "ExcellentInsight | AI-Powered Spreadsheet Intelligence",
    description:
      "Turn any Excel or CSV file into an AI-powered intelligence dashboard in seconds.",
    siteName: "ExcellentInsight",
  },
  twitter: {
    card: "summary_large_image",
    title: "ExcellentInsight | AI-Powered Spreadsheet Intelligence",
    description:
      "Turn any Excel or CSV file into an AI-powered intelligence dashboard in seconds.",
    creator: "@excellentinsight",
  },
  robots: {
    index: true,
    follow: true,
  },
  icons: {
    icon: "/favicon.ico",
    shortcut: "/favicon-16x16.png",
    apple: "/apple-touch-icon.png",
  },
};

import QueryProvider from "@/lib/query-provider";

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning className="dark">
      <head />
      {/* REFACTOR: [consolidate-hex] — body uses CSS var tokens */}
      <body className={`${geistSans.variable} ${geistMono.variable} antialiased bg-[var(--bg)] text-[var(--text)] selection:bg-[var(--accent-blue)] selection:text-white`}>
        <CursorIntelligence />
        <ErrorBoundary>
          <QueryProvider>
            {children}
          </QueryProvider>
        </ErrorBoundary>
        <Toaster
          position="top-right"
          toastOptions={{
            style: {
              background: "var(--bg-surface)",
              border: "1px solid var(--border)",
              color: "var(--text)",
              fontFamily: "var(--font-sans)",
              fontWeight: "500",
              borderRadius: "var(--radius)",
              boxShadow: "0 10px 30px rgba(0, 0, 0, 0.5)",
            },
          }}
        />
      </body>
    </html>
  );
}
