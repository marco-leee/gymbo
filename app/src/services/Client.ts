import { useSupabaseClient } from "@/utils/supabase";
import { SupabaseClient } from "@supabase/supabase-js";
import { Client } from "@/models";

class ClientService {
  private readonly CLIENT_TABLE = "clients";
  private client: SupabaseClient = useSupabaseClient();

  async getClients(page: number, limit: number): Promise<Client[]> {
    const offset = (page - 1) * limit;

    const { data, error } = await this.client.from(this.CLIENT_TABLE).select("*").range(offset, offset + limit - 1);

    if (error) {
      throw error;
    }

    return data.map((client) => Client.parse(client));
  }

  async getClientById(id: string): Promise<Client | null> {
    const { data, error } = await this.client.from(this.CLIENT_TABLE).select("*").eq("id", id).limit(1);

    if (error) {
      throw error;
    }

    return data.length > 0 ? Client.parse(data[0]) : null;
  }

  async getClientByEmail(email: string): Promise<Client | null> {
    const { data, error } = await this.client.from(this.CLIENT_TABLE).select("*").eq("email", email).limit(1);

    if (error) {
      throw error;
    }

    return data.length > 0 ? Client.parse(data[0]) : null;
  }

  async createClient(client: Client): Promise<Client> {
    const { data, error } = await this.client.from(this.CLIENT_TABLE).insert(client).select("*").limit(1).single();

    if (error) {
      throw error;
    }

    return Client.parse(data);
  }
}

const clientService = new ClientService();

export default clientService;