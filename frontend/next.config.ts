import type { NextConfig } from "next";

// eslint-disable-next-line @typescript-eslint/no-require-imports
const withBundleAnalyzer = require('@next/bundle-analyzer')({
  enabled: process.env.ANALYZE === 'true',
})

const nextConfig: NextConfig = {
  output: 'standalone',
  experimental: {
    optimizePackageImports: ['lucide-react', '@visx/group', '@visx/shape', '@visx/scale'],
  },
  /* eslint: {
    ignoreDuringBuilds: true,
  }, */
};

export default withBundleAnalyzer(nextConfig);
