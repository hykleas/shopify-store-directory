import type { Metadata } from "next";
import { getLocale, getTranslations } from "next-intl/server";
import Link from "next/link";
import { notFound } from "next/navigation";

import {
  Badge,
  Card,
  CardBody,
  CardHeader,
  CardTitle,
  LinkButton,
} from "@/components/ui";
import {
  countryFlag,
  discountPercent,
  formatDate,
  formatPrice,
  formatPriceRange,
} from "@/lib/format";
import { getProductDetail } from "@/lib/queries";

export const dynamic = "force-dynamic";

type Params = Promise<{ id: string }>;

export async function generateMetadata({ params }: { params: Params }): Promise<Metadata> {
  const { id } = await params;
  const product = await getProductDetail(Number(id));
  if (!product) return { title: "404" };
  return {
    title: product.title,
    description: `${product.title} — ${product.store_domain}`,
    alternates: { canonical: `/products/${product.id}` },
    openGraph: product.image_url ? { images: [product.image_url] } : undefined,
  };
}

export default async function ProductDetailPage({ params }: { params: Params }) {
  const { id } = await params;
  const numeric = Number(id);
  if (!Number.isInteger(numeric) || numeric <= 0) notFound();

  const product = await getProductDetail(numeric);
  if (!product) notFound();

  const t = await getTranslations("products");
  const locale = await getLocale();
  const off = discountPercent(product.price, product.compare_at_price);

  // 30 gun onceki yayilim - "kac magazada listeleniyordu", satis degil.
  const past = product.spread_history[0];

  const jsonLd = {
    "@context": "https://schema.org",
    "@type": "Product",
    name: product.title,
    ...(product.image_url ? { image: [product.image_url] } : {}),
    ...(product.vendor ? { brand: { "@type": "Brand", name: product.vendor } } : {}),
    offers: {
      "@type": "Offer",
      price: product.price ?? undefined,
      priceCurrency: product.currency ?? undefined,
      url: `https://${product.store_domain}/products/${product.handle}`,
    },
  };

  return (
    <div className="space-y-6">
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />

      <div className="grid gap-6 lg:grid-cols-[minmax(0,460px)_1fr]">
        <Card className="overflow-hidden">
          <div className="aspect-square bg-surface-2">
            {product.image_url ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img
                src={product.image_url}
                alt={product.title}
                className="h-full w-full object-cover"
                referrerPolicy="no-referrer"
              />
            ) : (
              <div className="grid h-full place-items-center font-mono text-xs text-faint">
                no image
              </div>
            )}
          </div>
        </Card>

        <div className="space-y-4">
          <div>
            <h1 className="text-xl font-semibold leading-snug tracking-tight">
              {product.title}
            </h1>
            <Link
              href={`/stores/${product.store_domain}`}
              className="mt-1 inline-flex items-center gap-1.5 font-mono text-xs text-muted hover:text-fg"
            >
              <span aria-hidden>{countryFlag(product.store_country)}</span>
              {product.store_domain}
            </Link>
          </div>

          <div className="flex flex-wrap items-baseline gap-3">
            <span className="font-mono text-3xl font-semibold tabular-nums">
              {formatPrice(product.price, product.currency, locale)}
            </span>
            {off !== null ? (
              <>
                <span className="font-mono text-sm text-faint line-through">
                  {formatPrice(product.compare_at_price, product.currency, locale)}
                </span>
                <Badge variant="danger">{t("off", { percent: off })}</Badge>
              </>
            ) : null}
          </div>

          {product.store_count && product.store_count > 1 ? (
            <div className="rounded-lg border border-border bg-surface px-3.5 py-3">
              <p className="text-sm text-fg">
                {t("soldIn", { count: product.store_count })}
                {past ? (
                  <span className="ml-2 text-muted">
                    ({t("spreadWas", { count: past.store_count })})
                  </span>
                ) : null}
              </p>
              <p className="mt-1 font-mono text-sm tabular-nums text-muted">
                {t("priceSpread")}:{" "}
                {formatPriceRange(
                  product.spread_min_price,
                  product.spread_max_price,
                  product.currency,
                  locale,
                )}
              </p>
            </div>
          ) : null}

          <div className="flex flex-wrap gap-1">
            {product.category ? <Badge variant="accent">{product.category}</Badge> : null}
            {product.niche ? <Badge>{product.niche}</Badge> : null}
            {product.vendor ? <Badge>{product.vendor}</Badge> : null}
            {product.product_type ? <Badge>{product.product_type}</Badge> : null}
          </div>

          <LinkButton
            href={`https://${product.store_domain}/products/${product.handle}`}
            target="_blank"
            rel="nofollow noopener noreferrer"
            variant="primary"
          >
            {t("viewProduct")} ↗
          </LinkButton>

          {product.variants.length > 0 ? (
            <Card>
              <CardHeader>
                <CardTitle>{t("variants")}</CardTitle>
              </CardHeader>
              <CardBody className="space-y-1">
                {product.variants.map((v, i) => (
                  <div
                    key={`${v.title ?? "v"}-${i}`}
                    className="flex items-center justify-between text-xs"
                  >
                    <span className="truncate text-muted">{v.title ?? "—"}</span>
                    <span className="ml-3 flex shrink-0 items-center gap-2">
                      <span className="font-mono tabular-nums text-fg">
                        {formatPrice(v.price, product.currency, locale)}
                      </span>
                      {v.available === null ? null : v.available ? (
                        <Badge variant="positive">{t("inStock")}</Badge>
                      ) : (
                        <Badge variant="danger">{t("outOfStock")}</Badge>
                      )}
                    </span>
                  </div>
                ))}
              </CardBody>
            </Card>
          ) : null}

          {product.tags.length > 0 ? (
            <div>
              <p className="mb-1 text-[11px] uppercase tracking-wide text-faint">
                {t("tags")}
              </p>
              <div className="flex flex-wrap gap-1">
                {product.tags.slice(0, 24).map((tag) => (
                  <Badge key={tag}>{tag}</Badge>
                ))}
              </div>
            </div>
          ) : null}
        </div>
      </div>

      {product.listings.length > 1 ? (
        <Card>
          <CardHeader>
            <CardTitle>
              {t("otherStores")} · {t("compareTable")}
            </CardTitle>
          </CardHeader>
          <div className="scroll-x">
            <table className="w-full min-w-[520px] text-sm">
              <thead>
                <tr className="border-b border-border text-left text-[11px] uppercase tracking-wide text-faint">
                  <th className="px-4 py-2 font-medium">{t("store")}</th>
                  <th className="px-4 py-2 font-medium">{t("price")}</th>
                  <th className="px-4 py-2 font-medium">{t("firstSeen")}</th>
                  <th className="px-4 py-2" />
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {product.listings.map((l) => (
                  <tr
                    key={l.product_id}
                    className={l.product_id === product.id ? "bg-surface-2" : undefined}
                  >
                    <td className="px-4 py-2">
                      <Link
                        href={`/stores/${l.store_domain}`}
                        className="flex items-center gap-1.5 font-mono text-xs hover:text-accent"
                      >
                        <span aria-hidden>{countryFlag(l.store_country)}</span>
                        {l.store_domain}
                      </Link>
                    </td>
                    <td className="px-4 py-2 font-mono tabular-nums">
                      {formatPrice(l.price, l.currency, locale)}
                    </td>
                    <td className="px-4 py-2 text-xs text-muted">
                      {formatDate(l.first_seen_at, locale)}
                    </td>
                    <td className="px-4 py-2 text-right">
                      <Link
                        href={`/products/${l.product_id}`}
                        className="text-xs text-accent hover:underline"
                      >
                        →
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      ) : null}
    </div>
  );
}
