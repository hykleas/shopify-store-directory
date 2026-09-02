-- 002_activity.sql — Faz 2 sayaci, Faz 4 urun yayilimi, Faz 7 heartbeat.

-- Faz 2: ust uste basarisiz crawl sayaci (3 -> is_active=false).
ALTER TABLE stores ADD COLUMN IF NOT EXISTS fail_count SMALLINT NOT NULL DEFAULT 0;

-- Faz 4: gorsel perceptual hash'ine gore ayni sayilan urun gruplari.
-- Satis/ciro ile ilgisi yoktur; sadece "bu urun kac magazada listeleniyor".
CREATE TABLE IF NOT EXISTS product_matches (
  product_id    BIGINT PRIMARY KEY REFERENCES products(id) ON DELETE CASCADE,
  canonical_id  BIGINT NOT NULL REFERENCES products(id) ON DELETE CASCADE,
  distance      SMALLINT NOT NULL DEFAULT 0,
  matched_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS product_matches_canonical_idx ON product_matches (canonical_id);

-- Canonical grup basina gunluk yayilim anlik goruntusu.
CREATE TABLE IF NOT EXISTS product_spread (
  canonical_id   BIGINT NOT NULL REFERENCES products(id) ON DELETE CASCADE,
  observed_on    DATE NOT NULL,
  store_count    INT NOT NULL,
  min_price_cents INT,
  max_price_cents INT,
  PRIMARY KEY (canonical_id, observed_on)
);
CREATE INDEX IF NOT EXISTS product_spread_observed_idx ON product_spread (observed_on DESC);

-- phash aramasi: ilk 4 hex hane (16 bit) uzerinden bucket'lama.
CREATE INDEX IF NOT EXISTS products_image_hash_idx
  ON products (left(image_hash, 4)) WHERE image_hash IS NOT NULL;
CREATE INDEX IF NOT EXISTS products_image_hash_null_idx
  ON products (id) WHERE image_hash IS NULL AND image_url IS NOT NULL;

-- Faz 7: crawler saglik nabzi. /api/health bunu okur.
CREATE TABLE IF NOT EXISTS crawler_heartbeat (
  id                  SMALLINT PRIMARY KEY DEFAULT 1,
  observed_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
  queue_pending       INT,
  domains_last_hour   INT,
  products_last_hour  INT,
  stores_total        INT,
  products_total      INT,
  notes               TEXT,
  CONSTRAINT crawler_heartbeat_single_row CHECK (id = 1)
);

-- Faz 3: kategorize edilmeyi bekleyen urunleri hizli bulmak icin.
CREATE INDEX IF NOT EXISTS products_pending_embedding_idx
  ON products (id) WHERE embedding IS NULL;
CREATE INDEX IF NOT EXISTS products_pending_category_idx
  ON products (id) WHERE category IS NULL AND embedding IS NOT NULL;
