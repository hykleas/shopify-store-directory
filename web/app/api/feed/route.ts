import { guard, json, parseQuery } from "@/lib/api";
import { getFeed } from "@/lib/queries";
import { feedQuerySchema } from "@/lib/validation";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function GET(req: Request) {
  const limited = guard(req, "feed");
  if (limited) return limited;

  const parsed = parseQuery(req, feedQuerySchema);
  if (parsed.error) return parsed.error;

  return json(await getFeed(parsed.data));
}
