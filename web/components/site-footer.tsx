import { getTranslations } from "next-intl/server";
import Link from "next/link";

export async function SiteFooter() {
  const t = await getTranslations("nav");
  const common = await getTranslations("common");
  const site = await getTranslations("site");

  return (
    <footer className="mt-12 border-t border-border">
      <div className="mx-auto flex w-full max-w-[1400px] flex-col gap-2 px-4 py-6 text-xs text-faint sm:flex-row sm:items-center sm:px-6">
        <span>
          {site("name")} · {common("free")}
        </span>
        <nav className="flex gap-4 sm:ml-auto">
          <Link href="/stores" className="hover:text-fg">
            {t("stores")}
          </Link>
          <Link href="/products" className="hover:text-fg">
            {t("products")}
          </Link>
          <Link href="/finder" className="hover:text-fg">
            {t("finder")}
          </Link>
          <Link href="/bot" className="hover:text-fg">
            {t("bot")}
          </Link>
        </nav>
      </div>
    </footer>
  );
}
