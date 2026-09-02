import { useLocale, useTranslations } from "next-intl";
import Link from "next/link";

import { Badge, Card } from "@/components/ui";
import { countryFlag, formatDate, formatNumber, formatPriceRange } from "@/lib/format";
import type { StoreSummary } from "@/lib/types";

/** Kompakt, veri yogun magaza karti. Dekoratif gorsel yok. */
export function StoreCard({ store }: { store: StoreSummary }) {
  const t = useTranslations("stores");
  const locale = useLocale();

  return (
    <Card className="flex flex-col hover:border-border-strong">
      <Link href={`/stores/${store.domain}`} className="flex flex-1 flex-col p-3.5">
        <div className="flex items-start gap-2">
          <span className="text-base leading-6" aria-hidden>
            {countryFlag(store.country)}
          </span>
          <div className="min-w-0 flex-1">
            <div className="truncate text-sm font-semibold text-fg">
              {store.name ?? store.domain}
            </div>
            <div className="truncate font-mono text-[11px] text-faint">{store.domain}</div>
          </div>
        </div>

        <dl className="mt-3 grid grid-cols-2 gap-x-3 gap-y-1.5 text-[11px]">
          <div>
            <dt className="text-faint">{t("products")}</dt>
            <dd className="font-mono tabular-nums text-fg">
              {formatNumber(store.product_count, locale)}
            </dd>
          </div>
          <div>
            <dt className="text-faint">{t("priceRange")}</dt>
            <dd className="truncate font-mono tabular-nums text-fg">
              {formatPriceRange(store.min_price, store.max_price, store.currency, locale)}
            </dd>
          </div>
          <div>
            <dt className="text-faint">{t("launched")}</dt>
            <dd className="text-fg">{formatDate(store.launch_date, locale)}</dd>
          </div>
          <div>
            <dt className="text-faint">{t("discovered")}</dt>
            <dd className="text-fg">{formatDate(store.first_seen_at, locale)}</dd>
          </div>
        </dl>

        <div className="mt-3 flex flex-wrap items-center gap-1">
          {store.primary_category ? (
            <Badge variant="accent">{store.primary_category}</Badge>
          ) : null}
          {store.currency ? <Badge>{store.currency}</Badge> : null}
          {store.tld ? <Badge>.{store.tld}</Badge> : null}
          {store.new_products_7d > 0 ? (
            <Badge variant="positive">+{store.new_products_7d} · 7d</Badge>
          ) : null}
        </div>
      </Link>
    </Card>
  );
}
