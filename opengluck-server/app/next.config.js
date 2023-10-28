/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",
  reactStrictMode: true,
  distDir: "node_modules/.next",
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `/api/:path*`,
      },
    ];
  },
};

module.exports = nextConfig;
