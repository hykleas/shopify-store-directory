import { useLocale, useTranslations } from "next-intl";
import Link from "next/link";

import { Badge, Card } from "@/components/ui";
import { countryFlag, discountPercent, formatPrice } from "@/lib/format";
import type { ProductSummary } from "@/lib/types";

/**
 * Urun karti. Gorsel Shopify CDN'inden hotlink edilir (kopyalanmaz),
 * bu yuzden next/image degil düz <img>.
 */
export function ProductCard({ product }: { product: ProductSummary }) {
  const t = useTranslations("products");
  const locale = useLocale();
  const off = discountPercent(product.price, product.compare_at_price);

  return (
    <Card className="group overflow-hidden hover:border-border-strong">
      <Link href={`/products/${product.id}`} className="block">
        <div className="relative aspect-square bg-surface-2">
          {product.image_url ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img
              src={product.image_url}
              alt=""
              loading="lazy"
              decoding="async"
              referrerPolicy="no-referrer"
              className="h-full w-full object-cover transition-opacity group-hover:opacity-90"
            />
          ) : (
            <div className="grid h-full place-items-center font-mono text-[11px] text-faint">
              no image
            </div>
          )}
          {off !== null ? (
            <span className="absolute left-1.5 top-1.5 rounded bg-negative/90 px-1.5 py-0.5 text-[10px] font-semibold text-white">
              {t("off", { percent: off })}
            </span>
          ) : null}
          {product.store_count && product.store_count > 1 ? (
            <span className="absolute right-1.5 top-1.5 rounded bg-bg/85 px-1.5 py-0.5 font-mono text-[10px] text-fg">
              {product.store_count}×
            </span>
          ) : null}
        </div>

        <div className="space-y-1.5 p-2.5">
          <p className="clamp-2 text-xs leading-4 text-fg">{product.title}</p>
          <div className="flex items-baseline gap-1.5">
            <span className="font-mono text-sm font-semibold tabular-nums text-fg">
              {formatPrice(product.price, product.currency, locale)}
            </span>
            {product.compare_at_price !== null && off !== null ? (
              <span className="font-mono text-[11px] text-faint line-through">
                {formatPrice(product.compare_at_price, product.currency, locale)}
              </span>
            ) : null}
          </div>
          <div className="flex items-center gap-1 text-[11px] text-faint">
            <span aria-hidden>{countryFlag(product.store_country)}</span>
            <span className="truncate font-mono">{product.store_domain}</span>
          </div>
          {product.niche ? (
            <Badge className="max-w-full truncate">{product.niche}</Badge>
          ) : null}
        </div>
      </Link>
    </Card>
  );
}
