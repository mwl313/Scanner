/** @type {import('next').NextConfig} */
const backendOrigin = process.env.BACKEND_ORIGIN;

const nextConfig = {
  async rewrites() {
    if (!backendOrigin) {
      return [];
    }
    return [
      {
        source: '/api/:path*',
        destination: `${backendOrigin}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;
