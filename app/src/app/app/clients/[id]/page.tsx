"use client";

import { useParams } from "next/navigation";

export default function ClientPage() {
  const { id } = useParams();

  return <div>ClientPage {id}</div>;
}