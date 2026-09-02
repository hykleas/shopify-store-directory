-- 005_supabase_rls.sql — yalnizca Supabase'de calisan sertlestirme.
--
-- Supabase her `public` tablosunu otomatik olarak PostgREST uzerinden yayinlar.
-- Bu projede PostgREST'i hic kullanmiyoruz: web dogrudan postgres baglantisi
-- ile okuyor, crawler asyncpg ile yaziyor. Supabase'deysek tum tablolarda
-- RLS'i acip HICBIR policy tanimlamiyoruz -> anon/authenticated anahtarlarla
-- gelen istekler bos doner. Tablo sahibi rol RLS'i zaten bypass ettigi icin
-- bizim baglantilarimiz etkilenmez.
--
-- Neon / duz Postgres'te `anon` rolu yoktur; orada bu migration hicbir sey
-- yapmaz. Boylece ileride sahibi olmayan bir rolle baglanildiginda sessizce
-- bos sonuc donme riski dogmuyor.

DO $$
DECLARE
  t text;
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'anon') THEN
    RAISE NOTICE 'Supabase degil (anon rolu yok) - RLS adimi atlandi.';
    RETURN;
  END IF;

  FOREACH t IN ARRAY ARRAY[
    'discovery_queue', 'stores', 'products', 'variants', 'variant_history',
    'store_metrics', 'removal_requests', 'product_matches', 'product_spread',
    'crawler_heartbeat', 'niche_vectors', 'schema_migrations'
  ]
  LOOP
    IF EXISTS (
      SELECT 1 FROM pg_tables WHERE schemaname = 'public' AND tablename = t
    ) THEN
      EXECUTE format('ALTER TABLE public.%I ENABLE ROW LEVEL SECURITY', t);
    END IF;
  END LOOP;
END
$$;
