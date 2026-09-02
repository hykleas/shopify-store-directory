import type { Metadata } from "next";
import { getTranslations } from "next-intl/server";

import { FilterPanel } from "@/components/filter-panel";
import { Pagination } from "@/components/pagination";
import { StoreCard } from "@/components/store-card";
import { EmptyState } from "@/components/ui";
import { getFilterOptions, getStores } from "@/lib/queries";
import { storeQuerySchema, toRecord } from "@/lib/validation";

export const dynamic = "force-dynamic";

type SearchParams = Promise<Record<string, string | string[] | undefined>>;

export async function generateMetadata({
  searchParams,
}: {
  searchParams: SearchParams;
}): Promise<Metadata> {
  const t = await getTranslations("stores");
  const raw = toRecord(await searchParams);
  const bits = [raw.category, raw.country, raw.niche].filter(Boolean).join(" · ");
  return {
    title: bits ? `${t("title")} — ${bits}` : t("title"),
    alternates: { canonical: "/stores" },
  };
}

export default async function StoresPage({ searchParams }: { searchParams: SearchParams }) {
  const t = await getTranslations("stores");
  const raw = toRecord(await searchParams);
  const parsed = storeQuerySchema.safeParse(raw);
  const query = parsed.success ? parsed.data : storeQuerySchema.parse({});

  // Sayfa render'i API'yi HTTP ile cagirmaz; ayni sorgu fonksiyonunu kullanir.
  const [page, options] = await Promise.all([getStores(query), getFilterOptions()]);

  return (
    <div className="flex flex-col gap-4 lg:flex-row lg:gap-6">
      <FilterPanel kind="stores" options={options} />

      <div className="min-w-0 flex-1">
        <div className="mb-4">
          <h1 className="text-xl font-semibold tracking-tight">{t("title")}</h1>
          <p className="mt-0.5 text-sm text-muted">
            {t("subtitle", { total: page.total.toLocaleString() })}
          </p>
        </div>

        {page.items.length === 0 ? (
          <EmptyState title={t("empty")} />
        ) : (
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-4">
            {page.items.map((store) => (
              <StoreCard key={store.domain} store={store} />
            ))}
          </div>
        )}

        <Pagination
          page={page.page}
          totalPages={page.total_pages}
          basePath="/stores"
          params={raw}
        />
      </div>
    </div>
  );
}
