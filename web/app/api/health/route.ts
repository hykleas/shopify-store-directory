import { NextResponse } from "next/server";

import { guard } from "@/lib/api";
import { getHealth } from "@/lib/queries";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function GET(req: Request) {
  const limited = guard(req, "health");
  if (limited) return limited;

  const health = await getHealth();
  return NextResponse.json(health, {
    status: health.ok ? 200 : 503,
    headers: { "cache-control": "no-store" },
  });
}
