"use client";

import { Button, Center, Container, Group, Loader, Stack, Table, Title } from "@mantine/core";
import { useQuery } from "@connectrpc/connect-query";
import Link from "next/link";
import Loading from "@/components/Loading";
import { type Client } from "@/models/Client";
import { listClients } from "@/gen/web/gateways/admin/v1/admin_gateway-AdminGatewayService_connectquery";
import { DataTable } from "@/components/DataTable";

const columns = [
  {
    accessor: "id",
    title: "ID",
  },
  {
    accessor: "email",
    title: "Email",
  },
  {
    accessor: "first_name",
    title: "First Name",
  },
  {
    accessor: "last_name",
    title: "Last Name",
  },
  // {
  //   accessor: "actions",
  //   title: "Actions",
  // },
];

export default function Clients() {
  const { data, isLoading, error } = useQuery(listClients, {
    // index: 0,
    // limit: 10,
    // offset: 0,
    // filters: {},
    // sort: {},
  });

  if (isLoading) {
    return <Loading />;
  }

  if (error) {
    return <div>Error: {error.message}</div>;
  }

  const clients = data?.clients || [];

  return (
    <Container fluid>
      <Stack>
        <Group justify="space-between">
          <Title order={2}>Clients</Title>
          <Button component={Link} href="/app/clients/new">New</Button>
        </Group>
        <DataTable 
          headers={["ID", "Email", "First Name", "Last Name"]}
          data={clients}
          getValue={(client, header) => {
            switch (header) {
              case "ID": return client.id;
              case "Email": return client.email;
              case "First Name": return client.first_name;
              case "Last Name": return client.last_name;
              default: return null;
            }
          }}
        />
      </Stack>
    </Container>
  );
}