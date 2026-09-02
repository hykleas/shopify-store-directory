# Shopify Store & Product Directory

Yeni açılan Shopify mağazalarını otomatik keşfeden, kataloglarını çeken, ürünleri
kategorize eden ve **katalog aktivitesini** izleyen ücretsiz araştırma platformu.

Kayıt olmadan gezilebilir. Pricing sayfası, plan, paywall veya kota yok.

> **Kesin kural:** Mağaza cirosu, kazancı, satış adedi veya bunların herhangi bir
> tahmini hiçbir yerde hesaplanmaz, saklanmaz, gösterilmez. Stok adedi sızdıran
> uçlara (`cart/add.js` vb.) hiç gidilmez. Ayrıntı: [`CLAUDE.md`](CLAUDE.md).

---

## Mimari

```
                    ┌──────────────────────┐
   CT logs  ───────▶│  ct_log_poller       │──┐
   (RFC 6962 HTTP)  └──────────────────────┘  │
                                              ▼
                                     ┌──────────────────┐
                                     │ discovery_queue  │
                                     └──────────────────┘
                                              │
                    ┌──────────────────────┐  │
                    │  shopify_detector    │◀─┘   DNS → header → meta.json
                    └──────────────────────┘
                                              │
                                              ▼
   store           ┌──────────────────────┐  ┌──────────┐
   /products.json ▶│  catalog_worker      │─▶│  stores  │
                   └──────────────────────┘  │ products │
                                             │ variants │
                    ┌──────────────────────┐ └──────────┘
                    │  embed + assign      │──────┤  pgvector, 27 kategori
                    └──────────────────────┘      │
                    ┌──────────────────────┐      │
                    │  daily_rollup        │──────┤  store_metrics
                    │  product_spread      │──────┤  product_matches
                    └──────────────────────┘      │
                                                  ▼
                                          ┌────────────────┐
                                          │ Supabase (PG)  │
                                          └────────────────┘
                                                  │ okuma
                                                  ▼
                                   ┌───────────────────────────┐
                                   │ Next.js (Vercel)          │
                                   │ /stores /products /finder │
                                   │ /api/* route handlers     │
                                   └───────────────────────────┘
```

Crawler tek bir VPS'te Docker Compose ile döner ve Supabase'e **yazar**.
Web Vercel'de çalışır ve aynı veritabanından yalnızca **okur**.

| Katman | Seçim |
|---|---|
| DB | Supabase (Postgres) + `pgvector` + `pg_trgm` |
| Web + API | Next.js 16 (App Router), TypeScript, Tailwind v4 |
| DB erişimi (web) | `postgres` (postgres.js), ham SQL — ORM yok |
| Crawler | Python 3.12, `httpx`, `asyncio`, `asyncpg` |
| Keşif | CT logları doğrudan (RFC 6962) — `certstream` public sunucusu ölü, varsayılan kapalı |
| Kuyruk | Postgres tablosu (`discovery_queue`) — Redis yok |
| Kategorizasyon | `sentence-transformers` / `paraphrase-multilingual-MiniLM-L12-v2`, CPU — yalnızca kategori |

```
/crawler   Python worker'ları (VPS)
/web       Next.js frontend + API (Vercel)
/db        numaralı migration .sql dosyaları + migrate.py
```

---

## Lokal kurulum

### 1. Ortam değişkenleri

```bash
cp .env.example .env
```

| Değişken | Açıklama |
|---|---|
| `DATABASE_URL` | Postgres bağlantısı, aşağıdaki tabloya bak |
| `NEXT_PUBLIC_SITE_URL` | Sitenin kanonik adresi (sitemap, metadata, bot iletişim linki) |
| `BOT_USER_AGENT` | Crawler kimliği. İçinde `/bot` sayfasına giden bir URL olmalı |

Opsiyonel ayarlar (`crawler/core/config.py` içinde varsayılanları var):
`HOST_MIN_INTERVAL_S`, `CDN_MIN_INTERVAL_S`, `GLOBAL_CONCURRENCY`,
`DETECTOR_BATCH`, `INGEST_BATCH`, `EMBED_BATCH`, `NICHE_MIN_SCORE`,
`PHASH_MAX_DISTANCE`, `CT_BATCH`, `CT_MAX_LOGS`, `ENABLE_CT_POLLER`,
`ENABLE_CERTSTREAM`, `ENABLE_DETECTOR`, `ENABLE_INGEST`, `ENABLE_EMBED`,
`ENABLE_SCHEDULER`.

**Hangi Supabase bağlantı dizesi nerede?** Supabase panelinde
*Project → Connect* altında üç seçenek var:

| Nerede | Seçenek | Port | Neden |
|---|---|---|---|
| Vercel (web) | Transaction pooler | 6543 | Serverless, kısa ömürlü bağlantı |
| VPS (crawler) | Session pooler | 5432 | Uzun ömürlü bağlantı, IPv4 |
| Migration (`db/migrate.py`) | Session pooler | 5432 | `CREATE EXTENSION` gerekiyor |

Direct connection (`db.<ref>.supabase.co:5432`) yeni projelerde IPv6-only;
VPS'in IPv4 ise çalışmaz, o yüzden pooler kullan.

### 2. Veritabanı + crawler (Docker)

```bash
docker compose up -d          # postgres + migration + crawler
docker compose logs -f crawler
```

Migration'ı elle çalıştırmak için:

```bash
pip install "psycopg[binary]"
DATABASE_URL=... python db/migrate.py            # bekleyenleri uygula
DATABASE_URL=... python db/migrate.py --status   # durum listesi
```

### 3. Web

```bash
cd web
npm install
npm run dev        # http://localhost:3000
```

---

## Crawler'ı Docker'sız çalıştırma

```bash
cd crawler
pip install -r requirements.txt
export PYTHONPATH=$PWD

python -m run_all                      # hepsi tek süreçte
python -m discovery.ct_log_poller         # tek tek de çalışır
python -m discovery.shopify_detector
python -m ingest.catalog_worker
python -m categorize.embed_worker
python -m categorize.assign_worker
python -m activity.daily_rollup
python -m activity.product_spread
```

## Operasyon komutları

```bash
cd crawler
python manage.py stats                  # kuyruk / mağaza / ürün sayıları + nabız
python manage.py removals               # bekleyen kaldırma talepleri
python manage.py resolve-removal 12     # talebi işle, mağazayı gizle
python manage.py hide-store example.com
python manage.py unhide-store example.com
python manage.py recrawl example.com
python manage.py seed domains.txt       # elle domain kuyruğa ekle
python manage.py rebuild-niches         # taksonomi değiştiyse
```

Sağlık: `GET /api/health` crawler nabzını okur; 3 saattir yazılmadıysa 503 döner.

---

## Migration ekleme

`db/NNN_isim.sql` oluştur (numara artan), sonra `python db/migrate.py`.
Uygulanmış bir dosyayı değiştirme — runner uyarır; yeni numara aç.

## Deploy

- **Web** → Vercel. Root directory `web`. Env: `DATABASE_URL` (transaction pooler,
  port 6543), `NEXT_PUBLIC_SITE_URL`, `BOT_USER_AGENT`.
- **Crawler** → tek VPS. Adım adım: [`crawler/DEPLOY.md`](crawler/DEPLOY.md).

## Yasal / etik

- Yalnızca herkese açık uçlardan veri çekilir. Login, captcha veya IP bloğu aşılmaz.
- Kişisel veri (mağaza sahibi adı, e-posta, telefon) toplanmaz ve saklanmaz.
- `robots.txt`'e uyulur; Disallow ise mağaza `is_hidden` işaretlenir.
- Kaldırma talepleri 7 gün içinde işlenir (`/bot` sayfasındaki form).
- Ürün görselleri kopyalanmaz; hotlink edilir veya sadece perceptual hash tutulur.
