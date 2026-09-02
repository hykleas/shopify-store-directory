import { guard, json, parseQuery } from "@/lib/api";
import { getStores } from "@/lib/queries";
import { storeQuerySchema } from "@/lib/validation";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function GET(req: Request) {
  const limited = guard(req, "stores");
  if (limited) return limited;

  const parsed = parseQuery(req, storeQuerySchema);
  if (parsed.error) return parsed.error;

  return json(await getStores(parsed.data));
}
