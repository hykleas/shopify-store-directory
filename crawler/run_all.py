"""Tum crawler worker'larini tek surecte asyncio task'i olarak calistirir.

Neden tek surec: embedding modeli bellekte tek kez duruyor ve rate limit /
blacklist durumu tum worker'lar arasinda paylasiliyor. Her worker ayrica
tek basina da calistirilabilir (python -m discovery.shopify_detector gibi).

Hangi worker'in acik olacagi .env'den kontrol edilir (ENABLE_* degiskenleri).
"""
from __future__ import annotations

import asyncio
import contextlib
import signal

import heartbeat
import scheduler
from categorize.assign_worker import AssignWorker
from categorize.embed_worker import EmbedWorker
from categorize.store_context import StoreContextWorker
from core import config, db, http
from core.log import get
from discovery.certstream_listener import CertstreamListener
from discovery.ct_log_poller import CtLogPoller
from discovery.shopify_detector import Detector
from ingest.catalog_worker import CatalogWorker

log = get("run_all")


def _tasks() -> dict[str, object]:
    jobs: dict[str, object] = {}
    if config.ENABLE_CT_POLLER:
        jobs["ct_poller"] = CtLogPoller().run_forever
    if config.ENABLE_CERTSTREAM:
        jobs["certstream"] = CertstreamListener().run
    if config.ENABLE_DETECTOR:
        jobs["detector"] = Detector().run_forever
    if config.ENABLE_INGEST:
        jobs["ingest"] = CatalogWorker().run_forever
    if config.ENABLE_EMBED:
        jobs["embed"] = EmbedWorker().run_forever
        # Magaza baglami atamadan ONCE hazir olmali; ikisi de kendi dongusunde
        # bekleyerek ilerliyor, sirayi veri belirliyor.
        if config.ENABLE_STORE_CONTEXT:
            jobs["store_context"] = StoreContextWorker().run_forever
        jobs["assign"] = AssignWorker().run_forever
    if config.ENABLE_SCHEDULER:
        jobs["scheduler"] = scheduler.run_forever
    jobs["heartbeat"] = heartbeat.run_forever
    return jobs


async def _supervise(name: str, factory) -> None:
    """Bir worker cokerse tum sureci dusurme; bekleyip yeniden basla."""
    delay = 5
    while True:
        try:
            await factory()
            log.warning("%s beklenmedik sekilde bitti, yeniden baslatiliyor", name)
        except asyncio.CancelledError:
            log.info("%s durduruldu", name)
            raise
        except Exception as exc:  # noqa: BLE001
            log.error("%s coktu: %s", name, exc)
        await asyncio.sleep(delay)
        delay = min(delay * 2, 300)


async def main() -> None:
    if not config.DATABASE_URL:
        raise SystemExit("DATABASE_URL tanimli degil.")

    jobs = _tasks()
    log.info("baslatiliyor: %s", ", ".join(jobs))

    tasks = [asyncio.create_task(_supervise(name, fn), name=name) for name, fn in jobs.items()]

    stop = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        with contextlib.suppress(NotImplementedError, AttributeError):
            loop.add_signal_handler(sig, stop.set)

    try:
        await stop.wait()
    except (KeyboardInterrupt, asyncio.CancelledError):
        pass
    finally:
        log.info("kapaniyor…")
        for t in tasks:
            t.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        await http.aclose()
        await db.close()


if __name__ == "__main__":
    with contextlib.suppress(KeyboardInterrupt):
        asyncio.run(main())
