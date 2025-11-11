/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  output: 'standalone',
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost/api',
    NEXT_PUBLIC_TOOL_HOST: process.env.NEXT_PUBLIC_TOOL_HOST || 'http://localhost'
  }
};

module.exports = nextConfig;
