-- 008_store_context.sql — magaza duzeyinde kategori onselini sakla.
--
-- Olculen problem: tek bir urun basligindan 220 nis arasindan dogru olani
-- secmek zayif sinyal. Olculen dogruluk %46.
--
-- Gozlem: Shopify magazalari neredeyse her zaman tek nisli. Magazanin adi,
-- aciklamasi ve en sik product_type'lari birlikte cok daha guclu sinyal veriyor
-- (olculen: urun agirlikli %84). Once magazanin kategorisi belirlenir, sonra
-- urunun nisi SADECE o kategorinin nisleri icinde aranir.

ALTER TABLE stores ADD COLUMN IF NOT EXISTS context_category TEXT;
ALTER TABLE stores ADD COLUMN IF NOT EXISTS context_score REAL;
ALTER TABLE stores ADD COLUMN IF NOT EXISTS context_at TIMESTAMPTZ;

-- Baglami hesaplanmayi bekleyen magazalar.
CREATE INDEX IF NOT EXISTS stores_context_pending_idx
  ON stores (id) WHERE context_category IS NULL AND product_count > 0;
