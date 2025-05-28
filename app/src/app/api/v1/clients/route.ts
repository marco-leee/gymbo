import { Client } from "@/app/models/Client";
import { useSupabaseClient } from "@/app/utils/supabase-client";
import { NextRequest, NextResponse } from "next/server";
import { ulid } from 'ulid';

export async function GET(request: NextRequest) {
  const params = request.nextUrl.searchParams;
  const page = params.get("page") ?? "1";
  const limit = params.get("limit") ?? "10";
  const offset = (Number(page) - 1) * Number(limit);

  const supabase = await useSupabaseClient();

  const { data, error } = await supabase.from("clients").select("*").range(offset, offset + Number(limit) - 1);

  if (error) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }

  console.log(data)

  return NextResponse.json({ data: data.map((client) => Client.parse(client)) });
}

export async function POST(request: NextRequest) {
  const body = await request.json();

  const supabase = await useSupabaseClient();

  const { data: existingClient, error: existingClientError } = await supabase.from("clients").select("*").eq("email", body.email).limit(1);

  if (existingClientError) {
    return NextResponse.json({ error: existingClientError.message }, { status: 500 });
  }

  if (Array.isArray(existingClient) && existingClient.length > 0) {
    return NextResponse.json({ error: "Client already exists" }, { status: 400 });
  }

  const { data: newClient, error: newClientError } = await supabase.from("clients").insert({
    id: ulid(),
    email: body.email,
    first_name: body.first_name,
    last_name: body.last_name,
  }).select("*").limit(1).single();

  if (newClientError) {
    return NextResponse.json({ error: newClientError.message }, { status: 500 });
  }

  console.log(newClient);

  return NextResponse.json({ data: Client.parse(newClient) });
}