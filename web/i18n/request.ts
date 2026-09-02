import { cookies } from "next/headers";
import { getRequestConfig } from "next-intl/server";

/**
 * Locale prefix'li routing kullanmiyoruz: dil cerezden okunur, URL'ler sabit
 * kalir (SEO acisindan tek kanonik adres, spec'te locale routing istenmedi).
 */
export const LOCALES = ["en", "tr"] as const;
export type Locale = (typeof LOCALES)[number];
export const DEFAULT_LOCALE: Locale = "en";
export const LOCALE_COOKIE = "locale";

export function isLocale(value: string | undefined): value is Locale {
  return !!value && (LOCALES as readonly string[]).includes(value);
}

export default getRequestConfig(async () => {
  const store = await cookies();
  const raw = store.get(LOCALE_COOKIE)?.value;
  const locale: Locale = isLocale(raw) ? raw : DEFAULT_LOCALE;

  return {
    locale,
    messages: (await import(`../messages/${locale}.json`)).default,
  };
});
