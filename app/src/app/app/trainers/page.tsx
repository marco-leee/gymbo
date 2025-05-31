"use client";

import { Button, Center, Container, Group, Loader, Stack, Table, Title } from "@mantine/core";
import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import Loading from "@/components/Loading";
import { type Trainer } from "@/models";

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

export default function Trainers() {
  const { data, isLoading, error } = useQuery<{ data: Trainer[] }>({
    queryKey: ["trainers"],
    queryFn: () => fetch("/api/v1/trainers").then((res) => res.json()),
  });

  if (isLoading) {
    return <Loading />;
  }

  if (error) {
    return <div>Error: {error.message}</div>;
  }

  const trainers = data?.data;

  return (
    <Container fluid>
      <Stack>
        <Group justify="space-between">
          <Title order={2}>Trainers</Title>
          <Button component={Link} href="/app/trainers/new">New</Button>
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
            {trainers && trainers.map((trainer) => (
              <Table.Tr key={trainer.id}>
                <Table.Td>{trainer.id}</Table.Td>
                <Table.Td>{trainer.email}</Table.Td>
                <Table.Td>{trainer.first_name}</Table.Td>
                <Table.Td>{trainer.last_name}</Table.Td>
                {/* <Table.Td>
                  <Button component={Link} href={`/app/clients/${client.id}`}>Edit</Button>
                </Table.Td> */}
              </Table.Tr>
            ))}
          </Table.Tbody>
        </Table>
      </Stack>
    </Container>
  );
}