# TODO

Atlanan veya elle yapılması gereken işler.

## Kimlik bilgisi bekleyenler

- [ ] **GitHub Actions workflow push'u** — `gh` token'ında `workflow` scope'u yok,
      `.github/workflows/ci.yml` taşıyan commit reddedildi. Repo ve kodun geri
      kalanı GitHub'da. Çözüm: `gh auth refresh -s workflow` sonra `git push`.
- [ ] **Neon `DATABASE_URL`** — migration'lar (`db/001`–`004`) henüz gerçek bir
      veritabanına uygulanmadı.
- [ ] **`vercel login`** — proje bağlanmadı, env değişkenleri eklenmedi,
      production deploy alınmadı.

## Kimlik bilgisi geldikten sonra doğrulanacak kabul kriterleri

Bunlar canlı DB olmadan test edilemedi:

- [ ] Faz 1 — 1 saat çalıştır: `discovery_queue` > 5.000, `stores` > 50,
      rastgele 10 mağaza elle Shopify doğrulaması.
- [ ] Faz 2 — 500 mağaza katalogu, `products` > 20.000, fiyat/varyant karşılaştırması.
- [ ] Faz 3 — 20.000 ürün kategorize, 50 örnekte ≥40 doğru, `uncategorized` < %15.
      `NICHE_MIN_SCORE` (varsayılan 0.35) bu ölçüme göre ayarlanmalı.
- [ ] Faz 4 — 100 mağaza için 7 günlük `store_metrics`, ürün eşleştirme kontrolü.
- [ ] Faz 5 — `EXPLAIN ANALYZE` ile 1M satırda `/stores` < 300ms doğrulaması.
- [ ] Faz 6 — Lighthouse performance > 85 (canlı URL gerekiyor).

## Ortam notları

- Bu geliştirme makinesinde Docker ve `psql` kurulu değil; `docker-compose.yml`
  ve `crawler/Dockerfile` yazıldı ama lokal olarak çalıştırılamadı. VPS'te
  `crawler/DEPLOY.md` adımları izlenmeli.
- `sentence-transformers` (torch) lokale kurulmadı; Docker imajında CPU-only
  wheel ile kuruluyor. `categorize/*` modülleri import edilmeden derleniyor,
  ilk gerçek çalıştırma VPS'te olacak.
