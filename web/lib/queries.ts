import { q, q1, safe } from "@/lib/db";
import type {
  CategoryShare,
  FeedPage,
  Health,
  Paged,
  ProductDetail,
  ProductSummary,
  Stats,
  StoreActivityPoint,
  StoreDetail,
  StoreSummary,
} from "@/lib/types";
import type { FeedQuery, ProductQuery, StoreQuery } from "@/lib/validation";

/**
 * Tum SQL burada. Hem route handler'lar hem sayfa render'lari bu fonksiyonlari
 * dogrudan import eder - sayfalar kendi API'sini HTTP ile cagirmaz.
 *
 * Kural: is_hidden = true magazalar hicbir sorgudan donmez.
 */

class Params {
  readonly values: unknown[] = [];
  add(value: unknown): string {
    this.values.push(value);
    return `$${this.values.length}`;
  }
}

const cents = (v: unknown): number | null =>
  v === null || v === undefined ? null : Number(v) / 100;

const num = (v: unknown): number => (v === null || v === undefined ? 0 : Number(v));

const iso = (v: unknown): string | null => {
  if (!v) return null;
  return v instanceof Date ? v.toISOString() : String(v);
};

// ---------------------------------------------------------------- magazalar

const STORE_COLUMNS = `
  s.domain, s.name, s.country, s.currency, s.language, s.tld,
  s.launch_date, s.first_seen_at, s.product_count,
  s.min_price_cents, s.avg_price_cents, s.max_price_cents,
  s.primary_category, s.last_crawled_at, s.is_active
`;

function storeWhere(f: Partial<StoreQuery>, p: Params): string {
  const w: string[] = ["NOT s.is_hidden"];
  if (f.country) w.push(`s.country = ${p.add(f.country)}`);
  if (f.currency) w.push(`s.currency = ${p.add(f.currency)}`);
  if (f.language) w.push(`s.language ILIKE ${p.add(f.language)}`);
  if (f.tld) w.push(`s.tld = ${p.add(f.tld.replace(/^\./, "").toLowerCase())}`);
  // Kategori magazanin birincil kategorisi; nis urun bazinda aranir.
  if (f.category) w.push(`s.primary_category = ${p.add(f.category)}`);
  if (f.niche) {
    w.push(
      `EXISTS (SELECT 1 FROM products pn WHERE pn.store_id = s.id AND pn.niche = ${p.add(f.niche)})`,
    );
  }
  if (f.min_price !== undefined) w.push(`s.avg_price_cents >= ${p.add(f.min_price)}`);
  if (f.max_price !== undefined) w.push(`s.avg_price_cents <= ${p.add(f.max_price)}`);
  if (f.min_products !== undefined) w.push(`s.product_count >= ${p.add(f.min_products)}`);
  if (f.max_products !== undefined) w.push(`s.product_count <= ${p.add(f.max_products)}`);
  if (f.launched_after) w.push(`s.launch_date >= ${p.add(f.launched_after)}::date`);
  if (f.launched_before) w.push(`s.launch_date <= ${p.add(f.launched_before)}::date`);
  return w.join(" AND ");
}

const STORE_SORTS: Record<string, string> = {
  // "recently_active" = son 7 gunde en cok urun EKLEYEN. Satisla ilgisi yoktur.
  newest: "s.launch_date DESC NULLS LAST, s.first_seen_at DESC, s.id DESC",
  products: "s.product_count DESC, s.id DESC",
  recently_active: "COALESCE(r.n, 0) DESC, s.first_seen_at DESC, s.id DESC",
};

function mapStore(row: Record<string, unknown>): StoreSummary {
  return {
    domain: String(row.domain),
    name: (row.name as string | null) ?? null,
    country: (row.country as string | null) ?? null,
    currency: (row.currency as string | null) ?? null,
    language: (row.language as string | null) ?? null,
    tld: (row.tld as string | null) ?? null,
    launch_date: iso(row.launch_date)?.slice(0, 10) ?? null,
    first_seen_at: iso(row.first_seen_at) ?? "",
    product_count: num(row.product_count),
    min_price: cents(row.min_price_cents),
    avg_price: cents(row.avg_price_cents),
    max_price: cents(row.max_price_cents),
    primary_category: (row.primary_category as string | null) ?? null,
    last_crawled_at: iso(row.last_crawled_at),
    new_products_7d: num(row.new_products_7d),
  };
}

export async function getStores(f: StoreQuery): Promise<Paged<StoreSummary>> {
  return safe(async () => {
    const p = new Params();
    const where = storeWhere(f, p);
    const order = STORE_SORTS[f.sort] ?? STORE_SORTS.newest;
    const offset = (f.page - 1) * f.per_page;

    const sql = `
      WITH recent AS (
        SELECT store_id, sum(new_products)::int AS n
        FROM store_metrics
        WHERE observed_on >= CURRENT_DATE - 7
        GROUP BY store_id
      )
      SELECT ${STORE_COLUMNS}, COALESCE(r.n, 0)::int AS new_products_7d
      FROM stores s
      LEFT JOIN recent r ON r.store_id = s.id
      WHERE ${where}
      ORDER BY ${order}
      LIMIT ${p.add(f.per_page)} OFFSET ${p.add(offset)}
    `;

    const cp = new Params();
    const countSql = `SELECT count(*)::int AS total FROM stores s WHERE ${storeWhere(f, cp)}`;

    const [rows, countRow] = await Promise.all([
      q(sql, p.values),
      q1<{ total: number }>(countSql, cp.values),
    ]);

    const total = countRow?.total ?? 0;
    return {
      items: rows.map(mapStore),
      total,
      page: f.page,
      per_page: f.per_page,
      total_pages: Math.max(1, Math.ceil(total / f.per_page)),
    };
  }, emptyPage(f.page, f.per_page));
}

function emptyPage<T>(page: number, perPage: number): Paged<T> {
  return { items: [], total: 0, page, per_page: perPage, total_pages: 1 };
}

export async function getStoreDetail(domain: string): Promise<StoreDetail | null> {
  return safe(async () => {
    const store = await q1<Record<string, unknown>>(
      `
      WITH recent AS (
        SELECT store_id, sum(new_products)::int AS n
        FROM store_metrics
        WHERE observed_on >= CURRENT_DATE - 7
        GROUP BY store_id
      )
      SELECT s.id, ${STORE_COLUMNS}, s.description,
             COALESCE(r.n, 0)::int AS new_products_7d
      FROM stores s
      LEFT JOIN recent r ON r.store_id = s.id
      WHERE s.domain = $1 AND NOT s.is_hidden
      `,
      [domain],
    );
    if (!store) return null;

    const storeId = store.id as number;
    const [activity, categories, products] = await Promise.all([
      q<Record<string, unknown>>(
        `SELECT observed_on, new_products, removed_products, price_changes
         FROM store_metrics
         WHERE store_id = $1 AND observed_on >= CURRENT_DATE - 30
         ORDER BY observed_on`,
        [storeId],
      ),
      q<Record<string, unknown>>(
        `SELECT category, count(*)::int AS product_count
         FROM products
         WHERE store_id = $1 AND category IS NOT NULL
         GROUP BY category
         ORDER BY product_count DESC
         LIMIT 12`,
        [storeId],
      ),
      q<Record<string, unknown>>(
        `${PRODUCT_SELECT}
         WHERE p.store_id = $1
         ORDER BY p.published_at DESC NULLS LAST, p.id DESC
         LIMIT 24`,
        [storeId],
      ),
    ]);

    return {
      ...mapStore(store),
      description: (store.description as string | null) ?? null,
      is_active: Boolean(store.is_active),
      activity: activity.map(
        (a): StoreActivityPoint => ({
          date: iso(a.observed_on)!.slice(0, 10),
          new_products: num(a.new_products),
          removed_products: num(a.removed_products),
          price_changes: num(a.price_changes),
        }),
      ),
      categories: categories.map(
        (c): CategoryShare => ({
          category: String(c.category),
          product_count: num(c.product_count),
        }),
      ),
      products: products.map(mapProduct),
    };
  }, null);
}

// ------------------------------------------------------------------ urunler

/** Yayilim verisi son anlik goruntuden gelir (product_spread gunluk yazilir). */
const PRODUCT_SELECT = `
  SELECT p.id, p.title, p.handle, p.image_url, p.price_cents, p.compare_at_cents,
         p.category, p.niche, p.vendor, p.published_at, p.first_seen_at,
         s.domain AS store_domain, s.name AS store_name,
         s.country AS store_country, s.currency,
         sp.store_count, sp.min_price_cents AS spread_min, sp.max_price_cents AS spread_max
  FROM products p
  JOIN stores s ON s.id = p.store_id AND NOT s.is_hidden
  LEFT JOIN product_matches pm ON pm.product_id = p.id
  LEFT JOIN product_spread sp
         ON sp.canonical_id = pm.canonical_id
        AND sp.observed_on = (SELECT max(observed_on) FROM product_spread)
`;

const PRODUCT_COUNT_FROM = `
  FROM products p
  JOIN stores s ON s.id = p.store_id AND NOT s.is_hidden
  LEFT JOIN product_matches pm ON pm.product_id = p.id
  LEFT JOIN product_spread sp
         ON sp.canonical_id = pm.canonical_id
        AND sp.observed_on = (SELECT max(observed_on) FROM product_spread)
`;

function productWhere(f: Partial<ProductQuery>, p: Params): string {
  const w: string[] = ["TRUE"];
  if (f.q) w.push(`p.title ILIKE ${p.add(`%${f.q}%`)}`);
  if (f.category) w.push(`p.category = ${p.add(f.category)}`);
  if (f.niche) w.push(`p.niche = ${p.add(f.niche)}`);
  if (f.min_price !== undefined) w.push(`p.price_cents >= ${p.add(f.min_price)}`);
  if (f.max_price !== undefined) w.push(`p.price_cents <= ${p.add(f.max_price)}`);
  if (f.country) w.push(`s.country = ${p.add(f.country)}`);
  if (f.currency) w.push(`s.currency = ${p.add(f.currency)}`);
  if (f.store_count_min !== undefined) {
    w.push(`sp.store_count >= ${p.add(f.store_count_min)}`);
  }
  return w.join(" AND ");
}

const PRODUCT_SORTS: Record<string, string> = {
  newest: "p.published_at DESC NULLS LAST, p.id DESC",
  price: "p.price_cents ASC NULLS LAST, p.id DESC",
  // "spread" = kac farkli magazada listelendigi. Satis sinyali degildir.
  spread: "sp.store_count DESC NULLS LAST, p.id DESC",
};

function mapProduct(row: Record<string, unknown>): ProductSummary {
  return {
    id: Number(row.id),
    title: String(row.title),
    handle: String(row.handle),
    image_url: (row.image_url as string | null) ?? null,
    price: cents(row.price_cents),
    compare_at_price: cents(row.compare_at_cents),
    currency: (row.currency as string | null) ?? null,
    category: (row.category as string | null) ?? null,
    niche: (row.niche as string | null) ?? null,
    vendor: (row.vendor as string | null) ?? null,
    published_at: iso(row.published_at),
    first_seen_at: iso(row.first_seen_at) ?? "",
    store_domain: String(row.store_domain),
    store_name: (row.store_name as string | null) ?? null,
    store_country: (row.store_country as string | null) ?? null,
    store_count: row.store_count === null || row.store_count === undefined ? null : Number(row.store_count),
    spread_min_price: cents(row.spread_min),
    spread_max_price: cents(row.spread_max),
  };
}

export async function getProducts(f: ProductQuery): Promise<Paged<ProductSummary>> {
  return safe(async () => {
    const p = new Params();
    const where = productWhere(f, p);
    const order = PRODUCT_SORTS[f.sort] ?? PRODUCT_SORTS.newest;
    const offset = (f.page - 1) * f.per_page;

    const sql = `${PRODUCT_SELECT}
      WHERE ${where}
      ORDER BY ${order}
      LIMIT ${p.add(f.per_page)} OFFSET ${p.add(offset)}`;

    const cp = new Params();
    const countSql = `SELECT count(*)::int AS total ${PRODUCT_COUNT_FROM} WHERE ${productWhere(f, cp)}`;

    const [rows, countRow] = await Promise.all([
      q<Record<string, unknown>>(sql, p.values),
      q1<{ total: number }>(countSql, cp.values),
    ]);

    const total = countRow?.total ?? 0;
    return {
      items: rows.map(mapProduct),
      total,
      page: f.page,
      per_page: f.per_page,
      total_pages: Math.max(1, Math.ceil(total / f.per_page)),
    };
  }, emptyPage(f.page, f.per_page));
}

export async function getProductDetail(id: number): Promise<ProductDetail | null> {
  return safe(async () => {
    const row = await q1<Record<string, unknown>>(
      `${PRODUCT_SELECT} WHERE p.id = $1`,
      [id],
    );
    if (!row) return null;

    const [extra, variants, listings, history] = await Promise.all([
      q1<Record<string, unknown>>(
        `SELECT p.tags, p.product_type,
                COALESCE(pm.canonical_id, p.id) AS canonical_id
         FROM products p
         LEFT JOIN product_matches pm ON pm.product_id = p.id
         WHERE p.id = $1`,
        [id],
      ),
      q<Record<string, unknown>>(
        `SELECT title, price_cents, available FROM variants
         WHERE product_id = $1 ORDER BY price_cents NULLS LAST, id LIMIT 60`,
        [id],
      ),
      q<Record<string, unknown>>(
        `SELECT s.domain AS store_domain, s.name AS store_name, s.country AS store_country,
                s.currency, p2.id AS product_id, p2.handle, p2.price_cents, p2.first_seen_at
         FROM product_matches m
         JOIN products p2 ON p2.id = m.product_id
         JOIN stores  s  ON s.id = p2.store_id AND NOT s.is_hidden
         WHERE m.canonical_id = (
                 SELECT COALESCE(pm.canonical_id, $1)
                 FROM products p LEFT JOIN product_matches pm ON pm.product_id = p.id
                 WHERE p.id = $1
               )
         ORDER BY p2.price_cents ASC NULLS LAST
         LIMIT 60`,
        [id],
      ),
      q<Record<string, unknown>>(
        `SELECT observed_on, store_count FROM product_spread
         WHERE canonical_id = (
                 SELECT COALESCE(pm.canonical_id, $1)
                 FROM products p LEFT JOIN product_matches pm ON pm.product_id = p.id
                 WHERE p.id = $1
               )
           AND observed_on >= CURRENT_DATE - 30
         ORDER BY observed_on`,
        [id],
      ),
    ]);

    return {
      ...mapProduct(row),
      tags: Array.isArray(extra?.tags) ? (extra!.tags as string[]) : [],
      product_type: (extra?.product_type as string | null) ?? null,
      variants: variants.map((v) => ({
        title: (v.title as string | null) ?? null,
        price: cents(v.price_cents),
        available: v.available === null || v.available === undefined ? null : Boolean(v.available),
      })),
      listings: listings.map((l) => ({
        store_domain: String(l.store_domain),
        store_name: (l.store_name as string | null) ?? null,
        store_country: (l.store_country as string | null) ?? null,
        product_id: Number(l.product_id),
        handle: String(l.handle),
        price: cents(l.price_cents),
        currency: (l.currency as string | null) ?? null,
        first_seen_at: iso(l.first_seen_at) ?? "",
      })),
      spread_history: history.map((h) => ({
        date: iso(h.observed_on)!.slice(0, 10),
        store_count: num(h.store_count),
      })),
    };
  }, null);
}

// --------------------------------------------------------------------- feed

/**
 * Finder akisi. Siralama = tazelik + yayilim ("momentum"); her ek magaza
 * 2 gunluk tazelige denk sayilir. Satis/ciro sinyali yoktur.
 */
const FEED_SCORE = `(
  EXTRACT(EPOCH FROM p.first_seen_at)::bigint + COALESCE(sp.store_count, 0) * 172800
)`;

function encodeCursor(score: number, id: number): string {
  return Buffer.from(`${score}:${id}`, "utf8").toString("base64url");
}

function decodeCursor(cursor?: string): { score: number; id: number } | null {
  if (!cursor) return null;
  try {
    const [score, id] = Buffer.from(cursor, "base64url").toString("utf8").split(":");
    const s = Number(score);
    const i = Number(id);
    if (!Number.isFinite(s) || !Number.isFinite(i)) return null;
    return { score: s, id: i };
  } catch {
    return null;
  }
}

export async function getFeed(f: FeedQuery): Promise<FeedPage> {
  return safe(async () => {
    const p = new Params();
    const w: string[] = ["p.image_url IS NOT NULL"];
    if (f.category) w.push(`p.category = ${p.add(f.category)}`);
    if (f.niche) w.push(`p.niche = ${p.add(f.niche)}`);
    const after = decodeCursor(f.cursor);
    if (after) {
      w.push(
        `(${FEED_SCORE}, p.id) < (${p.add(after.score)}::bigint, ${p.add(after.id)}::bigint)`,
      );
    }

    const rows = await q<Record<string, unknown>>(
      `${PRODUCT_SELECT.replace("SELECT p.id,", `SELECT ${FEED_SCORE} AS score, p.id,`)}
       WHERE ${w.join(" AND ")}
       ORDER BY ${FEED_SCORE} DESC, p.id DESC
       LIMIT ${p.add(f.limit)}`,
      p.values,
    );

    const items = rows.map(mapProduct);
    const last = rows[rows.length - 1];
    return {
      items,
      next_cursor:
        rows.length === f.limit && last
          ? encodeCursor(Number(last.score), Number(last.id))
          : null,
    };
  }, { items: [], next_cursor: null });
}

// -------------------------------------------------------------------- genel

export async function getStats(): Promise<Stats> {
  return safe(async () => {
    const row = await q1<Record<string, unknown>>(`
      SELECT
        (SELECT count(*) FROM stores WHERE NOT is_hidden)::int                       AS stores,
        (SELECT count(*) FROM products)::int                                         AS products,
        (SELECT count(*) FROM variants)::int                                         AS variants,
        (SELECT count(DISTINCT category) FROM products
          WHERE category IS NOT NULL AND category <> 'uncategorized')::int           AS categories,
        (SELECT count(*) FROM stores
          WHERE NOT is_hidden AND first_seen_at >= CURRENT_DATE)::int                AS stores_added_today,
        (SELECT count(*) FROM products WHERE first_seen_at >= CURRENT_DATE)::int     AS products_added_today,
        (SELECT count(DISTINCT country) FROM stores
          WHERE NOT is_hidden AND country IS NOT NULL)::int                          AS countries
    `);
    return {
      stores: num(row?.stores),
      products: num(row?.products),
      variants: num(row?.variants),
      categories: num(row?.categories),
      stores_added_today: num(row?.stores_added_today),
      products_added_today: num(row?.products_added_today),
      countries: num(row?.countries),
    };
  }, {
    stores: 0, products: 0, variants: 0, categories: 0,
    stores_added_today: 0, products_added_today: 0, countries: 0,
  });
}

export async function getHealth(): Promise<Health> {
  return safe(async () => {
    const row = await q1<Record<string, unknown>>(
      `SELECT observed_at, queue_pending, domains_last_hour, products_last_hour,
              stores_total, products_total,
              observed_at < now() - interval '3 hours' AS stale
       FROM crawler_heartbeat WHERE id = 1`,
    );
    if (!row) {
      return {
        ok: false, observed_at: null, queue_pending: null, domains_last_hour: null,
        products_last_hour: null, stores_total: null, products_total: null, stale: true,
      };
    }
    return {
      ok: !row.stale,
      observed_at: iso(row.observed_at),
      queue_pending: row.queue_pending === null ? null : num(row.queue_pending),
      domains_last_hour: row.domains_last_hour === null ? null : num(row.domains_last_hour),
      products_last_hour: row.products_last_hour === null ? null : num(row.products_last_hour),
      stores_total: row.stores_total === null ? null : num(row.stores_total),
      products_total: row.products_total === null ? null : num(row.products_total),
      stale: Boolean(row.stale),
    };
  }, {
    ok: false, observed_at: null, queue_pending: null, domains_last_hour: null,
    products_last_hour: null, stores_total: null, products_total: null, stale: true,
  });
}

export type FilterOptions = {
  countries: { value: string; count: number }[];
  currencies: { value: string; count: number }[];
  categories: { value: string; count: number }[];
  niches: { value: string; category: string; count: number }[];
  tlds: { value: string; count: number }[];
};

export async function getFilterOptions(): Promise<FilterOptions> {
  return safe(async () => {
    const [countries, currencies, categories, niches, tlds] = await Promise.all([
      q<Record<string, unknown>>(
        `SELECT country AS value, count(*)::int AS count FROM stores
         WHERE NOT is_hidden AND country IS NOT NULL
         GROUP BY country ORDER BY count DESC LIMIT 60`,
      ),
      q<Record<string, unknown>>(
        `SELECT currency AS value, count(*)::int AS count FROM stores
         WHERE NOT is_hidden AND currency IS NOT NULL
         GROUP BY currency ORDER BY count DESC LIMIT 40`,
      ),
      q<Record<string, unknown>>(
        `SELECT category AS value, count(*)::int AS count FROM products
         WHERE category IS NOT NULL AND category <> 'uncategorized'
         GROUP BY category ORDER BY count DESC LIMIT 40`,
      ),
      q<Record<string, unknown>>(
        `SELECT niche AS value, category, count(*)::int AS count FROM products
         WHERE niche IS NOT NULL
         GROUP BY niche, category ORDER BY count DESC LIMIT 250`,
      ),
      q<Record<string, unknown>>(
        `SELECT tld AS value, count(*)::int AS count FROM stores
         WHERE NOT is_hidden AND tld IS NOT NULL
         GROUP BY tld ORDER BY count DESC LIMIT 30`,
      ),
    ]);
    return {
      countries: countries.map((r) => ({ value: String(r.value), count: num(r.count) })),
      currencies: currencies.map((r) => ({ value: String(r.value), count: num(r.count) })),
      categories: categories.map((r) => ({ value: String(r.value), count: num(r.count) })),
      niches: niches.map((r) => ({
        value: String(r.value),
        category: String(r.category ?? ""),
        count: num(r.count),
      })),
      tlds: tlds.map((r) => ({ value: String(r.value), count: num(r.count) })),
    };
  }, { countries: [], currencies: [], categories: [], niches: [], tlds: [] });
}

export async function getLatestStores(limit = 12): Promise<StoreSummary[]> {
  const page = await getStores({
    sort: "newest",
    page: 1,
    per_page: limit,
  } as StoreQuery);
  return page.items;
}

// ------------------------------------------------------- kaldirma talepleri

export async function createRemovalRequest(input: {
  domain: string;
  email?: string;
  reason?: string;
}): Promise<number | null> {
  return safe(async () => {
    const row = await q1<{ id: number }>(
      `INSERT INTO removal_requests (domain, email, reason) VALUES ($1, $2, $3) RETURNING id`,
      [input.domain, input.email ?? null, input.reason ?? null],
    );
    return row?.id ?? null;
  }, null);
}

/** Sitemap icin: indekslenebilir tum domainler ve urun id'leri. */
export async function getSitemapEntries(): Promise<{
  stores: { domain: string; updated: string | null }[];
  products: { id: number; updated: string | null }[];
  categories: string[];
  niches: string[];
}> {
  return safe(async () => {
    const [stores, products, cats, niches] = await Promise.all([
      q<Record<string, unknown>>(
        `SELECT domain, last_crawled_at FROM stores
         WHERE NOT is_hidden ORDER BY first_seen_at DESC LIMIT 20000`,
      ),
      q<Record<string, unknown>>(
        `SELECT p.id, p.last_seen_at FROM products p
         JOIN stores s ON s.id = p.store_id AND NOT s.is_hidden
         ORDER BY p.first_seen_at DESC LIMIT 20000`,
      ),
      q<Record<string, unknown>>(
        `SELECT DISTINCT category FROM products
         WHERE category IS NOT NULL AND category <> 'uncategorized'`,
      ),
      q<Record<string, unknown>>(
        `SELECT DISTINCT niche FROM products WHERE niche IS NOT NULL`,
      ),
    ]);
    return {
      stores: stores.map((s) => ({
        domain: String(s.domain),
        updated: iso(s.last_crawled_at),
      })),
      products: products.map((p) => ({ id: Number(p.id), updated: iso(p.last_seen_at) })),
      categories: cats.map((c) => String(c.category)),
      niches: niches.map((n) => String(n.niche)),
    };
  }, { stores: [], products: [], categories: [], niches: [] });
}
