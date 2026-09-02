import { z } from "zod";

/** Query string parametreleri: her endpoint icin tek dogrulama noktasi. */

const trimmed = (max: number) =>
  z
    .string()
    .trim()
    .max(max)
    .transform((v) => (v === "" ? undefined : v))
    .optional();

const intIn = (min: number, max: number) =>
  z.coerce.number().int().min(min).max(max).optional();

/** Kullanicidan gelen fiyat birim para (19.99), DB'de cent. */
const priceToCents = z.coerce
  .number()
  .min(0)
  .max(1_000_000)
  .transform((v) => Math.round(v * 100))
  .optional();

const isoDate = z
  .string()
  .regex(/^\d{4}-\d{2}-\d{2}$/, "YYYY-MM-DD bekleniyor")
  .optional();

const country = z
  .string()
  .trim()
  .regex(/^[A-Za-z]{2}$/)
  .transform((v) => v.toUpperCase())
  .optional();

const currency = z
  .string()
  .trim()
  .regex(/^[A-Za-z]{3}$/)
  .transform((v) => v.toUpperCase())
  .optional();

export const storeQuerySchema = z.object({
  country,
  currency,
  language: trimmed(12),
  tld: trimmed(24),
  category: trimmed(80),
  niche: trimmed(80),
  min_price: priceToCents,
  max_price: priceToCents,
  min_products: intIn(0, 1_000_000),
  max_products: intIn(0, 1_000_000),
  launched_after: isoDate,
  launched_before: isoDate,
  sort: z.enum(["newest", "products", "recently_active"]).default("newest"),
  page: z.coerce.number().int().min(1).max(2000).default(1),
  per_page: z.coerce.number().int().min(1).max(50).default(24),
});

export const productQuerySchema = z.object({
  q: trimmed(120),
  category: trimmed(80),
  niche: trimmed(80),
  min_price: priceToCents,
  max_price: priceToCents,
  country,
  currency,
  store_count_min: intIn(1, 10_000),
  sort: z.enum(["newest", "price", "spread"]).default("newest"),
  page: z.coerce.number().int().min(1).max(2000).default(1),
  per_page: z.coerce.number().int().min(1).max(50).default(24),
});

export const feedQuerySchema = z.object({
  cursor: trimmed(120),
  category: trimmed(80),
  niche: trimmed(80),
  limit: z.coerce.number().int().min(1).max(50).default(20),
});

export const removalRequestSchema = z.object({
  domain: z
    .string()
    .trim()
    .toLowerCase()
    .min(4)
    .max(253)
    .regex(/^[a-z0-9.-]+\.[a-z]{2,}$/, "Gecerli bir alan adi girin"),
  email: z.string().trim().email().max(254).optional().or(z.literal("").transform(() => undefined)),
  reason: z.string().trim().max(2000).optional(),
});

export type StoreQuery = z.infer<typeof storeQuerySchema>;
export type ProductQuery = z.infer<typeof productQuerySchema>;
export type FeedQuery = z.infer<typeof feedQuerySchema>;
export type RemovalRequestInput = z.infer<typeof removalRequestSchema>;

/** URLSearchParams / Next searchParams -> düz obje (ilk deger kazanir). */
export function toRecord(
  input: URLSearchParams | Record<string, string | string[] | undefined>,
): Record<string, string> {
  const out: Record<string, string> = {};
  if (input instanceof URLSearchParams) {
    for (const [k, v] of input.entries()) {
      if (out[k] === undefined && v !== "") out[k] = v;
    }
    return out;
  }
  for (const [k, v] of Object.entries(input)) {
    const value = Array.isArray(v) ? v[0] : v;
    if (value !== undefined && value !== "") out[k] = value;
  }
  return out;
}
