import postgres from "postgres";

/**
 * Tek DB erisim noktasi. ORM yok, ham SQL.
 *
 * Supabase Postgres'e postgres.js ile baglaniyoruz. Vercel'de transaction
 * pooler (port 6543) kullanildigi icin `prepare: false` sart - pgbouncer
 * transaction modunda prepared statement'lar baglantilar arasi tasinmaz.
 *
 * Kural: deger asla SQL metnine gomulmez. `q()` her zaman parametreli
 * calisir ($1, $2 ...); sadece sabit clause parcalari birlestirilir.
 */

type Client = ReturnType<typeof postgres>;

let client: Client | null = null;

function getClient(): Client {
  if (!client) {
    const url = process.env.DATABASE_URL;
    if (!url) {
      throw new Error("DATABASE_URL tanimli degil.");
    }
    client = postgres(url, {
      prepare: false,
      max: 1, // serverless: instance basina tek baglanti yeter
      idle_timeout: 20,
      connect_timeout: 10,
      ssl: url.includes("localhost") || url.includes("127.0.0.1") ? false : "require",
      onnotice: () => {},
    });
  }
  return client;
}

export async function q<T = Record<string, unknown>>(
  text: string,
  params: unknown[] = [],
): Promise<T[]> {
  // sql.unsafe(text, params) parametreli calisir: degerler SQL'e gomulmez.
  const rows = await getClient().unsafe(text, params as never[]);
  return rows as unknown as T[];
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
