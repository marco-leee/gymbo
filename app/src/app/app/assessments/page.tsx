'use client';

import { Table, Container, Stack, Group, Title, Button } from '@mantine/core';
import Link from 'next/link';

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

export default function Assessments() {
  return (
    <Container fluid>
      <Stack>
        <Group justify="space-between">
          <Title order={2}>Assessments</Title>
          <Button component={Link} href="/app/assessments/new">New</Button>
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