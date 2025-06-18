import { InfiniteScrollSelect } from "./InfiniteScrollSelect";
import { listClients } from "@/gen/web/gateways/admin/v1/admin_gateway-AdminGatewayService_connectquery";
import { Client } from "@/gen/web/shared/entities/v1/client_pb";
import { adminGatewayClient } from "@/services/shared";
import { UseFormReturnType } from '@mantine/form';
import { useEffect, useState } from "react";

type ClientSelectProps = {
  onChange: (value: string | null) => void;
  required?: boolean;
}

export function ClientSelect({ onChange, required }: ClientSelectProps) {
  const [value, setValue] = useState<string | null>(null);

  const fetchClients = async (page: number, search: string) => {
    const response = await adminGatewayClient.listClients({
      $typeName: 'shared.messages.v1.ListClientsRequest',
      index: page,
      limit: 10,
      offset: (page - 1) * 10,
      filters: search ? { email: search } : {},
      sort: {},
    });

    return {
      data: response.clients.map((client: Client) => ({
        value: client.id,
        label: `${client.fullName} (${client.email})`,
      })),
      hasMore: response.clients.length === 10,
    };
  };

  useEffect(() => {
    if (value) {
      onChange(value);
    }
  }, [value]);

  return (
    <InfiniteScrollSelect
      label="Client"
      value={value}
      onChange={setValue}
      fetchData={fetchClients}
      placeholder="Search for a client..."
      required={required}
    />
  );
}