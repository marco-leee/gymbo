import { Client } from "@/app/models";
import { clientService } from "@/app/services";
import { PostgrestError } from "@supabase/supabase-js";
import { NextRequest, NextResponse } from "next/server";
import { ulid } from 'ulid';

export async function GET(request: NextRequest) {
  const params = request.nextUrl.searchParams;
  const page = Number(params.get("page") ?? "1");
  const limit = Number(params.get("limit") ?? "10");

  const clients = await clientService.getClients(page, limit);

  return NextResponse.json({ data: clients });
}

export async function POST(request: NextRequest) {
  const body = await request.json();

  try {
    const client = await clientService.getClientByEmail(body.email);

    if (client) {
      return NextResponse.json({ error: "Client already exists" }, { status: 400 });
    }
  } catch (error: any) {
    if (error instanceof PostgrestError) {
      return NextResponse.json({ error: error.message }, { status: 500 });
    }
    
    return NextResponse.json({ error: error.message }, { status: 500 });
  }

  try {
    const client = await clientService.createClient(Client.parse({
      id: ulid(),
      email: body.email,
      first_name: body.first_name,
      last_name: body.last_name,
      created_at: new Date(),
      updated_at: new Date(),
    }));

    return NextResponse.json({ data: client });
  } catch (error: any) {
    console.log(error);
    if (error instanceof PostgrestError) {
      return NextResponse.json({ error: error.message }, { status: 500 });
    }
    
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}