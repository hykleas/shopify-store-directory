# TODO

## Senin yapman gereken

- [ ] **CI workflow push'u** — `gh` token'inda `workflow` scope'u yok,
      `.github/workflows/ci.yml` tasiyan commit reddedildi.
      `gh auth refresh -h github.com -s workflow` sonra `git push`.
- [ ] **Crawler VPS kurulumu** — `crawler/DEPLOY.md`.
- [ ] Kaldirma taleplerini haftada bir kontrol et (`manage.py removals`).

## Uzun kosuda olculecek kabul kriterleri

Bu makinede ~1 saatlik kosu yapildi; asagidakiler VPS'te surekli kosuda
dogrulanmali.

- [ ] Faz 2 — 500 magaza katalogu / >20.000 urun (su an 71 magaza, 7.458 urun).
- [ ] Faz 4 — 100 magaza icin 7 gunluk `store_metrics` (su an 1 gun, 71 magaza).
      Urun eslestirme (phash) ilk tam turunu VPS'te tamamlayacak.
- [ ] Faz 5 — `EXPLAIN ANALYZE` ile 1M satirda `/stores` < 300ms.
- [ ] Faz 6 — Lighthouse performance > 85.

## Bilincli olarak yapilmayanlar

- **Nis atamasi** (DECISIONS #26). Yalnizca 27 kategori ataniyor.
  Ingilizce olmayan magazalarda kategori de yanilabiliyor
  (`emrababy.ro` -> "Outdoor & Adventure", dogrusu "Baby & Kids").
  Acmak icin gereken: urun metnini Ingilizce'ye ceviren bir NMT adimi
  (~300MB model, VPS'te ek RAM/CPU).
- **certstream** worker'i duruyor ama kapali (public sunucu olu, DECISIONS #21).

## Ortam notlari

- Bu gelistirme makinesinde Docker ve `psql` kurulu degil; `docker-compose.yml`
  ve `crawler/Dockerfile` yazildi ama lokal olarak calistirilamadi.
