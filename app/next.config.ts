import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
  async rewrites() {
    const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL;
    return [
      {
        source: '/gateways.admin.v1.AdminGatewayService/:path',
        destination: `${backendUrl}/gateways.admin.v1.AdminGatewayService/:path`,
      },
      {
        source: '/gateways.trainer.v1.TrainerGatewayService/:path',
        destination: `${backendUrl}/gateways.trainer.v1.TrainerGatewayService/:path`,
      },
      {
        source: '/gateways.client.v1.ClientGatewayService/:path',
        destination: `${backendUrl}/gateways.client.v1.ClientGatewayService/:path`,
      },
      {
        source: '/gateways.organisation.v1.OrganisationGatewayService/:path',
        destination: `${backendUrl}/gateways.organisation.v1.OrganisationGatewayService/:path`,
      }
    ]
  }
};

export default nextConfig;
