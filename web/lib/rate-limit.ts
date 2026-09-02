/**
 * IP bazli, bellek ici rate limit.
 *
 * Redis kurmuyoruz (spec). Vercel'de sayac instance basina tutulur; amac
 * kotuye kullanimi kirmak, kesin kota uygulamak degil.
 */

type Bucket = { count: number; resetAt: number };

const MAX_KEYS = 5000;
const buckets = new Map<string, Bucket>();

function prune(now: number): void {
  for (const [key, b] of buckets) {
    if (b.resetAt <= now) buckets.delete(key);
  }
  // LRU yerine en eski eklenenden at: Map ekleme sirasini korur.
  while (buckets.size > MAX_KEYS) {
    const oldest = buckets.keys().next().value;
    if (oldest === undefined) break;
    buckets.delete(oldest);
  }
}

export type RateLimitResult = {
  ok: boolean;
  remaining: number;
  limit: number;
  resetInSeconds: number;
};

export function rateLimit(key: string, limit: number, windowMs: number): RateLimitResult {
  const now = Date.now();
  if (buckets.size > MAX_KEYS / 2) prune(now);

  const existing = buckets.get(key);
  if (!existing || existing.resetAt <= now) {
    buckets.set(key, { count: 1, resetAt: now + windowMs });
    return { ok: true, remaining: limit - 1, limit, resetInSeconds: Math.ceil(windowMs / 1000) };
  }

  existing.count += 1;
  const resetInSeconds = Math.max(1, Math.ceil((existing.resetAt - now) / 1000));
  return {
    ok: existing.count <= limit,
    remaining: Math.max(0, limit - existing.count),
    limit,
    resetInSeconds,
  };
}

/** Vercel/proxy arkasinda istemci IP'si. */
export function clientIp(req: Request): string {
  const forwarded = req.headers.get("x-forwarded-for");
  if (forwarded) return forwarded.split(",")[0]!.trim();
  return req.headers.get("x-real-ip") ?? "unknown";
}
