import type { Metadata } from "next";
import { getLocale, getTranslations } from "next-intl/server";
import { notFound } from "next/navigation";

import { ActivityChart } from "@/components/activity-chart";
import { ProductCard } from "@/components/product-card";
import { Badge, Card, CardBody, CardHeader, CardTitle, LinkButton, Stat } from "@/components/ui";
import {
  countryFlag,
  formatDate,
  formatNumber,
  formatPriceRange,
  storeUrl,
} from "@/lib/format";
import { getStoreDetail } from "@/lib/queries";

export const dynamic = "force-dynamic";

type Params = Promise<{ domain: string }>;

function normalize(raw: string): string {
  return decodeURIComponent(raw).trim().toLowerCase();
}

export async function generateMetadata({ params }: { params: Params }): Promise<Metadata> {
  const { domain } = await params;
  const store = await getStoreDetail(normalize(domain));
  if (!store) return { title: "404" };
  return {
    title: store.name ?? store.domain,
    description:
      store.description ??
      `${store.domain} — ${store.product_count} products, ${store.country ?? ""}`,
    alternates: { canonical: `/stores/${store.domain}` },
  };
}

export default async function StoreDetailPage({ params }: { params: Params }) {
  const { domain } = await params;
  const store = await getStoreDetail(normalize(domain));
  if (!store) notFound();

  const t = await getTranslations("stores");
  const locale = await getLocale();

  const jsonLd = {
    "@context": "https://schema.org",
    "@type": "OnlineStore",
    name: store.name ?? store.domain,
    url: storeUrl(store.domain),
    ...(store.description ? { description: store.description } : {}),
    ...(store.country ? { address: { "@type": "PostalAddress", addressCountry: store.country } } : {}),
  };

  return (
    <div className="space-y-6">
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />

      <header className="flex flex-wrap items-start gap-4">
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <span className="text-xl" aria-hidden>
              {countryFlag(store.country)}
            </span>
            <h1 className="truncate text-xl font-semibold tracking-tight">
              {store.name ?? store.domain}
            </h1>
            {!store.is_active ? <Badge variant="warning">{t("inactive")}</Badge> : null}
          </div>
          <p className="mt-0.5 font-mono text-xs text-faint">{store.domain}</p>
          {store.description ? (
            <p className="mt-2 max-w-2xl text-sm leading-relaxed text-muted">
              {store.description}
            </p>
          ) : null}
          <div className="mt-2 flex flex-wrap gap-1">
            {store.primary_category ? (
              <Badge variant="accent">{store.primary_category}</Badge>
            ) : null}
            {store.currency ? <Badge>{store.currency}</Badge> : null}
            {store.language ? <Badge>{store.language}</Badge> : null}
            {store.tld ? <Badge>.{store.tld}</Badge> : null}
          </div>
        </div>

        <LinkButton
          href={storeUrl(store.domain)}
          target="_blank"
          rel="nofollow noopener noreferrer"
          variant="primary"
        >
          {t("visit")} ↗
        </LinkButton>
      </header>

      <section className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <Stat label={t("products")} value={formatNumber(store.product_count, locale)} />
        <Stat
          label={t("priceRange")}
          value={formatPriceRange(store.min_price, store.max_price, store.currency, locale)}
        />
        <Stat label={t("launched")} value={formatDate(store.launch_date, locale)} />
        <Stat label={t("discovered")} value={formatDate(store.first_seen_at, locale)} />
      </section>

      {store.new_products_7d > 0 ? (
        <p className="text-sm text-positive">
          {t("newIn7d", { count: store.new_products_7d })}
        </p>
      ) : null}

      <div className="grid gap-4 lg:grid-cols-[2fr_1fr]">
        <Card>
          <CardHeader>
            <CardTitle>{t("activityTitle")}</CardTitle>
          </CardHeader>
          <CardBody>
            {store.activity.length === 0 ? (
              <p className="py-8 text-center text-sm text-muted">{t("activityEmpty")}</p>
            ) : (
              <ActivityChart data={store.activity} />
            )}
          </CardBody>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>{t("categoryBreakdown")}</CardTitle>
          </CardHeader>
          <CardBody className="space-y-1.5">
            {store.categories.length === 0 ? (
              <p className="py-6 text-center text-sm text-muted">—</p>
            ) : (
              store.categories.map((c) => {
                const max = store.categories[0]!.product_count || 1;
                return (
                  <div key={c.category} className="text-xs">
                    <div className="flex justify-between">
                      <span className="truncate text-fg">{c.category}</span>
                      <span className="ml-2 font-mono tabular-nums text-faint">
                        {c.product_count}
                      </span>
                    </div>
                    <div className="mt-1 h-1 rounded bg-surface-2">
                      <div
                        className="h-1 rounded bg-accent"
                        style={{ width: `${Math.max(4, (c.product_count / max) * 100)}%` }}
                      />
                    </div>
                  </div>
                );
              })
            )}
          </CardBody>
        </Card>
      </div>

      <section>
        <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-faint">
          {t("latestProducts")}
        </h2>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4 2xl:grid-cols-6">
          {store.products.map((p) => (
            <ProductCard key={p.id} product={p} />
          ))}
        </div>
      </section>
    </div>
  );
}
