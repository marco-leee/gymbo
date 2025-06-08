'use client';

import { Table, Container, Stack, Group, Title, Button } from '@mantine/core';
import Link from 'next/link';

const columns = [
  {
    accessor: "id",
    title: "ID",
  },
  {
    accessor: "name",
    title: "Name",
  },
  {
    accessor: "type",
    title: "Type",
  },
  {
    accessor: "client_id",
    title: "Client",
  },
  {
    accessor: "trainer_id",
    title: "Trainer",
  },
  {
    accessor: "status",
    title: "Status",
  },
  {
    accessor: "actions",
    title: "Actions",
  },
];

export default function Exercises() {
  return (
    <Container fluid>
      <Stack>
        <Group justify="space-between">
          <Title order={2}>Exercises</Title>
          <Button component={Link} href="/app/exercises/new">New</Button>
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
          </Table.Tbody>
        </Table>
      </Stack>
    </Container>
  );
}