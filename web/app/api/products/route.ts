import { guard, json, parseQuery } from "@/lib/api";
import { getProducts } from "@/lib/queries";
import { productQuerySchema } from "@/lib/validation";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function GET(req: Request) {
  const limited = guard(req, "products");
  if (limited) return limited;

  const parsed = parseQuery(req, productQuerySchema);
  if (parsed.error) return parsed.error;

  return json(await getProducts(parsed.data));
}
