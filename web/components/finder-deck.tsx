"use client";

import { useLocale, useTranslations } from "next-intl";
import Link from "next/link";
import { useCallback, useEffect, useRef, useState, useSyncExternalStore } from "react";

import { Badge, Button, Card, EmptyState } from "@/components/ui";
import { countryFlag, formatPrice } from "@/lib/format";
import type { FeedPage, ProductSummary } from "@/lib/types";

/**
 * Swipe kartlar. Mobilde dokunmatik surukleme, masaustunde ok tuslari.
 * Kaydedilenler localStorage'da tutulur - hesap yok, sunucuya gitmez.
 */

const STORAGE_KEY = "finder.saved.v1";
const PREFETCH_AT = 4;
const EMPTY: ProductSummary[] = [];

/**
 * Kaydedilenler localStorage'da yasar - React state'i degil, harici bir sistem.
 * useSyncExternalStore ile okunur: sunucuda bos, istemcide gercek liste.
 */
const savedStore = (() => {
  let cache: ProductSummary[] | null = null;
  const listeners = new Set<() => void>();

  function read(): ProductSummary[] {
    try {
      const raw = window.localStorage.getItem(STORAGE_KEY);
      return raw ? (JSON.parse(raw) as ProductSummary[]) : EMPTY;
    } catch {
      return EMPTY;
    }
  }

  return {
    subscribe(cb: () => void) {
      listeners.add(cb);
      return () => listeners.delete(cb);
    },
    get(): ProductSummary[] {
      if (cache === null) cache = read();
      return cache;
    },
    getServer(): ProductSummary[] {
      return EMPTY;
    },
    set(next: ProductSummary[]) {
      cache = next.slice(0, 300);
      try {
        window.localStorage.setItem(STORAGE_KEY, JSON.stringify(cache));
      } catch {
        /* kota dolu olabilir; kaydetmemek kritik degil */
      }
      for (const cb of listeners) cb();
    },
  };
})();

export function FinderDeck({ initial }: { initial: FeedPage }) {
  const t = useTranslations("finder");
  const locale = useLocale();

  const [queue, setQueue] = useState<ProductSummary[]>(initial.items);
  const [cursor, setCursor] = useState<string | null>(initial.next_cursor);
  const [showSaved, setShowSaved] = useState(false);
  const [loading, setLoading] = useState(false);
  const [drag, setDrag] = useState(0);
  const startX = useRef<number | null>(null);

  const saved = useSyncExternalStore(
    savedStore.subscribe,
    savedStore.get,
    savedStore.getServer,
  );

  const fetchMore = useCallback(async () => {
    if (!cursor || loading) return;
    setLoading(true);
    try {
      const res = await fetch(`/api/feed?cursor=${encodeURIComponent(cursor)}&limit=20`);
      if (res.ok) {
        const page = (await res.json()) as FeedPage;
        setQueue((q) => [...q, ...page.items]);
        setCursor(page.next_cursor);
      }
    } catch {
      /* aga bagli; sessizce gec */
    } finally {
      setLoading(false);
    }
  }, [cursor, loading]);

  const advance = useCallback(
    (keep: boolean) => {
      const [head, ...rest] = queue;
      if (!head) return;
      if (keep) {
        savedStore.set([head, ...savedStore.get().filter((s) => s.id !== head.id)]);
      }
      setQueue(rest);
      setDrag(0);
      if (rest.length <= PREFETCH_AT) void fetchMore();
    },
    [queue, fetchMore],
  );

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === "ArrowRight") advance(true);
      else if (e.key === "ArrowLeft") advance(false);
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [advance]);

  const current = queue[0];

  if (!current) {
    return (
      <div className="space-y-4">
        <EmptyState title={loading ? t("loading") : t("empty")} />
        {saved.length > 0 ? <SavedList saved={saved} onClear={() => savedStore.set([])} /> : null}
      </div>
    );
  }

  return (
    <div className="grid gap-6 lg:grid-cols-[minmax(0,420px)_1fr]">
      <div>
        <div
          className="relative touch-pan-y select-none"
          onTouchStart={(e) => {
            startX.current = e.touches[0]!.clientX;
          }}
          onTouchMove={(e) => {
            if (startX.current === null) return;
            setDrag(e.touches[0]!.clientX - startX.current);
          }}
          onTouchEnd={() => {
            if (Math.abs(drag) > 80) advance(drag > 0);
            else setDrag(0);
            startX.current = null;
          }}
        >
          <Card
            className="overflow-hidden"
            style={{
              transform: `translateX(${drag}px) rotate(${drag / 40}deg)`,
              transition: drag === 0 ? "transform 160ms ease-out" : "none",
            }}
          >
            <div className="relative aspect-square bg-surface-2">
              {current.image_url ? (
                // eslint-disable-next-line @next/next/no-img-element
                <img
                  src={current.image_url}
                  alt=""
                  className="h-full w-full object-cover"
                  referrerPolicy="no-referrer"
                />
              ) : null}
              {drag > 40 ? (
                <span className="absolute left-3 top-3 rounded border border-positive px-2 py-1 text-xs font-bold text-positive">
                  {t("save")}
                </span>
              ) : null}
              {drag < -40 ? (
                <span className="absolute right-3 top-3 rounded border border-negative px-2 py-1 text-xs font-bold text-negative">
                  {t("skip")}
                </span>
              ) : null}
            </div>
            <div className="space-y-2 p-4">
              <Link href={`/products/${current.id}`} className="block text-sm hover:underline">
                {current.title}
              </Link>
              <div className="flex items-center gap-2">
                <span className="font-mono text-lg font-semibold tabular-nums">
                  {formatPrice(current.price, current.currency, locale)}
                </span>
                {current.store_count && current.store_count > 1 ? (
                  <Badge variant="accent">{current.store_count}×</Badge>
                ) : null}
              </div>
              <div className="flex items-center gap-1 font-mono text-[11px] text-faint">
                <span aria-hidden>{countryFlag(current.store_country)}</span>
                {current.store_domain}
              </div>
            </div>
          </Card>
        </div>

        <div className="mt-4 flex items-center gap-2">
          <Button variant="outline" className="flex-1" onClick={() => advance(false)}>
            {t("skip")}
          </Button>
          <Button variant="primary" className="flex-1" onClick={() => advance(true)}>
            {t("save")}
          </Button>
        </div>
        <p className="mt-2 text-center font-mono text-[11px] text-faint">
          {t("hintLeft")} · {t("hintRight")}
        </p>
      </div>

      <div>
        <Button variant="ghost" size="sm" onClick={() => setShowSaved((v) => !v)}>
          {showSaved ? t("hideSaved") : t("saved", { count: saved.length })}
        </Button>
        {showSaved ? (
          <div className="mt-3">
            <SavedList saved={saved} onClear={() => savedStore.set([])} />
          </div>
        ) : null}
      </div>
    </div>
  );
}

function SavedList({
  saved,
  onClear,
}: {
  saved: ProductSummary[];
  onClear: () => void;
}) {
  const t = useTranslations("finder");
  const locale = useLocale();

  if (saved.length === 0) return null;

  return (
    <Card>
      <div className="flex items-center justify-between border-b border-border px-3 py-2">
        <h2 className="text-xs font-semibold uppercase tracking-wide text-faint">
          {t("savedTitle")}
        </h2>
        <Button variant="ghost" size="sm" onClick={onClear}>
          {t("clearSaved")}
        </Button>
      </div>
      <ul className="max-h-[520px] divide-y divide-border overflow-y-auto">
        {saved.map((p) => (
          <li key={p.id}>
            <Link href={`/products/${p.id}`} className="flex items-center gap-3 px-3 py-2">
              <div className="h-10 w-10 shrink-0 overflow-hidden rounded bg-surface-2">
                {p.image_url ? (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img
                    src={p.image_url}
                    alt=""
                    className="h-full w-full object-cover"
                    referrerPolicy="no-referrer"
                  />
                ) : null}
              </div>
              <span className="min-w-0 flex-1 truncate text-xs">{p.title}</span>
              <span className="font-mono text-xs tabular-nums text-muted">
                {formatPrice(p.price, p.currency, locale)}
              </span>
            </Link>
          </li>
        ))}
      </ul>
    </Card>
  );
}
