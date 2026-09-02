# Bitiş Raporu

## Canlı adresler

| Ne | Nerede |
|---|---|
| Site | https://shopify-store-directory.vercel.app |
| API | `/api/stats` · `/api/stores` · `/api/products` · `/api/feed` · `/api/health` |
| Repo | https://github.com/hykleas/shopify-store-directory (private) |
| Veritabanı | Neon (Vercel Storage üzerinden, `storedir-db`, Frankfurt, free plan) |
| Vercel projesi | `shopify-store-directory` (root directory: `web`) |

## Fazlar

| Faz | Durum | Not |
|---|---|---|
| 0 İskelet | ✅ | monorepo, 8 migration + runner, docker-compose, Next.js 16 |
| 1 Keşif | ✅ | **certstream yerine doğrudan CT log okuma** — public certstream sunucusu ölü |
| 2 Katalog ingest | ✅ | products.json sayfalama, sitemap fallback, crawl priority |
| 3 Kategorizasyon | ⚠️ kapsam daraltıldı | **Yalnızca 27 kategori; niş ataması kapalı** — aşağıya bak |
| 4 Katalog aktivitesi | ✅ | günlük rollup çalıştı; ürün eşleştirme ilk tam turunu VPS'te tamamlayacak |
| 5 API | ✅ | 8 endpoint, zod doğrulama, 120/dk rate limit, hepsi parametreli SQL |
| 6 Frontend | ✅ | 7 sayfa, koyu tema, URL'e senkron filtreler, finder, en/tr |
| 7 Operasyon | ✅ | heartbeat, APScheduler, run_all, manage.py |
| 8 Deploy | ⚠️ | web canlı; CI dosyası push edilemedi (aşağıya bak) |

## Ölçülen durum (bu makinede ~1 saatlik koşu)

```
discovery_queue   14.971 bekleyen
stores                71   (elle doğrulanan 6/6 gerçek Shopify)
products           7.458
variants          64.719
variant_history   64.719
store_metrics         71
```

Canlı doğrulama: tüm sayfalar 200, `/api/health` `ok:true`, filtre
kombinasyonları (`country`, `currency`, `category`, `min_products`,
`launched_after`, `q`, `sort`) doğru sonuç dönüyor.

## Faz 3 — neden niş yok

Spec 225 niş ve "50 üründen 40'ı doğru" istiyordu. Ölçülen doğruluk %46'da kaldı.
Kök neden dört ayrı açıdan doğrulandı:

- Model İngilizce başlıklarda iyi: `Hair Care` → Haircare (0.95), `Oversized
  Cotton Crewneck Tee` → T-Shirts & Tops (1.00).
- İngilizce olmayanda çöküyor: `Relojes` → Planners & Calendars, `Kopfhörer`
  → Haircare, `Scaune de Masă` → Spiritual Decor.
- Külliyatın %30'u İngilizce değil (RO %21, ES, FR, CH…).
- Denenen ve İngilizce tarafı düzeltip diğerini düzeltmeyenler: model değişimi
  (MiniLM → çok dilli → E5), havuzlama (ortalama → en yakın örnek), metin
  kurulumu (product_type öne, ölçü/model kodu temizliği), ağırlık taraması.
- Metni İngilizce'ye çevirmek düzeltiyor (1/10 → 6/10) ama ~300MB'lık NMT
  modeli tek-VPS bütçesine yük.

**Karar (kullanıcı):** niş bırakıldı, 27 kategori atanıyor. Kategori mağaza
bağlamından geliyor (ad + açıklama + en sık `product_type` + örnek başlıklar
oylaması) — etiketli 14 mağazada 11 doğru. `products.niche` kolonu ve API
parametresi duruyor, hep NULL; niş verisi olmadığı sürece UI'da filtre
gösterilmiyor, ileride açılırsa kendiliğinden geri gelir.

Bilinen sınır: İngilizce olmayan mağazalarda kategori de yanılabiliyor
(örn. `emrababy.ro` → "Outdoor & Adventure", doğrusu "Baby & Kids").

## Senin çalıştırman gerekenler

### 1. CI dosyasını push et (30 saniye)

`gh` token'ında `workflow` scope'u yok, `.github/workflows/ci.yml` taşıyan
commit reddedildi. Kendi terminalinde:

```bash
gh auth refresh -h github.com -s workflow
cd C:\Users\Lenovo\shopify-directory
git push
```

### 2. Crawler'ı VPS'e kur

Adım adım: [`crawler/DEPLOY.md`](crawler/DEPLOY.md). Özet:

```bash
curl -fsSL https://get.docker.com | sh
git clone https://github.com/hykleas/shopify-store-directory.git /opt/storedir
cd /opt/storedir && cp .env.example .env && nano .env
docker compose up -d --build
docker compose exec crawler python manage.py stats
```

`.env` içine gidecek `DATABASE_URL` — Vercel panelinde
Storage → `storedir-db` → `DATABASE_URL_UNPOOLED` (crawler için pooler'sız olan).

Ya da yerelden:

```bash
cd C:\Users\Lenovo\shopify-directory\web && vercel env pull
```

### 3. Kaldırma taleplerini haftada bir kontrol et

```bash
docker compose exec crawler python manage.py removals
docker compose exec crawler python manage.py resolve-removal <id>
```

Spec gereği talepler 7 gün içinde işlenmeli.

## TODO'da kalanlar

Ayrıntı: [`TODO.md`](TODO.md)

- CI workflow push'u (yukarıda)
- Faz 1–4 kabul kriterlerinin uzun koşuda ölçümü (1 saatlik koşuda mağaza
  sayısı 71'de kaldı, kriter >50 — geçti; ürün eşleştirme tam turu VPS'te)
- `EXPLAIN ANALYZE` ile 1M satırda `/stores` < 300ms doğrulaması
- Lighthouse ölçümü

## Kesin kural denetimi

Şemada satış/ciro/kazanç kolonu yok. `cart/add.js` veya stok adedi sızdıran
hiçbir uca gidilmiyor — yalnızca `products.json`'daki `available` boolean'ı.
Pricing sayfası, plan, paywall, kayıt duvarı yok. Mağaza sahibi kişisel verisi
toplanmıyor (`meta.json`'daki `shop_owner` bilinçli olarak okunmuyor).
Görseller Shopify CDN'inden hotlink, kopyalanmıyor. `robots.txt` Disallow ise
mağaza `is_hidden`. Bot User-Agent'ta kimliğini açıkça veriyor.
