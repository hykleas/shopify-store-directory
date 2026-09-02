-- 007_niche_examples.sql — nis vektorleri: ortalama yerine tek tek ornekler.
--
-- Olculen problem: bir nisin 7 ornek basligini ortalayinca ortaya cikan vektor
-- "urun basligi" ortak yonune yakinsiyor, konuyu ayirt etmiyordu. E5'te tum
-- benzerlikler 0.85-0.92 araligina sikismisti. Ornekleri tek tek tutup en
-- yakinini secmek ayirt ediciligi geri getiriyor (test: 1/12 -> 3/15).
--
-- Tablo ~1.500 satir; IVFFlat gereksiz, sequential scan zaten hizli.

ALTER TABLE niche_vectors ADD COLUMN IF NOT EXISTS example_idx SMALLINT NOT NULL DEFAULT 0;
ALTER TABLE niche_vectors ADD COLUMN IF NOT EXISTS example_text TEXT;

-- Eski (model, category, niche) tekilligi artik gecersiz: nis basina cok satir var.
ALTER TABLE niche_vectors DROP CONSTRAINT IF EXISTS niche_vectors_model_category_niche_key;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'niche_vectors_model_cat_niche_idx_key'
  ) THEN
    -- Ortalama donemi kalintilarini temizle, yeniden kurulacak.
    DELETE FROM niche_vectors;
    ALTER TABLE niche_vectors
      ADD CONSTRAINT niche_vectors_model_cat_niche_idx_key
      UNIQUE (model, category, niche, example_idx);
  END IF;
END
$$;
