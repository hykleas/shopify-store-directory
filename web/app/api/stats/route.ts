import { guard, json } from "@/lib/api";
import { getStats } from "@/lib/queries";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function GET(req: Request) {
  const limited = guard(req, "stats");
  if (limited) return limited;

  return json(await getStats());
}
