import { errorResponse, guard, json } from "@/lib/api";
import { getStoreDetail } from "@/lib/queries";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function GET(
  req: Request,
  ctx: { params: Promise<{ domain: string }> },
) {
  const limited = guard(req, "store-detail");
  if (limited) return limited;

  const { domain } = await ctx.params;
  const normalized = decodeURIComponent(domain).trim().toLowerCase();
  if (!/^[a-z0-9.-]+\.[a-z]{2,}$/.test(normalized)) {
    return errorResponse("Gecersiz alan adi", 400);
  }

  const store = await getStoreDetail(normalized);
  if (!store) return errorResponse("Magaza bulunamadi", 404);
  return json(store);
}
