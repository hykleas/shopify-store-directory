import { errorResponse, guard, json } from "@/lib/api";
import { getProductDetail } from "@/lib/queries";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function GET(req: Request, ctx: { params: Promise<{ id: string }> }) {
  const limited = guard(req, "product-detail");
  if (limited) return limited;

  const { id } = await ctx.params;
  const numeric = Number(id);
  if (!Number.isInteger(numeric) || numeric <= 0) {
    return errorResponse("Gecersiz urun id", 400);
  }

  const product = await getProductDetail(numeric);
  if (!product) return errorResponse("Urun bulunamadi", 404);
  return json(product);
}
