# Shopify Store & Product Directory

Yeni açılan Shopify mağazalarını keşfeden, kataloglarını çeken, ürünleri kategorize
eden ve **katalog aktivitesini** izleyen ücretsiz araştırma platformu.

## Mimari

| Katman | Seçim |
|---|---|
| DB | Supabase (Postgres) + `pgvector` + `pg_trgm` |
| Web + API | Next.js (App Router), TypeScript, Tailwind, Route Handlers |
| DB erişimi (web) | `postgres` (postgres.js), ham SQL — ORM yok |
| Crawler | Python 3.12, `httpx` (async), `asyncio`, `asyncpg` |
| Queue | Postgres tabanlı job tablosu (`discovery_queue`) — Redis yok |
| Kategorizasyon | `sentence-transformers` / `all-MiniLM-L6-v2`, lokal CPU |
| Deploy | web → Vercel, crawler → tek VPS (Docker Compose) |
| PostgREST | Kullanılmıyor. Tüm tablolarda policy'siz RLS açık (`005`), Supabase anon anahtarı hiçbir şey göremez. |

```
/crawler   Python worker'ları (VPS)
/web       Next.js frontend + API (Vercel)
/db        numaralı migration .sql dosyaları + migrate.py
```

## KESİN KURALLAR — ihlal etme, "sonra ekleriz" diye altyapı da bırakma

1. **Mağaza kazancı / cirosu / satış adedi hiçbir yerde tahmin edilmez,
   hesaplanmaz, saklanmaz, gösterilmez.** Ne sayı, ne aralık, ne rozet,
   ne "yüksek/düşük" etiketi. Veritabanında böyle bir kolon açılmaz.
2. **Stok adedi sorgulanmaz.** `cart/add.js`, `/products/x.js?variant=`,
   checkout veya benzeri stok-adedi sızdıran endpoint'lere hiç gidilmez.
   Sadece `products.json`'daki `available` boolean'ı tutulur.
3. **Ürün ücretsiz.** Pricing sayfası, plan tier'ı, paywall, kullanım kotası,
   "upgrade" CTA'sı, kayıt duvarı YOK.
4. **Kişisel veri toplanmaz.** Mağaza sahibinin e-postası, telefonu, ismi
   çekilmez ve saklanmaz. "Leads" özelliği yok (GDPR).
5. **Blok atlatılmaz.** Login duvarı arkasına geçilmez, captcha aşılmaz,
   proxy rotasyonu ile IP bloğu atlatılmaz. Sadece herkese açık endpoint'ler.
6. **Görseller kopyalanmaz.** Shopify CDN URL'i hotlink edilir veya sadece
   perceptual hash tutulur; kendi sunucumuza indirilmez.

## Crawler kuralları (tüm worker'lar için geçerli)

- User-Agent: `StoreDirectoryBot/1.0 (+https://<site>/bot)` — kimlik gizlenmez.
- Aynı host'a **saniyede en fazla 1 istek**. Tek istisna paylaşımlı CDN'ler
  (`cdn.shopify.com` vb.) — `config.CDN_HOSTS` + `CDN_MIN_INTERVAL_S`, bkz. DECISIONS #13.
- `429` veya `503` alınan host **24 saat blacklist**.
- `robots.txt` kontrol edilir; ilgili yol Disallow ise mağaza `is_hidden=true`.
- **Tüm HTTP çağrıları `core/http.py` içindeki `fetch()` helper'ından geçer.**
  Rate limit, retry, blacklist, robots ve UA orada tek yerde uygulanır.
  Worker içinde doğrudan `httpx.get` çağırma.
- Kaldırma talepleri 7 gün içinde işlenir (`manage.py hide-store`).

## Kod kuralları

- Her iki tarafta da **ham SQL**. ORM, query builder, Prisma, Alembic yok.
- Migration = `/db/NNN_isim.sql` + `python db/migrate.py`.
- Fiyatlar her yerde **integer cent**. Float ile para tutulmaz.
- SQL'de string birleştirme yok — her yerde parametreli sorgu.
- Sayfa render'ları kendi API'sini HTTP ile çağırmaz; `web/lib/queries.ts`
  içindeki fonksiyonu doğrudan import eder.
