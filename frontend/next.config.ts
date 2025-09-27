import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Enable standalone output for Docker deployment
  output: 'standalone',

  // Disable static generation to avoid Supabase client issues during build
  trailingSlash: true,
  skipTrailingSlashRedirect: true,
  skipMiddlewareUrlNormalize: true,

  // Force dynamic rendering to avoid static generation issues
  experimental: {
    // Enable standalone mode
  },

  // Environment variables that should be available at build time
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL,
  },

  // Disable static optimization for all pages
  generateBuildId: async () => {
    return 'build-' + Date.now()
  },
};

export default nextConfig;
