"use client";

import { getOrganisation } from "@/gen/web/gateways/admin/v1/admin_gateway-AdminGatewayService_connectquery";
import { useQuery } from "@connectrpc/connect-query";
import { useParams } from "next/navigation";
import Loading from "@/components/Loading";
import { Container, Stack, Text, Title } from "@mantine/core";

export default function Organisation() {
  const { id } = useParams();
  const { data, isLoading, error } = useQuery(getOrganisation, {
    id: id as string,
  });

  if (isLoading) {
    return <Loading />;
  };

  if (error) {
    return <div>Error: {error.message}</div>;
  };

  console.log(data?.organisation);

  return (
    <Container fluid>
      <Stack>
        <Title order={2}>Organisation</Title>
        <Text>{data?.organisation?.name}</Text>
        <Text>{data?.organisation?.email}</Text>
        <Text>{data?.organisation?.address}</Text>
        <Text>{data?.organisation?.phone}</Text>
        <Text>{data?.organisation?.logo}</Text>
        <Text>{data?.organisation?.website}</Text>
      </Stack>
    </Container>
  );
}