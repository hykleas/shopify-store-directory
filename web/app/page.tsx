import { getLocale, getTranslations } from "next-intl/server";
import Link from "next/link";

import { StoreCard } from "@/components/store-card";
import { Card, LinkButton, Stat } from "@/components/ui";
import { formatCompact, formatNumber } from "@/lib/format";
import { getFilterOptions, getLatestStores, getStats } from "@/lib/queries";

export const revalidate = 300;

export default async function HomePage() {
  const t = await getTranslations("home");
  const common = await getTranslations("common");
  const locale = await getLocale();

  const [stats, latest, options] = await Promise.all([
    getStats(),
    getLatestStores(12),
    getFilterOptions(),
  ]);

  return (
    <div className="space-y-10">
      <section className="pt-4">
        <p className="mb-2 font-mono text-[11px] uppercase tracking-widest text-accent">
          {common("free")}
        </p>
        <h1 className="max-w-3xl text-3xl font-semibold tracking-tight sm:text-4xl">
          {t("heroTitle")}
        </h1>
        <p className="mt-3 max-w-2xl text-sm leading-relaxed text-muted">
          {t("heroSubtitle")}
        </p>
        <div className="mt-5 flex flex-wrap gap-2">
          <LinkButton href="/stores" variant="primary" size="lg">
            {t("browseStores")}
          </LinkButton>
          <LinkButton href="/products" variant="outline" size="lg">
            {t("browseProducts")}
          </LinkButton>
        </div>
      </section>

      <section className="grid grid-cols-2 gap-3 sm:grid-cols-3 xl:grid-cols-6">
        <Stat label={t("statStores")} value={formatNumber(stats.stores, locale)} />
        <Stat label={t("statProducts")} value={formatCompact(stats.products, locale)} />
        <Stat label={t("statVariants")} value={formatCompact(stats.variants, locale)} />
        <Stat label={t("statCountries")} value={formatNumber(stats.countries, locale)} />
        <Stat
          label={t("statStoresToday")}
          value={`+${formatNumber(stats.stores_added_today, locale)}`}
        />
        <Stat
          label={t("statProductsToday")}
          value={`+${formatCompact(stats.products_added_today, locale)}`}
        />
      </section>

      <section>
        <div className="mb-3 flex items-baseline justify-between">
          <h2 className="text-sm font-semibold uppercase tracking-wide text-faint">
            {t("latestStores")}
          </h2>
          <Link href="/stores" className="text-xs text-accent hover:underline">
            {t("browseStores")} →
          </Link>
        </div>
        {latest.length === 0 ? (
          <Card className="px-6 py-10 text-center text-sm text-muted">{t("noData")}</Card>
        ) : (
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            {latest.map((store) => (
              <StoreCard key={store.domain} store={store} />
            ))}
          </div>
        )}
      </section>

      <section>
        <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-faint">
          {t("categories")}
        </h2>
        {options.categories.length === 0 ? (
          <Card className="px-6 py-10 text-center text-sm text-muted">{t("noData")}</Card>
        ) : (
          <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-5">
            {options.categories.map((c) => (
              <Link
                key={c.value}
                href={`/products?category=${encodeURIComponent(c.value)}`}
                className="rounded-lg border border-border bg-surface px-3 py-2.5 transition-colors hover:border-border-strong"
              >
                <div className="truncate text-sm text-fg">{c.value}</div>
                <div className="font-mono text-[11px] tabular-nums text-faint">
                  {formatCompact(c.count, locale)}
                </div>
              </Link>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
