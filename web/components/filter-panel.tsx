"use client";

import { useTranslations } from "next-intl";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useMemo, useState, useTransition } from "react";

import { Button, Field, Input, Select, cn } from "@/components/ui";
import type { FilterOptions } from "@/lib/queries";

/**
 * Filtre paneli. Tum durum URL query string'inde tutulur: yenilemede kayip
 * olmaz, link paylasilabilir. Mobilde alttan acilan sheet.
 */

export type FilterKind = "stores" | "products";

type Props = {
  kind: FilterKind;
  options: FilterOptions;
};

const STORE_KEYS = [
  "country", "currency", "language", "tld", "category", "niche",
  "min_price", "max_price", "min_products", "max_products",
  "launched_after", "launched_before", "sort",
] as const;

const PRODUCT_KEYS = [
  "q", "category", "niche", "min_price", "max_price",
  "country", "currency", "store_count_min", "sort",
] as const;

const SORTS: Record<FilterKind, string[]> = {
  stores: ["newest", "products", "recently_active"],
  products: ["newest", "price", "spread"],
};

export function FilterPanel({ kind, options }: Props) {
  const searchParams = useSearchParams();
  // URL degisince (geri/ileri dahil) form remount olur ve draft yeniden
  // ilklenir - effect ile senkronlamaya gerek kalmaz.
  return (
    <FilterForm
      key={searchParams.toString()}
      kind={kind}
      options={options}
      searchParams={searchParams}
    />
  );
}

function FilterForm({
  kind,
  options,
  searchParams,
}: Props & { searchParams: ReturnType<typeof useSearchParams> }) {
  const t = useTranslations("filters");
  const tSort = useTranslations("sort");
  const router = useRouter();
  const pathname = usePathname();
  const [, startTransition] = useTransition();
  const [open, setOpen] = useState(false);

  const keys = kind === "stores" ? STORE_KEYS : PRODUCT_KEYS;

  const [draft, setDraft] = useState<Record<string, string>>(() =>
    Object.fromEntries(keys.map((k) => [k, searchParams.get(k) ?? ""])),
  );

  const activeCount = useMemo(
    () => keys.filter((k) => k !== "sort" && (searchParams.get(k) ?? "") !== "").length,
    [searchParams, keys],
  );

  // Nis listesi secili kategoriye gore daralir.
  const niches = useMemo(() => {
    const category = draft.category;
    const list = category
      ? options.niches.filter((n) => n.category === category)
      : options.niches;
    return list.slice(0, 120);
  }, [draft.category, options.niches]);

  function set(key: string, value: string) {
    setDraft((d) => ({ ...d, [key]: value, ...(key === "category" ? { niche: "" } : {}) }));
  }

  function apply() {
    const params = new URLSearchParams();
    for (const [key, value] of Object.entries(draft)) {
      if (value.trim() !== "") params.set(key, value.trim());
    }
    setOpen(false);
    startTransition(() => router.push(`${pathname}?${params.toString()}`, { scroll: false }));
  }

  function clear() {
    setDraft(Object.fromEntries(keys.map((k) => [k, ""])));
    setOpen(false);
    startTransition(() => router.push(pathname, { scroll: false }));
  }

  const body = (
    <form
      className="space-y-3"
      onSubmit={(e) => {
        e.preventDefault();
        apply();
      }}
    >
      {kind === "products" ? (
        <Field label={t("search")}>
          <Input
            value={draft.q ?? ""}
            onChange={(e) => set("q", e.target.value)}
            placeholder="…"
          />
        </Field>
      ) : null}

      <Field label={t("sort")}>
        <Select value={draft.sort ?? ""} onChange={(e) => set("sort", e.target.value)}>
          {SORTS[kind].map((s) => (
            <option key={s} value={s}>
              {tSort(s)}
            </option>
          ))}
        </Select>
      </Field>

      <Field label={t("category")}>
        <Select value={draft.category ?? ""} onChange={(e) => set("category", e.target.value)}>
          <option value="">{t("any")}</option>
          {options.categories.map((c) => (
            <option key={c.value} value={c.value}>
              {c.value} ({c.count})
            </option>
          ))}
        </Select>
      </Field>

      <Field label={t("niche")}>
        <Select value={draft.niche ?? ""} onChange={(e) => set("niche", e.target.value)}>
          <option value="">{t("any")}</option>
          {niches.map((n) => (
            <option key={n.value} value={n.value}>
              {n.value} ({n.count})
            </option>
          ))}
        </Select>
      </Field>

      <div className="grid grid-cols-2 gap-2">
        <Field label={t("country")}>
          <Select value={draft.country ?? ""} onChange={(e) => set("country", e.target.value)}>
            <option value="">{t("any")}</option>
            {options.countries.map((c) => (
              <option key={c.value} value={c.value}>
                {c.value} ({c.count})
              </option>
            ))}
          </Select>
        </Field>
        <Field label={t("currency")}>
          <Select value={draft.currency ?? ""} onChange={(e) => set("currency", e.target.value)}>
            <option value="">{t("any")}</option>
            {options.currencies.map((c) => (
              <option key={c.value} value={c.value}>
                {c.value} ({c.count})
              </option>
            ))}
          </Select>
        </Field>
      </div>

      <div className="grid grid-cols-2 gap-2">
        <Field label={t("minPrice")}>
          <Input
            type="number"
            min={0}
            step="0.01"
            inputMode="decimal"
            value={draft.min_price ?? ""}
            onChange={(e) => set("min_price", e.target.value)}
          />
        </Field>
        <Field label={t("maxPrice")}>
          <Input
            type="number"
            min={0}
            step="0.01"
            inputMode="decimal"
            value={draft.max_price ?? ""}
            onChange={(e) => set("max_price", e.target.value)}
          />
        </Field>
      </div>

      {kind === "stores" ? (
        <>
          <div className="grid grid-cols-2 gap-2">
            <Field label={t("minProducts")}>
              <Input
                type="number"
                min={0}
                value={draft.min_products ?? ""}
                onChange={(e) => set("min_products", e.target.value)}
              />
            </Field>
            <Field label={t("maxProducts")}>
              <Input
                type="number"
                min={0}
                value={draft.max_products ?? ""}
                onChange={(e) => set("max_products", e.target.value)}
              />
            </Field>
          </div>
          <div className="grid grid-cols-2 gap-2">
            <Field label={t("launchedAfter")}>
              <Input
                type="date"
                value={draft.launched_after ?? ""}
                onChange={(e) => set("launched_after", e.target.value)}
              />
            </Field>
            <Field label={t("launchedBefore")}>
              <Input
                type="date"
                value={draft.launched_before ?? ""}
                onChange={(e) => set("launched_before", e.target.value)}
              />
            </Field>
          </div>
          <div className="grid grid-cols-2 gap-2">
            <Field label={t("tld")}>
              <Select value={draft.tld ?? ""} onChange={(e) => set("tld", e.target.value)}>
                <option value="">{t("any")}</option>
                {options.tlds.map((x) => (
                  <option key={x.value} value={x.value}>
                    .{x.value} ({x.count})
                  </option>
                ))}
              </Select>
            </Field>
            <Field label={t("language")}>
              <Input
                value={draft.language ?? ""}
                onChange={(e) => set("language", e.target.value)}
                placeholder="en"
              />
            </Field>
          </div>
        </>
      ) : (
        <Field label={t("storeCountMin")}>
          <Input
            type="number"
            min={1}
            value={draft.store_count_min ?? ""}
            onChange={(e) => set("store_count_min", e.target.value)}
          />
        </Field>
      )}

      <div className="flex gap-2 pt-1">
        <Button type="submit" variant="primary" className="flex-1">
          {t("apply")}
        </Button>
        <Button type="button" variant="ghost" onClick={clear}>
          {t("clear")}
        </Button>
      </div>
    </form>
  );

  return (
    <>
      {/* Masaustu: sabit sol panel */}
      <aside className="hidden w-64 shrink-0 lg:block">
        <div className="sticky top-20 rounded-lg border border-border bg-surface p-3.5">
          <h2 className="mb-3 text-xs font-semibold uppercase tracking-wide text-faint">
            {t("title")}
            {activeCount > 0 ? (
              <span className="ml-1 text-accent">({activeCount})</span>
            ) : null}
          </h2>
          {body}
        </div>
      </aside>

      {/* Mobil: alttan acilan sheet */}
      <div className="lg:hidden">
        <Button variant="outline" className="w-full" onClick={() => setOpen(true)}>
          {t("open")}
          {activeCount > 0 ? ` (${activeCount})` : ""}
        </Button>
      </div>

      <div
        className={cn(
          "fixed inset-0 z-40 lg:hidden",
          open ? "pointer-events-auto" : "pointer-events-none",
        )}
        aria-hidden={!open}
      >
        <div
          className={cn(
            "absolute inset-0 bg-black/60 transition-opacity",
            open ? "opacity-100" : "opacity-0",
          )}
          onClick={() => setOpen(false)}
        />
        <div
          className={cn(
            "absolute inset-x-0 bottom-0 max-h-[85vh] overflow-y-auto rounded-t-xl border-t border-border bg-surface p-4 transition-transform",
            open ? "translate-y-0" : "translate-y-full",
          )}
        >
          <div className="mb-3 flex items-center justify-between">
            <h2 className="text-sm font-semibold">{t("title")}</h2>
            <Button variant="ghost" size="sm" onClick={() => setOpen(false)}>
              {t("close")}
            </Button>
          </div>
          {body}
        </div>
      </div>
    </>
  );
}
