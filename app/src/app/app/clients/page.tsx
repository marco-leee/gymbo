"use client";

import { Button, Center, Container, Group, Loader, Stack, Table, Title } from "@mantine/core";
import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import Loading from "@/app/components/Loading";
import { type Client } from "@/app/models/Client";

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
  {
    accessor: "actions",
    title: "Actions",
  },
];

export default function Clients() {
  const { data, isLoading, error } = useQuery<{ data: Client[] }>({
    queryKey: ["clients"],
    queryFn: () => fetch("/api/v1/clients").then((res) => res.json()),
  });

  if (isLoading) {
    return <Loading />;
  }

  if (error) {
    return <div>Error: {error.message}</div>;
  }

  const clients = data?.data;

  return (
    <Container fluid>
      <Stack>
        <Group justify="space-between">
          <Title order={2}>Clients</Title>
          <Button component={Link} href="/app/clients/new">New</Button>
        </Group>
        <Table striped highlightOnHover withTableBorder withRowBorders={false}>
          <Table.Thead>
            <Table.Tr>
              {columns.map((column) => (
                <Table.Th key={column.accessor}>{column.title}</Table.Th>
              ))}
            </Table.Tr>
          </Table.Thead>
          <Table.Tbody>
            {clients && clients.map((client) => (
              <Table.Tr key={client.id}>
                <Table.Td>{client.id}</Table.Td>
                <Table.Td>{client.email}</Table.Td>
                <Table.Td>{client.first_name}</Table.Td>
                <Table.Td>{client.last_name}</Table.Td>
                <Table.Td>
                  <Button component={Link} href={`/app/clients/${client.id}`}>Edit</Button>
                </Table.Td>
              </Table.Tr>
            ))}
          </Table.Tbody>
        </Table>
      </Stack>
    </Container>
  );
}