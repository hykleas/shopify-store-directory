import { neon, type NeonQueryFunction } from "@neondatabase/serverless";

/**
 * Tek DB erisim noktasi. ORM yok, ham SQL.
 *
 * Kural: deger asla SQL metnine gomulmez. `q()` her zaman parametreli
 * calisir ($1, $2 ...); sadece sabit clause parcalari birlestirilir.
 */

let client: NeonQueryFunction<false, false> | null = null;

function getClient(): NeonQueryFunction<false, false> {
  if (!client) {
    const url = process.env.DATABASE_URL;
    if (!url) {
      throw new Error("DATABASE_URL tanimli degil.");
    }
    client = neon(url);
  }
  return client;
}

export async function q<T = Record<string, unknown>>(
  text: string,
  params: unknown[] = [],
): Promise<T[]> {
  const rows = await getClient().query(text, params);
  return rows as T[];
}

export async function q1<T = Record<string, unknown>>(
  text: string,
  params: unknown[] = [],
): Promise<T | null> {
  const rows = await q<T>(text, params);
  return rows.length > 0 ? rows[0] : null;
}

/** DB erisilemedigi durumda sayfa cokmesin diye guvenli sarmalayici. */
export async function safe<T>(fn: () => Promise<T>, fallback: T): Promise<T> {
  try {
    return await fn();
  } catch (err) {
    console.error("[db]", err instanceof Error ? err.message : err);
    return fallback;
  }
}
