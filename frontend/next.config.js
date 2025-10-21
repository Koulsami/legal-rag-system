/**
 * Next.js Configuration for Static Export to Netlify
 * This configuration enables full static site generation
 */

/** @type {import('next').NextConfig} */
const nextConfig = {
  // Enable static export - this is CRITICAL for Netlify deployment
  output: 'export',
  
  // Disable image optimization for static export
  images: {
    unoptimized: true,
  },
  
  // Add trailing slashes for better routing
  trailingSlash: true,
  
  // Strict mode for better error detection
  reactStrictMode: true,
  
  // Environment variables (only NEXT_PUBLIC_* are exposed to browser)
  env: {
    NEXT_PUBLIC_API_BASE_URL: process.env.NEXT_PUBLIC_API_BASE_URL || 'https://api.mykraws.com',
    NEXT_PUBLIC_APP_NAME: 'Myk Raws Legal AI',
    NEXT_PUBLIC_ENVIRONMENT: process.env.NODE_ENV || 'production',
  },
  
  // Compiler options
  compiler: {
    // Remove console.log in production
    removeConsole: process.env.NODE_ENV === 'production' ? {
      exclude: ['error', 'warn'],
    } : false,
  },
  
  // Webpack configuration
  webpack: (config, { isServer }) => {
    // Add any custom webpack config here
    return config;
  },
  
  // TypeScript configuration
  typescript: {
    // Strict type checking
    ignoreBuildErrors: false,
  },
  
  // ESLint configuration
  eslint: {
    // Run ESLint on build
    ignoreDuringBuilds: false,
  },
};

module.exports = nextConfig;
