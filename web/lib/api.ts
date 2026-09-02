import { NextResponse } from "next/server";
import type { ZodType } from "zod";

import { clientIp, rateLimit } from "@/lib/rate-limit";
import { toRecord } from "@/lib/validation";

/** Route handler'lar icin ortak yardimcilar. */

export const API_RATE_LIMIT = 120; // istek / dakika / IP
export const API_RATE_WINDOW_MS = 60_000;

export function json(data: unknown, init?: ResponseInit): NextResponse {
  return NextResponse.json(data, {
    ...init,
    headers: {
      "cache-control": "public, s-maxage=60, stale-while-revalidate=300",
      ...(init?.headers ?? {}),
    },
  });
}

export function errorResponse(message: string, status: number, extra?: unknown): NextResponse {
  return NextResponse.json(
    { error: message, ...(extra ? { details: extra } : {}) },
    { status, headers: { "cache-control": "no-store" } },
  );
}

/** Limit asildiysa hazir 429 cevabi, degilse null. */
export function guard(
  req: Request,
  bucket: string,
  limit = API_RATE_LIMIT,
  windowMs = API_RATE_WINDOW_MS,
): NextResponse | null {
  const result = rateLimit(`${bucket}:${clientIp(req)}`, limit, windowMs);
  if (result.ok) return null;
  return NextResponse.json(
    { error: "Cok fazla istek. Biraz sonra tekrar deneyin." },
    {
      status: 429,
      headers: {
        "cache-control": "no-store",
        "retry-after": String(result.resetInSeconds),
        "x-ratelimit-limit": String(result.limit),
        "x-ratelimit-remaining": "0",
      },
    },
  );
}

export function parseQuery<T>(
  req: Request,
  schema: ZodType<T>,
): { data: T; error: null } | { data: null; error: NextResponse } {
  const url = new URL(req.url);
  const parsed = schema.safeParse(toRecord(url.searchParams));
  if (!parsed.success) {
    return {
      data: null,
      error: errorResponse("Gecersiz parametre", 400, parsed.error.flatten().fieldErrors),
    };
  }
  return { data: parsed.data, error: null };
}
