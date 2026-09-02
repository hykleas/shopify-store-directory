import { getTranslations } from "next-intl/server";
import Link from "next/link";

import { LocaleSwitcher } from "@/components/locale-switcher";
import { NavLink } from "@/components/nav-link";

/**
 * Header'da sadece: Stores, Products, Finder, dil secici.
 * Pricing / upgrade / giris yok - urun ucretsiz.
 */
export async function SiteHeader() {
  const t = await getTranslations("nav");
  const site = await getTranslations("site");

  return (
    <header className="sticky top-0 z-30 border-b border-border bg-bg/85 backdrop-blur">
      <div className="mx-auto flex h-14 w-full max-w-[1400px] items-center gap-4 px-4 sm:px-6">
        <Link href="/" className="flex items-center gap-2 font-semibold tracking-tight">
          <span
            aria-hidden
            className="grid h-6 w-6 place-items-center rounded bg-accent text-[11px] font-bold text-accent-fg"
          >
            OS
          </span>
          <span className="hidden sm:inline">{site("name")}</span>
        </Link>

        <nav className="flex items-center gap-1 text-sm">
          <NavLink href="/stores">{t("stores")}</NavLink>
          <NavLink href="/products">{t("products")}</NavLink>
          <NavLink href="/finder">{t("finder")}</NavLink>
        </nav>

        <div className="ml-auto flex items-center gap-3">
          <LocaleSwitcher />
        </div>
      </div>
    </header>
  );
}
