import { NextResponse } from "next/server";

import { errorResponse, guard } from "@/lib/api";
import { createRemovalRequest } from "@/lib/queries";
import { removalRequestSchema } from "@/lib/validation";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function POST(req: Request) {
  // Spam'i kirmak icin saatte 3 talep / IP.
  const limited = guard(req, "removal", 3, 60 * 60 * 1000);
  if (limited) return limited;

  let body: unknown;
  try {
    body = await req.json();
  } catch {
    return errorResponse("Gecersiz JSON govdesi", 400);
  }

  const parsed = removalRequestSchema.safeParse(body);
  if (!parsed.success) {
    return errorResponse("Gecersiz veri", 400, parsed.error.flatten().fieldErrors);
  }

  const id = await createRemovalRequest(parsed.data);
  if (id === null) return errorResponse("Talep kaydedilemedi", 500);

  return NextResponse.json(
    {
      id,
      status: "pending",
      message: "Talebiniz alindi. 7 gun icinde islenecek.",
    },
    { status: 201, headers: { "cache-control": "no-store" } },
  );
}
