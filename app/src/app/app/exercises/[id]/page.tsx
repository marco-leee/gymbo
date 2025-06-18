'use client';

import { useQuery } from '@connectrpc/connect-query';
import { getExercise } from '@/gen/web/gateways/admin/v1/admin_gateway-AdminGatewayService_connectquery';
import Loading from '@/components/Loading';
import { useParams } from 'next/navigation';


export default function ExercisePage() {
  const { id } = useParams();
  const { data, isLoading, error } = useQuery(getExercise, {
    id: id as string,
  });

  if (isLoading) {
    return <Loading />;
  }

  if (error) {
    return <div>Error: {error.message}</div>;
  }

  return <div>ExercisePage {id}</div>;
}