import { createConnectTransport } from "@connectrpc/connect-web";
import { createClient } from "@connectrpc/connect";
import { AdminGatewayService } from "@/gen/web/gateways/admin/v1/admin_gateway_pb";
import { OrganisationGatewayService } from "@/gen/web/gateways/organisation/v1/organisation_gateway_pb";
import { TrainerGatewayService } from "@/gen/web/gateways/trainer/v1/trainer_gateway_pb";
import { ClientGatewayService } from "@/gen/web/gateways/client/v1/client_gateway_pb";

export const transport = createConnectTransport({
  baseUrl: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3000',
});

export const adminGatewayClient = createClient(AdminGatewayService, transport);

export const organisationGatewayClient = createClient(OrganisationGatewayService, transport);

export const trainingGatewayClient = createClient(TrainerGatewayService, transport);

export const clientGatewayClient = createClient(ClientGatewayService, transport);