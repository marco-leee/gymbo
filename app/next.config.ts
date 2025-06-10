import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
  async rewrites() {
    return [
      {
        source: '/gateways.admin.v1.AdminGatewayService/:path',
        destination: 'http://localhost:8080/gateways.admin.v1.AdminGatewayService/:path',
      }
    ]
  }
};

export default nextConfig;
