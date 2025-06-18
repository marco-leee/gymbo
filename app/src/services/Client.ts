import { CreateClientResponse, DeleteClientResponse, GetClientResponse, UpdateClientResponse } from "@/gen/web/shared/messages/v1/client_pb";
import { adminGatewayClient } from "./shared";
import { Client } from "@/gen/web/shared/entities/v1/client_pb";


export class AdminGatewayClientService {
  private static client = adminGatewayClient;

  public static async createClient(client: Client): Promise<CreateClientResponse> {
    const response = await AdminGatewayClientService.client.createClient({
      $typeName: 'shared.messages.v1.CreateClientRequest',
      client,
    });

    return response;
  }

  public static async getClient(id: string): Promise<GetClientResponse> {
    const response = await AdminGatewayClientService.client.getClient({
      $typeName: 'shared.messages.v1.GetClientRequest',
      id,
    });

    return response;
  }

  public static async updateClient(client: Client): Promise<UpdateClientResponse> {
    const response = await AdminGatewayClientService.client.updateClient({
      $typeName: 'shared.messages.v1.UpdateClientRequest',
      client,
    });

    return response;
  }

  public static async deleteClient(id: string): Promise<DeleteClientResponse> {
    const response = await AdminGatewayClientService.client.deleteClient({
      $typeName: 'shared.messages.v1.DeleteClientRequest',
      id,
    });

    return response;
  }
}