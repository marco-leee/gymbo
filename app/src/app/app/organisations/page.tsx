"use client";

import { useQuery, useTransport } from "@connectrpc/connect-query";
import { AdminGatewayService } from '@/gen/web/gateways/admin/v1/admin_gateway_pb';
import { createClient } from "@connectrpc/connect";
import { listOrganisations } from "@/gen/web/gateways/admin/v1/admin_gateway-AdminGatewayService_connectquery";
import { Organisation } from "@/gen/web/shared/entities/v1/organisation_pb";
import Loading from "@/components/Loading";
import { Button, Container, Group, Stack, Table, Title } from "@mantine/core";
import Link from "next/link";
import { DataTable } from "@/components/DataTable";


export default function Organisations() {
  const { data, isLoading, error } = useQuery(listOrganisations, {
    index: 0,
    limit: 10,
    offset: 0,
    filters: {},
    sort: {},
  });

  if (isLoading) {
    return <Loading />;
  };

  if (error) {
    return <div>Error: {error.message}</div>;
  };

  return (
    <Container fluid>
      <Stack>
        <Group justify="space-between">
          <Title order={2}>Organisations</Title>
          <Button component={Link} href="/app/organisations/new">New</Button>
        </Group>
        <DataTable 
          headers={["Name", "Email", "Address", "Phone", "Logo"]} 
          data={data?.organisations || []}
          getValue={(org, header) => {
            switch (header) {
              case "Name": return org.name;
              case "Email": return org.email;
              case "Address": return org.address;
              case "Phone": return org.phone;
              case "Logo": return org.logo;
              default: return null;
            }
          }}
        />
      </Stack>
    </Container>
  );
}