'use client';

import { Container, Stack, Group, Title, Button } from '@mantine/core';
import Link from 'next/link';
import { DataTable } from '@/components/DataTable';
import { useQuery } from '@connectrpc/connect-query';
import { listExercises } from '@/gen/web/gateways/admin/v1/admin_gateway-AdminGatewayService_connectquery';
import Loading from '@/components/Loading';
import { ExtendedExercise } from '@/gen/web/shared/messages/v1/exercise_pb';

export default function Exercises() {
  const { data, isLoading, error } = useQuery(listExercises, {
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

  const exercises: ExtendedExercise[] = data?.exercises || [];

  return (
    <Container fluid>
      <Stack>
        <Group justify="space-between">
          <Title order={2}>Exercises</Title>
          <Button component={Link} href="/app/exercises/new">New</Button>
        </Group>
        <DataTable 
          headers={["ID", "Name", "Type", "Client", "Trainer", "Actions"]}
          data={exercises}
          getValue={(exercise, header) => {
            switch (header) {
              case "ID": return exercise.exercise?.id;
              case "Name": return exercise.exercise?.name;
              case "Type": return exercise.exercise?.type;
              case "Client": return <Link href={`/app/clients/${exercise.client?.id}`}>{exercise.client?.email}</Link>;
              case "Trainer": return <Link href={`/app/trainers/${exercise.trainer?.id}`}>{exercise.trainer?.fullName}</Link>;
              // case "Status": return exercise.media?.step;
              case "Actions": return <Button component={Link} href={`/app/exercises/${exercise.exercise?.id}`}>View</Button>;
            }
          }}
        />
      </Stack>
    </Container>
  );
}