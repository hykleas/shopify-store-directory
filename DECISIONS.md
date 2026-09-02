# Kararlar

Spec'te açık bırakılan veya ortam kaynaklı sapmalar. Her satır: karar + gerekçe.

| # | Karar | Gerekçe |
|---|---|---|
| 1 | Next.js 16 (spec'te 15 yazıyordu) | `create-next-app@latest` 16.3.4 kuruyor; App Router API'si aynı, Vercel'in varsayılanı. |
| 2 | Tailwind v4 (PostCSS eklentisi, `tailwind.config` dosyası yok) | Next 16 scaffold'unun getirdiği sürüm; tema token'ları `globals.css` içinde `@theme` ile tanımlandı. |
| 3 | shadcn/ui CLI yerine elle yazılmış shadcn tarzı primitive'ler (`web/components/ui/*`) | CLI Tailwind v4 + Next 16 kombinasyonunda registry'ye bağımlı; ihtiyacımız olan 8 bileşen (button, card, input, select, badge, sheet, skeleton, tabs) cva + tailwind-merge ile 200 satırda karşılanıyor. Bağımlılık ve kırılma yüzeyi daha az. |
| 4 | Migration runner `psycopg[binary]` kullanıyor, crawler `asyncpg` | migrate.py senkron ve tek seferlik; asyncpg'nin çoklu-statement kısıtı (`execute` tek statement) ham .sql dosyaları için uygun değil. |
| 5 | Lokal geliştirme postgres'i `5433` portunda | Makinede 5432'de başka bir postgres olma ihtimaline karşı çakışmayı önlemek için. |
| 6 | Crawler tek konteynerde, tüm worker'lar asyncio task'ı olarak (`run_all.py`) | Tek VPS'te 6 ayrı konteyner yerine tek süreç; bellek ayak izi düşük, embedding modeli tek kez yükleniyor. Her worker ayrıca `python -m <modül>` ile tek başına da çalışabiliyor. |
| 7 | `discovery_queue`'daki `checking` durumu için `FOR UPDATE SKIP LOCKED` | Redis'siz kuyrukta birden fazla worker aynı domaini almasın diye. |
| 8 | Ürün eşleştirme (Faz 4) 8 bantlı LSH + union-find | 1M+ hash'te O(n²) Hamming karşılaştırması pahalı. 64-bit phash 8×8-bit banda bölünüyor; Hamming ≤ 6 olan iki hash güvercin yuvası ilkesiyle en az iki bantta birebir aynı olmak zorunda, o yüzden aday üretimi kayıpsız ve O(n). Tek VPS bütçesine uygun. |
| 9 | Rate limit (API) in-memory LRU, Vercel instance başına | Spec Redis kurmayı yasaklıyor. Serverless'ta instance başına sayım kabaca doğru; amaç kötüye kullanımı kırmak, kesin kota değil. |
| 10 | Görseller Shopify CDN'inden hotlink, `next/image` yerine düz `<img>` | Vercel image optimization kotası ücretsiz planda sınırlı ve spec görsel kopyalamayı yasaklıyor. |
| 11 | `recently_active` sıralaması yalnızca son 7 günün `new_products` toplamı | Satış ima eden hiçbir sinyal karışmasın; isimlendirme de "aktivite" üzerinden. |
| 12 | Docker/psql bu geliştirme makinesinde kurulu değil | Lokal postgres ile duman testi yapılamadı; şema ve worker'lar doğrudan Neon'a karşı doğrulandı. `docker-compose.yml` VPS için yazıldı. |
| 13 | `cdn.shopify.com` gibi paylaşımlı CDN'ler için host aralığı 1 sn yerine 0.25 sn (`CDN_MIN_INTERVAL_S`) | "Saniyede 1 istek" kuralı mağaza sunucularını korumak için. Tek bir CDN host'unda 1 istek/sn, görsel hash'lemeyi (Faz 4) günde ~86k ile sınırlar ve pratikte imkânsız kılar. CDN'ler bu yükü taşımak için var; mağaza domainlerinde kural aynen 1 sn. |
| 14 | Taksonomi 27 kategori / 219 niş (spec 25 / ~225 diyordu) | Kategoriler doğal olarak 27'ye ayrıldı (Digital Products ve Industrial & Business Supplies ayrı tutuldu); niş toplamı hedefin içinde. |
| 15 | Faz 5 index'leri `004_api_indexes.sql`'de (spec 003 diyordu) | 003 numarası niş vektör tablosuna gitti; migration numaraları sırayla ilerliyor. |
| 16 | DB Neon yerine **Supabase** | Kullanıcının isteği; Supabase'de zaten hesabı ve başka projeleri var. Postgres olduğu için şema, `pgvector` ve `pg_trgm` aynen çalışıyor; değişen tek şey web tarafındaki sürücü. |
| 17 | Web sürücüsü `@neondatabase/serverless` yerine `postgres` (postgres.js) | Neon'un HTTP sürücüsü yalnızca Neon endpoint'lerine bağlanır. postgres.js Supabase pooler'ıyla çalışır; `sql.unsafe(text, params)` sayesinde parametreli dinamik SQL kuralı bozulmuyor. |
| 18 | postgres.js `prepare: false`, asyncpg `statement_cache_size=0` | Supabase transaction pooler (pgbouncer) prepared statement'ları bağlantılar arasında taşımaz; cache açık kalırsa rastgele `prepared statement does not exist` hataları gelir. |
| 19 | `005_supabase_rls.sql` — tüm tablolarda policy'siz RLS | Supabase her `public` tablosunu otomatik olarak PostgREST üzerinden yayınlar. Bu projede PostgREST hiç kullanılmıyor; policy'siz RLS anon/authenticated anahtarlarını tamamen kapatır, bizim `postgres` rolüyle açtığımız bağlantılar (BYPASSRLS) etkilenmez. |
| 20 | Crawler için Session pooler (5432), Vercel için Transaction pooler (6543) | Supabase'in direct connection'ı yeni projelerde IPv6-only; VPS'te IPv4 olma ihtimali yüksek. Session pooler IPv4 ve uzun ömürlü bağlantı için uygun; serverless tarafında ise transaction pooler doğru seçim. |
