-- 003_categorize.sql — nis vektorleri, tamami DB tarafinda atama icin.

CREATE TABLE IF NOT EXISTS niche_vectors (
  id         SERIAL PRIMARY KEY,
  model      TEXT NOT NULL,
  category   TEXT NOT NULL,
  niche      TEXT NOT NULL,
  embedding  vector(384) NOT NULL,
  built_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (model, category, niche)
);

-- 219 satirlik tablo; IVFFlat gereksiz, sequential scan zaten hizli.
CREATE INDEX IF NOT EXISTS niche_vectors_model_idx ON niche_vectors (model);
