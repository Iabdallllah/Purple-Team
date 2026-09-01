/** @type {import('next').NextConfig} */
const nextConfig = {
  transpilePackages: ['@purple/shared'],
  eslint: { ignoreDuringBuilds: true },
  typescript: { ignoreBuildErrors: false },
  async rewrites() {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';
    return [
      {
        source: '/api/:path*',
        destination: `${apiUrl}/api/:path*`,
      },
    ];
  },
  // For Vercel deployment, ensure shared package is transpiled
  experimental: {
    externalDir: true,
  },
};

module.exports = nextConfig;