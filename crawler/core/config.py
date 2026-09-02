"""Ortam değişkenlerinden okunan tek merkezî yapılandırma."""
from __future__ import annotations

import os
import pathlib

from dotenv import load_dotenv

ROOT = pathlib.Path(__file__).resolve().parent.parent
load_dotenv(ROOT.parent / ".env", override=False)
load_dotenv(ROOT / ".env", override=False)


def _int(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, "") or default)
    except ValueError:
        return default


def _bool(name: str, default: bool) -> bool:
    raw = (os.environ.get(name) or "").strip().lower()
    if not raw:
        return default
    return raw in {"1", "true", "yes", "on"}


DATABASE_URL: str = os.environ.get("DATABASE_URL", "")
SITE_URL: str = os.environ.get("NEXT_PUBLIC_SITE_URL", "http://localhost:3000").rstrip("/")

# Kimliği gizlemiyoruz — bot açıkça kendini tanıtır ve iletişim sayfasına link verir.
USER_AGENT: str = os.environ.get(
    "BOT_USER_AGENT", f"StoreDirectoryBot/1.0 (+{SITE_URL}/bot)"
)

# --- kibarlık ayarları -------------------------------------------------------
# Aynı host'a saniyede en fazla 1 istek. Bunu artırma.
HOST_MIN_INTERVAL_S: float = float(os.environ.get("HOST_MIN_INTERVAL_S", "1.0"))
# 429/503 sonrası host kaç saniye blackliste alınsın.
BLACKLIST_TTL_S: int = _int("BLACKLIST_TTL_S", 24 * 3600)
GLOBAL_CONCURRENCY: int = _int("GLOBAL_CONCURRENCY", 40)
# Paylasimli CDN'ler magaza sunucusu degil; 1 istek/sn kurali onlar icin
# gorsel hash'lemeyi imkansiz kilardi (bkz. DECISIONS.md #13).
CDN_HOSTS: frozenset[str] = frozenset(
    {"cdn.shopify.com", "cdn.shopifycdn.net", "cdn11.bigcommerce.com"}
)
CDN_MIN_INTERVAL_S: float = float(os.environ.get("CDN_MIN_INTERVAL_S", "0.25"))
HTTP_TIMEOUT_S: float = float(os.environ.get("HTTP_TIMEOUT_S", "10"))
HTTP_RETRIES: int = _int("HTTP_RETRIES", 3)

# --- worker ayarları ---------------------------------------------------------
DETECTOR_BATCH: int = _int("DETECTOR_BATCH", 200)
DETECTOR_CONCURRENCY: int = _int("DETECTOR_CONCURRENCY", 40)
INGEST_BATCH: int = _int("INGEST_BATCH", 25)
INGEST_CONCURRENCY: int = _int("INGEST_CONCURRENCY", 8)
INGEST_MAX_PAGES: int = _int("INGEST_MAX_PAGES", 20)
EMBED_BATCH: int = _int("EMBED_BATCH", 256)
# Cok dilli: magazalar dunya genelinde, urun basliklari Ingilizce degil.
# all-MiniLM-L6-v2 Romence/Turkce basliklari rastgele nislere atiyordu.
# Ayni 384 boyut -> sema degismiyor.
EMBED_MODEL: str = os.environ.get(
    "EMBED_MODEL", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)
NICHE_MIN_SCORE: float = float(os.environ.get("NICHE_MIN_SCORE", "0.35"))
# Magaza baglamindan tahmin edilen kategoriye ne kadar guvenilirse dayatilir.
STORE_CONTEXT_MIN_SCORE: float = float(os.environ.get("STORE_CONTEXT_MIN_SCORE", "0.14"))
PHASH_MAX_DISTANCE: int = _int("PHASH_MAX_DISTANCE", 6)

# CT loglarini dogrudan okuma (birincil kesif kaynagi).
CT_LOG_LIST_URL: str = os.environ.get(
    "CT_LOG_LIST_URL", "https://www.gstatic.com/ct/log_list/v3/log_list.json"
)
CT_BATCH: int = _int("CT_BATCH", 256)      # get-entries basina kayit
CT_MAX_LOGS: int = _int("CT_MAX_LOGS", 9)  # es zamanli takip edilen log sayisi

# certstream: public sunucu (calidog) olu, varsayilan kapali. Kendi certstream
# sunucunu calistiriyorsan CERTSTREAM_URL'i verip ENABLE_CERTSTREAM=true yap.
CERTSTREAM_URL: str = os.environ.get("CERTSTREAM_URL", "wss://certstream.calidog.io/")
CERTSTREAM_BATCH: int = _int("CERTSTREAM_BATCH", 500)

# Hangi worker'lar run_all içinde çalışsın (VPS'te bazılarını kapatmak için).
ENABLE_CT_POLLER: bool = _bool("ENABLE_CT_POLLER", True)
ENABLE_CERTSTREAM: bool = _bool("ENABLE_CERTSTREAM", False)
ENABLE_DETECTOR: bool = _bool("ENABLE_DETECTOR", True)
ENABLE_INGEST: bool = _bool("ENABLE_INGEST", True)
ENABLE_EMBED: bool = _bool("ENABLE_EMBED", True)
ENABLE_STORE_CONTEXT: bool = _bool("ENABLE_STORE_CONTEXT", True)
ENABLE_SCHEDULER: bool = _bool("ENABLE_SCHEDULER", True)

LOG_LEVEL: str = os.environ.get("LOG_LEVEL", "INFO").upper()
