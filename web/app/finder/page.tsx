import type { Metadata } from "next";
import { getTranslations } from "next-intl/server";

import { FinderDeck } from "@/components/finder-deck";
import { getFeed } from "@/lib/queries";

export const dynamic = "force-dynamic";

export async function generateMetadata(): Promise<Metadata> {
  const t = await getTranslations("finder");
  return { title: t("title"), description: t("subtitle"), alternates: { canonical: "/finder" } };
}

export default async function FinderPage() {
  const t = await getTranslations("finder");
  const initial = await getFeed({ limit: 20, cursor: undefined, category: undefined, niche: undefined });

  return (
    <div className="space-y-5">
      <header>
        <h1 className="text-xl font-semibold tracking-tight">{t("title")}</h1>
        <p className="mt-0.5 text-sm text-muted">{t("subtitle")}</p>
      </header>
      <FinderDeck initial={initial} />
    </div>
  );
}
