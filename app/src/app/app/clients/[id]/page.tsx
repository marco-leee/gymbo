"use client";

import { getClient } from "@/gen/web/gateways/admin/v1/admin_gateway-AdminGatewayService_connectquery";
import { useQuery } from "@connectrpc/connect-query";
import { useParams } from "next/navigation";

export default function ClientPage() {
  const { id } = useParams();

  const { data, isLoading, error } = useQuery(getClient, {
    id: id as string,
  });

  if (isLoading) return <div>Loading...</div>;

  if (error) return <div>Error: {error.message}</div>;

  return <div>ClientPage {data?.client?.email}</div>;
}