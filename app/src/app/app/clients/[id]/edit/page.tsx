"use client";

import { useParams } from "next/navigation";

export default function EditClientPage() {
  const { id } = useParams();

  return <div>EditClientPage {id}</div>;
}