# Crawler VPS kurulumu

Hetzner CX22 / Contabo VPS S yeter. Ubuntu 24.04 varsayılıyor.
Aşağıdaki blokları sırayla kopyala-yapıştır.

## 1. Docker

```bash
curl -fsSL https://get.docker.com | sh
systemctl enable --now docker
docker --version && docker compose version
```

## 2. Repo

```bash
apt-get update && apt-get install -y git
git clone https://github.com/<KULLANICI>/<REPO>.git /opt/storedir
cd /opt/storedir
```

## 3. .env

```bash
cp .env.example .env
nano .env
```

Doldurulacaklar:

```
DATABASE_URL=postgresql://<user>:<pass>@<neon-host>/<db>?sslmode=require
NEXT_PUBLIC_SITE_URL=https://<canli-alan-adin>
BOT_USER_AGENT=StoreDirectoryBot/1.0 (+https://<canli-alan-adin>/bot)
```

Neon kullanıyorsan lokal postgres'e gerek yok:

```bash
docker compose up -d --build migrate crawler
```

Lokal postgres istiyorsan `DATABASE_URL` satırını `.env`'den sil ve:

```bash
docker compose up -d --build
```

## 4. Migration + başlatma

`migrate` servisi `crawler`'dan önce otomatik koşar. Elle tetiklemek için:

```bash
docker compose run --rm migrate
```

Başlat:

```bash
docker compose up -d --build
docker compose ps
```

## 5. Log takibi

```bash
docker compose logs -f crawler
docker compose logs --tail=200 crawler | grep -E "kuyruk|nabiz|blacklist"
```

İlk açılışta embedding modeli (~90MB) indirilir; `model hazir` satırını bekle.

## 6. Doğrulama

```bash
docker compose exec crawler python manage.py stats
```

İlk saatte beklenen: `discovery_queue` bekleyen > 5.000, `stores` > 50.
Bir saat sonra `products` artmaya başlar.

```bash
curl -s https://<canli-alan-adin>/api/health | head -c 400
```

## 7. Günlük bakım

Zamanlayıcı konteynerin içinde (UTC):

| Saat | İş |
|---|---|
| 03:10 | `daily_rollup` — katalog aktivitesi özeti |
| 04:00 | `product_spread` — görsel hash, eşleştirme, yayılım |
| 05:00 | `prune` — 30 günden eski `not_shopify` kayıtlarını sil |

Elle çalıştırmak:

```bash
docker compose exec crawler python -m activity.daily_rollup
docker compose exec crawler python -m activity.product_spread
```

## 8. Kaldırma talepleri (7 gün içinde işlenmeli)

```bash
docker compose exec crawler python manage.py removals
docker compose exec crawler python manage.py resolve-removal <id>
```

## 9. Güncelleme

```bash
cd /opt/storedir
git pull
docker compose up -d --build
docker compose run --rm migrate
```

## 10. Yük ayarı

Kaynak yetmiyorsa `.env`'e ekle:

```
GLOBAL_CONCURRENCY=10
DETECTOR_CONCURRENCY=10
INGEST_CONCURRENCY=4
EMBED_BATCH=128
ENABLE_EMBED=false        # kategorizasyonu geçici kapat
```

Sonra `docker compose up -d`.

## Notlar

- `restart: unless-stopped` açık; reboot sonrası kendi başına kalkar.
- Log rotasyonu docker json-file ile: `max-size 50m`, `max-file 3`.
- Neon otomatik yedekliyor; ek yedek script'i yok.
- Rate limit ve blacklist bellekte tutulur, restart sonrası sıfırlanır — bu
  kasıtlı: 24 saatlik blacklist yeniden öğrenilir.
