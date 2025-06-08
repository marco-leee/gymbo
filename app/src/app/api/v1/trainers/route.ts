import { Client, Trainer } from "@/models";
import { clientService, trainerService } from "@/services";
import { PostgrestError } from "@supabase/supabase-js";
import { NextRequest, NextResponse } from "next/server";
import { ulid } from 'ulid';

export async function GET(request: NextRequest) {
  const params = request.nextUrl.searchParams;
  const page = Number(params.get("page") ?? "1");
  const limit = Number(params.get("limit") ?? "10");

  const trainers = await trainerService.getTrainers(page, limit);

  return NextResponse.json({ data: trainers });
}

export async function POST(request: NextRequest) {
  const body = await request.json();

  try {
    const trainer = await trainerService.getTrainerByEmail(body.email);

    if (trainer) {
      return NextResponse.json({ error: "Trainer already exists" }, { status: 400 });
    }
  } catch (error: any) {
    if (error instanceof PostgrestError) {
      return NextResponse.json({ error: error.message }, { status: 500 });
    }
    
    return NextResponse.json({ error: error.message }, { status: 500 });
  }

  try {
    const trainer = await trainerService.createTrainer(Trainer.parse({
      id: ulid(),
      email: body.email,
      first_name: body.first_name,
      last_name: body.last_name,
      created_at: new Date(),
      updated_at: new Date(),
    }));

    return NextResponse.json({ data: trainer });
  } catch (error: any) {
    if (error instanceof PostgrestError) {
      return NextResponse.json({ error: error.message }, { status: 500 });
    }
    
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}