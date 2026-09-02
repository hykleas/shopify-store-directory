import { getTranslations } from "next-intl/server";
import Link from "next/link";

import { cn } from "@/components/ui";

/** Sayfalama linkleri mevcut filtreleri korur. */
export async function Pagination({
  page,
  totalPages,
  basePath,
  params,
}: {
  page: number;
  totalPages: number;
  basePath: string;
  params: Record<string, string>;
}) {
  const t = await getTranslations("common");
  if (totalPages <= 1) return null;

  const href = (target: number) => {
    const sp = new URLSearchParams(params);
    if (target <= 1) sp.delete("page");
    else sp.set("page", String(target));
    const qs = sp.toString();
    return qs ? `${basePath}?${qs}` : basePath;
  };

  const linkClass =
    "rounded-md border border-border px-3 py-1.5 text-sm text-muted hover:border-border-strong hover:text-fg";

  return (
    <nav className="mt-6 flex items-center justify-center gap-3">
      {page > 1 ? (
        <Link href={href(page - 1)} className={linkClass} rel="prev">
          {t("previous")}
        </Link>
      ) : (
        <span className={cn(linkClass, "opacity-40")}>{t("previous")}</span>
      )}

      <span className="font-mono text-xs tabular-nums text-faint">
        {t("page", { page, total: totalPages })}
      </span>

      {page < totalPages ? (
        <Link href={href(page + 1)} className={linkClass} rel="next">
          {t("next")}
        </Link>
      ) : (
        <span className={cn(linkClass, "opacity-40")}>{t("next")}</span>
      )}
    </nav>
  );
}
