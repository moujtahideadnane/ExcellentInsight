import type { Metadata } from "next";
import "./globals.css";
import React from "react";
import { Toaster } from "sonner";
import { Geist, Geist_Mono } from "next/font/google";
import CursorIntelligence from "@/components/design-system/CursorIntelligence";

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
      {/* Vercel Edge baseline: Pure black bg, off-white text, specific selection color */}
      <body className={`${geistSans.variable} ${geistMono.variable} antialiased bg-black text-[#EDEDED] selection:bg-[#0070F3] selection:text-white`}>
        <CursorIntelligence />
        <QueryProvider>
          {children}
        </QueryProvider>
        <Toaster
          position="top-right"
          toastOptions={{
            style: {
              background: "#111111", /* Elevated surface */
              border: "1px solid #333333", /* Hairline border */
              color: "#EDEDED",
              fontFamily: "var(--font-sans)",
              fontWeight: "500",
              borderRadius: "6px", /* Sharp/subtle radius */
              boxShadow: "0 10px 30px rgba(0, 0, 0, 0.5)",
            },
          }}
        />
      </body>
    </html>
  );
}
