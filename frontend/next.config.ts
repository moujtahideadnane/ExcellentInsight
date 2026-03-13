import type { NextConfig } from "next";
import bundleAnalyzer from '@next/bundle-analyzer';

const withBundleAnalyzer = bundleAnalyzer({
  enabled: process.env.ANALYZE === 'true',
});

const nextConfig: NextConfig = {
  output: 'standalone',
  experimental: {
    optimizePackageImports: [
      'lucide-react', 
      '@visx/group', 
      '@visx/shape', 
      '@visx/scale',
      '@visx/tooltip',
      '@visx/axis',
      '@visx/grid',
      '@visx/event',
      '@visx/gradient',
      'framer-motion',
      'sonner',
      'zustand',
      'axios'
    ],
  },
};

export default withBundleAnalyzer(nextConfig);
