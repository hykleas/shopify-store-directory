import type { Metadata } from "next";
import { getTranslations } from "next-intl/server";

import { FilterPanel } from "@/components/filter-panel";
import { Pagination } from "@/components/pagination";
import { ProductCard } from "@/components/product-card";
import { EmptyState } from "@/components/ui";
import { getFilterOptions, getProducts } from "@/lib/queries";
import { productQuerySchema, toRecord } from "@/lib/validation";

export const dynamic = "force-dynamic";

type SearchParams = Promise<Record<string, string | string[] | undefined>>;

export async function generateMetadata({
  searchParams,
}: {
  searchParams: SearchParams;
}): Promise<Metadata> {
  const t = await getTranslations("products");
  const raw = toRecord(await searchParams);
  const bits = [raw.q, raw.niche, raw.category].filter(Boolean).join(" · ");
  return {
    title: bits ? `${t("title")} — ${bits}` : t("title"),
    alternates: { canonical: "/products" },
  };
}

export default async function ProductsPage({ searchParams }: { searchParams: SearchParams }) {
  const t = await getTranslations("products");
  const raw = toRecord(await searchParams);
  const parsed = productQuerySchema.safeParse(raw);
  const query = parsed.success ? parsed.data : productQuerySchema.parse({});

  const [page, options] = await Promise.all([getProducts(query), getFilterOptions()]);

  return (
    <div className="flex flex-col gap-4 lg:flex-row lg:gap-6">
      <FilterPanel kind="products" options={options} />

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
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4 2xl:grid-cols-6">
            {page.items.map((product) => (
              <ProductCard key={product.id} product={product} />
            ))}
          </div>
        )}

        <Pagination
          page={page.page}
          totalPages={page.total_pages}
          basePath="/products"
          params={raw}
        />
      </div>
    </div>
  );
}
