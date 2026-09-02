/**
 * API cevap tipleri.
 *
 * Bilincli olarak YOK ve eklenmeyecek: satis adedi, ciro, kazanc, bunlarin
 * tahmini, aralik veya rozet hali. Sadece katalog aktivitesi tasiniyor.
 */

export type StoreSummary = {
  domain: string;
  name: string | null;
  country: string | null;
  currency: string | null;
  language: string | null;
  tld: string | null;
  launch_date: string | null;
  first_seen_at: string;
  product_count: number;
  min_price: number | null;
  avg_price: number | null;
  max_price: number | null;
  primary_category: string | null;
  last_crawled_at: string | null;
  /** Son 7 gunde katalogua eklenen urun sayisi. Satisla ilgisi yoktur. */
  new_products_7d: number;
};

export type StoreActivityPoint = {
  date: string;
  new_products: number;
  removed_products: number;
  price_changes: number;
};

export type CategoryShare = {
  category: string;
  product_count: number;
};

export type StoreDetail = StoreSummary & {
  description: string | null;
  is_active: boolean;
  activity: StoreActivityPoint[];
  categories: CategoryShare[];
  products: ProductSummary[];
};

export type ProductSummary = {
  id: number;
  title: string;
  handle: string;
  image_url: string | null;
  price: number | null;
  compare_at_price: number | null;
  currency: string | null;
  category: string | null;
  niche: string | null;
  vendor: string | null;
  published_at: string | null;
  first_seen_at: string;
  store_domain: string;
  store_name: string | null;
  store_country: string | null;
  /** Ayni gorseli listeleyen magaza sayisi (yayilim). */
  store_count: number | null;
  spread_min_price: number | null;
  spread_max_price: number | null;
};

export type ProductListing = {
  store_domain: string;
  store_name: string | null;
  store_country: string | null;
  product_id: number;
  handle: string;
  price: number | null;
  currency: string | null;
  first_seen_at: string;
};

export type ProductDetail = ProductSummary & {
  tags: string[];
  product_type: string | null;
  variants: { title: string | null; price: number | null; available: boolean | null }[];
  listings: ProductListing[];
  /** Yayilim gecmisi: kac gun once kac magazadaydi. */
  spread_history: { date: string; store_count: number }[];
};

export type Paged<T> = {
  items: T[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
};

export type Stats = {
  stores: number;
  products: number;
  variants: number;
  categories: number;
  stores_added_today: number;
  products_added_today: number;
  countries: number;
};

export type Health = {
  ok: boolean;
  observed_at: string | null;
  queue_pending: number | null;
  domains_last_hour: number | null;
  products_last_hour: number | null;
  stores_total: number | null;
  products_total: number | null;
  stale: boolean;
};

export type FeedPage = {
  items: ProductSummary[];
  next_cursor: string | null;
};
