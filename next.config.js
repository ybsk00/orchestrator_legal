/** @type {import('next').NextConfig} */
const nextConfig = {
  // Python API는 Vercel Functions로 처리
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: '/api/:path*',
      },
    ];
  },
};

module.exports = nextConfig;
