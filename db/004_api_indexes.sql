-- 004_api_indexes.sql — API sorgulari icin index'ler (Faz 5).
-- Her biri lib/queries.ts icindeki somut bir sorguyu hedefler.

-- /stores : "recently_active" CTE'si son 7 gunu tarar.
CREATE INDEX IF NOT EXISTS store_metrics_observed_idx
  ON store_metrics (observed_on DESC, store_id);

-- /stores : sort=products ve sort=newest
CREATE INDEX IF NOT EXISTS stores_product_count_idx
  ON stores (product_count DESC) WHERE NOT is_hidden;
CREATE INDEX IF NOT EXISTS stores_first_seen_idx
  ON stores (first_seen_at DESC) WHERE NOT is_hidden;

-- /stores : filtreler
CREATE INDEX IF NOT EXISTS stores_tld_idx        ON stores (tld)        WHERE NOT is_hidden;
CREATE INDEX IF NOT EXISTS stores_language_idx   ON stores (language)   WHERE NOT is_hidden;
CREATE INDEX IF NOT EXISTS stores_avg_price_idx  ON stores (avg_price_cents) WHERE NOT is_hidden;

-- /stores?niche=... -> EXISTS (products where store_id and niche)
CREATE INDEX IF NOT EXISTS products_store_niche_idx ON products (store_id, niche);

-- /stores/{domain} : magazanin urun listesi
CREATE INDEX IF NOT EXISTS products_store_published_idx
  ON products (store_id, published_at DESC);

-- /products : sort=newest ve /feed skoru
CREATE INDEX IF NOT EXISTS products_published_idx  ON products (published_at DESC);
CREATE INDEX IF NOT EXISTS products_first_seen_idx ON products (first_seen_at DESC);

-- /products : kategori + fiyat birlikte filtrelenir
CREATE INDEX IF NOT EXISTS products_category_price_idx ON products (category, price_cents);

-- /products/{id} : ayni canonical'i satan magazalar
CREATE INDEX IF NOT EXISTS product_matches_canonical_product_idx
  ON product_matches (canonical_id, product_id);

-- Planner'in yeni index'leri hemen kullanabilmesi icin.
ANALYZE stores;
ANALYZE products;
ANALYZE store_metrics;
