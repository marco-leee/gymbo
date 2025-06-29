import { LoginResponse, User } from "@/gen/web/shared/messages/v1/auth_pb";
import { AuthService } from "./interfaces";
import { adminGatewayClient, GatewayService } from "./shared";
import { AuthToken } from "@/types/auth";
import { CallOptions, createClient, Transport } from "@connectrpc/connect";
import { createConnectTransport } from "@connectrpc/connect-web";
import { AdminGatewayService } from "@/gen/web/gateways/admin/v1/admin_gateway_pb";
import { useQuery } from "@connectrpc/connect-query";
import { listOrganisations } from "@/gen/web/gateways/admin/v1/admin_gateway-AdminGatewayService_connectquery";
import { Gateway } from "./shared";

class AdminGateway extends Gateway implements GatewayService {
  private client = adminGatewayClient;
  public transport: Transport;

  constructor() {
    super();
    this.transport = createConnectTransport({
      baseUrl: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3000',
      useBinaryFormat: true,
      useHttpGet: false,
      interceptors: [this.authInterceptor.bind(this)]
    });
    
    this.client = createClient(AdminGatewayService, this.transport);
  }

  public async login(email: string): Promise<LoginResponse> {
    const response = await this.client.login({
      $typeName: "shared.messages.v1.LoginRequest",
      email
    })

    return response;
  }

  public async logout(): Promise<void> {}

  public async getCurrentUser(): Promise<User> {
    const response = await this.client.getCurrentUser({
      $typeName: "shared.messages.v1.GetCurrentUserRequest",
    })

    return response.user as User;
  }

  public async refreshToken(refreshToken: string): Promise<AuthToken> {
    const response = await this.client.refreshToken({
      $typeName: "shared.messages.v1.RefreshTokenRequest",
      refreshToken
    })

    return {
      user_type: 'admin',
      access_token: response.accessToken,
      refresh_token: response.refreshToken,
      expires_in: Number(response.expiresAt),
    };
  }
}

const adminGateway = new AdminGateway();

export default adminGateway;