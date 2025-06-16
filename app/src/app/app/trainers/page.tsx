"use client";

import { Button, Center, Container, Group, Loader, Stack, Table, Title } from "@mantine/core";
import { useQuery, useTransport } from "@connectrpc/connect-query";
import Link from "next/link";
import Loading from "@/components/Loading";
import { Trainer } from "@/gen/web/shared/entities/v1/trainer_pb";
import { DataTable } from "@/components/DataTable";
import { listTrainers } from "@/gen/web/gateways/admin/v1/admin_gateway-AdminGatewayService_connectquery";

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
  const { data, isLoading, error } = useQuery(listTrainers, {
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

  // const trainers = data?.trainers || [];

  return (
    <Container fluid>
      <Stack>
        <Group justify="space-between">
          <Title order={2}>Trainers</Title>
          <Button component={Link} href="/app/trainers/new">New</Button>
        </Group>
        {/* <DataTable data={trainers} columns={columns} /> */}
      </Stack>
    </Container>
  );
}