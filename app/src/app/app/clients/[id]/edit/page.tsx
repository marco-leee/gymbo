"use client";

import Loading from "@/app/components/Loading";
import { useQuery } from "@tanstack/react-query";
import { useParams } from "next/navigation";

export default function EditClientPage() {
  const { id } = useParams();

  const { data: client, isLoading } = useQuery({
    queryKey: ["client", id],
    queryFn: () => fetch(`/api/v1/clients/${id}`).then((res) => res.json()),
  });

  if (isLoading) {
    return <Loading />;
  }

  return <div>EditClientPage {client.data.first_name}</div>;
}