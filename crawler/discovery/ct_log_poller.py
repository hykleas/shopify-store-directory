"""Certificate Transparency loglarini dogrudan okuyup discovery_queue'yu besler.

Neden certstream degil: `wss://certstream.calidog.io` public sunucusu baglantiyi
kabul ediyor ama hicbir mesaj gondermiyor (olu servis). CT loglarinin kendisi
RFC 6962 HTTP API'siyle herkese acik, bu yuzden dogrudan onlari okuyoruz -
certstream'in kendi ic isleyisi de budur.

Akis:
  1. Google'in bilinen-log listesinden (log_list.json) su an "usable" olan ve
     bugunu kapsayan loglari sec.
  2. Her log icin `get-sth` ile agac boyutunu ogren, `ct_log_state`'te tuttugumuz
     son indeksten ileriye `get-entries` ile ilerle.
  3. Her kaydin X.509 sertifikasindan SAN dNSName'leri cikar, domain_filter'dan
     gecir, `discovery_queue`'ya batch yaz.

Tek basina:  python -m discovery.ct_log_poller
"""
from __future__ import annotations

import asyncio
import base64
import contextlib
import datetime as dt
import struct
import time

from cryptography import x509

from core import config, db, http
from core.log import get
from discovery.domain_filter import extract

log = get("discovery.ctlog")

INSERT_SQL = """
INSERT INTO discovery_queue (domain, source)
SELECT unnest($1::text[]), $2
ON CONFLICT (domain) DO NOTHING
"""

LOAD_STATE_SQL = "SELECT log_url, next_index FROM ct_log_state"

SAVE_STATE_SQL = """
INSERT INTO ct_log_state (log_url, next_index, tree_size, updated_at)
VALUES ($1, $2, $3, now())
ON CONFLICT (log_url) DO UPDATE SET
  next_index = EXCLUDED.next_index,
  tree_size  = EXCLUDED.tree_size,
  updated_at = now()
"""

# --- RFC 6962 yapilari ------------------------------------------------------
ENTRY_X509 = 0
ENTRY_PRECERT = 1


def _u24(buf: bytes, off: int) -> tuple[int, int]:
    """3 baytlik uzunluk oku -> (uzunluk, yeni_offset)."""
    return (buf[off] << 16) | (buf[off + 1] << 8) | buf[off + 2], off + 3


def certificate_der(leaf_input: bytes, extra_data: bytes) -> bytes | None:
    """MerkleTreeLeaf + extra_data'dan tam X.509 DER'i cikarir.

    x509_entry'de sertifika leaf_input icindedir. precert_entry'de leaf_input
    yalnizca TBSCertificate tasir (tek basina parse edilemez), tam on-sertifika
    extra_data'nin basindadir.
    """
    if len(leaf_input) < 12:
        return None
    version, leaf_type = leaf_input[0], leaf_input[1]
    if version != 0 or leaf_type != 0:
        return None
    entry_type = struct.unpack(">H", leaf_input[10:12])[0]

    if entry_type == ENTRY_X509:
        length, off = _u24(leaf_input, 12)
        der = leaf_input[off : off + length]
        return der if len(der) == length else None

    if entry_type == ENTRY_PRECERT:
        if len(extra_data) < 3:
            return None
        length, off = _u24(extra_data, 0)
        der = extra_data[off : off + length]
        return der if len(der) == length else None

    return None


def domains_from_der(der: bytes) -> list[str]:
    """Sertifikadan SAN dNSName'leri (yoksa CN) dondurur."""
    try:
        cert = x509.load_der_x509_certificate(der)
    except Exception:  # noqa: BLE001 - bozuk kayitlar normaldir
        return []

    names: list[str] = []
    try:
        san = cert.extensions.get_extension_for_class(x509.SubjectAlternativeName)
        names.extend(san.value.get_values_for_type(x509.DNSName))
    except x509.ExtensionNotFound:
        pass
    except Exception:  # noqa: BLE001
        return []

    if not names:
        with contextlib.suppress(Exception):
            names.extend(
                a.value for a in cert.subject.get_attributes_for_oid(x509.oid.NameOID.COMMON_NAME)
                if isinstance(a.value, str)
            )
    return names


def parse_entries(entries: list[dict]) -> set[str]:
    """CPU-yogun kisim: thread'e atilarak cagrilir."""
    out: set[str] = set()
    for e in entries:
        try:
            leaf = base64.b64decode(e.get("leaf_input") or "")
            extra = base64.b64decode(e.get("extra_data") or "")
        except Exception:  # noqa: BLE001
            continue
        der = certificate_der(leaf, extra)
        if der:
            out |= extract(domains_from_der(der))
    return out


# --- log kesfi --------------------------------------------------------------
async def usable_logs() -> list[str]:
    """Su an yazilabilir ve bugunu kapsayan CT loglarinin base URL'leri."""
    r = await http.fetch(config.CT_LOG_LIST_URL, retries=2, timeout=30)
    if r is None or not r.ok:
        log.error("CT log listesi alinamadi")
        return []
    data = r.json()
    if not isinstance(data, dict):
        return []

    now = dt.datetime.now(dt.UTC)
    urls: list[str] = []
    for operator in data.get("operators") or []:
        for entry in operator.get("logs") or []:
            if "usable" not in (entry.get("state") or {}):
                continue
            interval = entry.get("temporal_interval")
            if interval:
                try:
                    start = dt.datetime.fromisoformat(interval["start_inclusive"].replace("Z", "+00:00"))
                    end = dt.datetime.fromisoformat(interval["end_exclusive"].replace("Z", "+00:00"))
                except (KeyError, ValueError):
                    continue
                if not (start <= now < end):
                    continue
            url = (entry.get("url") or "").rstrip("/")
            if url:
                urls.append(url)
    return urls[: config.CT_MAX_LOGS]


class CtLogPoller:
    def __init__(self) -> None:
        self.state: dict[str, int] = {}
        self.certs = 0
        self.queued = 0
        self._last_report = time.monotonic()

    async def load_state(self) -> None:
        for row in await db.fetch(LOAD_STATE_SQL):
            self.state[row["log_url"]] = row["next_index"]

    async def tree_size(self, base: str) -> int | None:
        r = await http.fetch(base + "/ct/v1/get-sth", retries=2, timeout=20)
        if r is None or not r.ok:
            return None
        data = r.json()
        size = (data or {}).get("tree_size")
        return int(size) if isinstance(size, int) else None

    async def poll(self, base: str) -> int:
        size = await self.tree_size(base)
        if size is None:
            return 0

        start = self.state.get(base)
        if start is None:
            # Ilk gorusme: gecmisi taramiyoruz, agacin ucundan basliyoruz.
            start = max(0, size - config.CT_BATCH)
        if start >= size:
            return 0

        end = min(start + config.CT_BATCH - 1, size - 1)
        r = await http.fetch(
            base + f"/ct/v1/get-entries?start={start}&end={end}", retries=2, timeout=40
        )
        if r is None or not r.ok:
            return 0
        data = r.json()
        entries = (data or {}).get("entries")
        if not isinstance(entries, list) or not entries:
            return 0

        # Log istenenden az kayit dondurebilir; ilerlemeyi gercek sayiya gore yap.
        domains = await asyncio.to_thread(parse_entries, entries)
        self.certs += len(entries)
        self.state[base] = start + len(entries)
        await db.execute(SAVE_STATE_SQL, base, self.state[base], size)

        if domains:
            await db.execute(INSERT_SQL, sorted(domains), "ct_log")
            self.queued += len(domains)
        return len(entries)

    async def report(self) -> None:
        if time.monotonic() - self._last_report < 60:
            return
        self._last_report = time.monotonic()
        pending = await db.fetchval(
            "SELECT count(*) FROM discovery_queue WHERE status = 'pending'"
        )
        log.info(
            "sertifika=%d kuyruga_yazilan=%d bekleyen=%s log=%d",
            self.certs,
            self.queued,
            pending,
            len(self.state),
        )

    async def run_forever(self) -> None:
        await self.load_state()
        logs = await usable_logs()
        if not logs:
            log.error("kullanilabilir CT log bulunamadi, 5 dk sonra tekrar denenecek")
            await asyncio.sleep(300)
            return
        log.info("CT poller basladi: %d log, batch=%d", len(logs), config.CT_BATCH)

        while True:
            # Loglar farkli host'larda; fetch() zaten host basina 1 istek/sn uyguluyor.
            results = await asyncio.gather(
                *(self._safe_poll(base) for base in logs), return_exceptions=False
            )
            await self.report()
            if not any(results):
                await asyncio.sleep(10)

    async def _safe_poll(self, base: str) -> int:
        try:
            return await self.poll(base)
        except asyncio.CancelledError:
            raise
        except Exception as exc:  # noqa: BLE001
            log.warning("%s pollanamadi: %s", base, exc)
            return 0


async def main() -> None:
    poller = CtLogPoller()
    try:
        while True:
            await poller.run_forever()
    finally:
        await http.aclose()
        await db.close()


if __name__ == "__main__":
    with contextlib.suppress(KeyboardInterrupt):
        asyncio.run(main())
