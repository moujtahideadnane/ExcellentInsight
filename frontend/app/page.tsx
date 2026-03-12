import { Metadata } from 'next'
import LandingClient from './landing-client'

export const metadata: Metadata = {
  title: 'ExcellentInsight - AI-Powered Excel & CSV Analysis Tool | Automatic Dashboard Generator',
  description: 'Transform Excel (.xlsx, .xls) and CSV files into interactive AI-powered dashboards with automatic KPI detection in under 60 seconds. Free open-source business intelligence platform using OpenRouter AI for data analysis, trend forecasting, and insights.',
  keywords: [
    'excel analysis',
    'csv analysis',
    'ai dashboard',
    'kpi detection',
    'business intelligence',
    'data visualization',
    'spreadsheet analysis',
    'automatic insights',
    'excel to dashboard',
    'ai data analysis',
    'openrouter ai',
    'free bi tool',
    'pandas analysis',
    'fastapi',
    'nextjs dashboard',
    'real-time analytics',
    'zero configuration',
    'trend forecasting',
    'anomaly detection',
    'open source bi'
  ],
  authors: [{ name: 'ExcellentInsight Team' }],
  creator: 'ExcellentInsight',
  publisher: 'ExcellentInsight',
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      'max-video-preview': -1,
      'max-image-preview': 'large',
      'max-snippet': -1,
    },
  },
  openGraph: {
    type: 'website',
    locale: 'en_US',
    url: 'https://excellentinsight.onthewifi.com',
    siteName: 'ExcellentInsight',
    title: 'ExcellentInsight - AI-Powered Excel & CSV Analysis Tool',
    description: 'Transform any Excel or CSV file into comprehensive AI-powered dashboards with automatic KPI detection. Zero configuration, instant business intelligence insights.',
    images: [
      {
        url: '/og-image.png',
        width: 1200,
        height: 630,
        alt: 'ExcellentInsight AI Dashboard - Transform Excel and CSV files into interactive dashboards',
      },
    ],
  },
  twitter: {
    card: 'summary_large_image',
    title: 'ExcellentInsight - AI-Powered Excel & CSV Analysis',
    description: 'Transform Excel & CSV files into AI-powered dashboards with automatic KPI detection in under 60 seconds.',
    images: ['/og-image.png'],
  },
  alternates: {
    canonical: 'https://excellentinsight.onthewifi.com',
  },
  verification: {
    // Add Google Search Console verification meta tag here once you get it
    // google: 'your-google-verification-code',
  },
  category: 'technology',
}

export default function LandingPage() {
  return <LandingClient />
}
