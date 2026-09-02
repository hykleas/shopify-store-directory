-- 001_init.sql — core schema
-- Extensions must exist before any vector/trgm column or index is created.
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Keşif kuyruğu: CT loglarından düşen ham domainler
CREATE TABLE IF NOT EXISTS discovery_queue (
  id            BIGSERIAL PRIMARY KEY,
  domain        TEXT UNIQUE NOT NULL,
  source        TEXT NOT NULL,                   -- 'certstream' | 'zonefile' | 'manual'
  status        TEXT NOT NULL DEFAULT 'pending', -- pending|checking|shopify|not_shopify|error
  checked_at    TIMESTAMPTZ,
  attempts      SMALLINT NOT NULL DEFAULT 0,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS discovery_queue_status_created_idx
  ON discovery_queue (status, created_at);

CREATE TABLE IF NOT EXISTS stores (
  id                BIGSERIAL PRIMARY KEY,
  domain            TEXT UNIQUE NOT NULL,
  shop_id           BIGINT,                 -- /meta.json id
  name              TEXT,
  description       TEXT,
  country           CHAR(2),
  currency          CHAR(3),
  language          TEXT,
  tld               TEXT,
  first_seen_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
  launch_date       DATE,                   -- en eski ürün published_at
  product_count     INT NOT NULL DEFAULT 0,
  avg_price_cents   INT,
  min_price_cents   INT,
  max_price_cents   INT,
  primary_category  TEXT,
  is_active         BOOLEAN NOT NULL DEFAULT true,
  is_hidden         BOOLEAN NOT NULL DEFAULT false,  -- kaldırma talebi / robots.txt disallow
  last_crawled_at   TIMESTAMPTZ,
  crawl_priority    SMALLINT NOT NULL DEFAULT 5      -- 1 = en sık
);
CREATE INDEX IF NOT EXISTS stores_country_currency_idx ON stores (country, currency);
CREATE INDEX IF NOT EXISTS stores_launch_date_idx      ON stores (launch_date DESC);
CREATE INDEX IF NOT EXISTS stores_primary_category_idx ON stores (primary_category);

CREATE TABLE IF NOT EXISTS products (
  id                BIGSERIAL PRIMARY KEY,
  store_id          BIGINT NOT NULL REFERENCES stores(id) ON DELETE CASCADE,
  shopify_id        BIGINT NOT NULL,
  handle            TEXT NOT NULL,
  title             TEXT NOT NULL,
  vendor            TEXT,
  product_type      TEXT,
  tags              TEXT[],
  image_url         TEXT,
  image_hash        TEXT,                   -- perceptual hash, Faz 4
  price_cents       INT,
  compare_at_cents  INT,
  category          TEXT,
  niche             TEXT,
  embedding         vector(384),
  published_at      TIMESTAMPTZ,
  first_seen_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
  last_seen_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (store_id, shopify_id)
);
CREATE INDEX IF NOT EXISTS products_category_niche_idx ON products (category, niche);
CREATE INDEX IF NOT EXISTS products_price_idx          ON products (price_cents);
CREATE INDEX IF NOT EXISTS products_title_trgm_idx     ON products USING gin (title gin_trgm_ops);

CREATE TABLE IF NOT EXISTS variants (
  id                BIGSERIAL PRIMARY KEY,
  product_id        BIGINT NOT NULL REFERENCES products(id) ON DELETE CASCADE,
  shopify_id        BIGINT NOT NULL,
  title             TEXT,
  price_cents       INT,
  available         BOOLEAN,
  UNIQUE (product_id, shopify_id)
);

-- Fiyat ve stok durumu geçmişi (Faz 4). Adet tutulmaz, sadece stokta var/yok.
CREATE TABLE IF NOT EXISTS variant_history (
  variant_id        BIGINT NOT NULL REFERENCES variants(id) ON DELETE CASCADE,
  observed_on       DATE NOT NULL,
  price_cents       INT,
  available         BOOLEAN,
  PRIMARY KEY (variant_id, observed_on)
);

-- Katalog aktivitesi. Satış/ciro alanı YOK, eklenmeyecek.
CREATE TABLE IF NOT EXISTS store_metrics (
  store_id          BIGINT NOT NULL REFERENCES stores(id) ON DELETE CASCADE,
  observed_on       DATE NOT NULL,
  new_products      INT,          -- o gün eklenen ürün
  removed_products  INT,          -- o gün katalogdan düşen ürün
  price_changes     INT,          -- fiyatı değişen varyant sayısı
  PRIMARY KEY (store_id, observed_on)
);

CREATE TABLE IF NOT EXISTS removal_requests (
  id          BIGSERIAL PRIMARY KEY,
  domain      TEXT NOT NULL,
  email       TEXT,
  reason      TEXT,
  status      TEXT NOT NULL DEFAULT 'pending',
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
