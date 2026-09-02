-- 005_supabase_rls.sql — Supabase sertlestirmesi.
--
-- Supabase her `public` tablosunu otomatik olarak PostgREST uzerinden yayinlar.
-- Bu projede PostgREST'i hic kullanmiyoruz: web dogrudan postgres baglantisi
-- ile okuyor, crawler asyncpg ile yaziyor. Bu yuzden tum tablolarda RLS'i
-- aciyoruz ve HICBIR policy tanimlamiyoruz -> anon/authenticated anahtarlarla
-- gelen istekler bos doner. Bizim baglantilarimiz `postgres` rolu (BYPASSRLS)
-- oldugu icin etkilenmez.
--
-- Neon veya duz Postgres'te de zararsiz: policy'siz RLS sadece
-- superuser/owner disindaki rolleri kisitlar.

DO $$
DECLARE
  t text;
BEGIN
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
