import type { MetadataRoute } from "next";

import { getSitemapEntries } from "@/lib/queries";

export const revalidate = 3600;

const base = (process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3000").replace(/\/$/, "");

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const { stores, products, categories, niches } = await getSitemapEntries();

  const staticPages: MetadataRoute.Sitemap = [
    { url: `${base}/`, changeFrequency: "hourly", priority: 1 },
    { url: `${base}/stores`, changeFrequency: "hourly", priority: 0.9 },
    { url: `${base}/products`, changeFrequency: "hourly", priority: 0.9 },
    { url: `${base}/finder`, changeFrequency: "daily", priority: 0.5 },
    { url: `${base}/bot`, changeFrequency: "monthly", priority: 0.3 },
  ];

  // Kategori ve nis sayfalari filtreli listeler olarak indekslenir.
  const categoryPages: MetadataRoute.Sitemap = categories.map((c) => ({
    url: `${base}/products?category=${encodeURIComponent(c)}`,
    changeFrequency: "daily",
    priority: 0.7,
  }));

  const nichePages: MetadataRoute.Sitemap = niches.map((n) => ({
    url: `${base}/products?niche=${encodeURIComponent(n)}`,
    changeFrequency: "daily",
    priority: 0.6,
  }));

  const storePages: MetadataRoute.Sitemap = stores.map((s) => ({
    url: `${base}/stores/${s.domain}`,
    lastModified: s.updated ? new Date(s.updated) : undefined,
    changeFrequency: "weekly",
    priority: 0.6,
  }));

  const productPages: MetadataRoute.Sitemap = products.map((p) => ({
    url: `${base}/products/${p.id}`,
    lastModified: p.updated ? new Date(p.updated) : undefined,
    changeFrequency: "weekly",
    priority: 0.4,
  }));

  return [...staticPages, ...categoryPages, ...nichePages, ...storePages, ...productPages];
}
