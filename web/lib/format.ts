/** Bicimlendirme yardimcilari. Para her yerde ayni kurallarla gosterilir. */

export function formatPrice(
  value: number | null | undefined,
  currency: string | null | undefined,
  locale = "en",
): string {
  if (value === null || value === undefined) return "—";
  const code = currency && /^[A-Z]{3}$/.test(currency) ? currency : undefined;
  try {
    return new Intl.NumberFormat(locale, {
      style: code ? "currency" : "decimal",
      currency: code,
      maximumFractionDigits: value >= 1000 ? 0 : 2,
      minimumFractionDigits: 0,
    }).format(value);
  } catch {
    return `${value.toFixed(2)}${code ? ` ${code}` : ""}`;
  }
}

export function formatPriceRange(
  min: number | null,
  max: number | null,
  currency: string | null,
  locale = "en",
): string {
  if (min === null && max === null) return "—";
  if (min !== null && max !== null && Math.abs(min - max) < 0.005) {
    return formatPrice(min, currency, locale);
  }
  return `${formatPrice(min, currency, locale)} – ${formatPrice(max, currency, locale)}`;
}

export function formatNumber(value: number | null | undefined, locale = "en"): string {
  if (value === null || value === undefined) return "—";
  return new Intl.NumberFormat(locale).format(value);
}

export function formatCompact(value: number | null | undefined, locale = "en"): string {
  if (value === null || value === undefined) return "—";
  return new Intl.NumberFormat(locale, { notation: "compact", maximumFractionDigits: 1 })
    .format(value);
}

export function formatDate(value: string | null | undefined, locale = "en"): string {
  if (!value) return "—";
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return "—";
  return new Intl.DateTimeFormat(locale, {
    year: "numeric",
    month: "short",
    day: "numeric",
  }).format(d);
}

export function daysSince(value: string | null | undefined): number | null {
  if (!value) return null;
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return null;
  return Math.floor((Date.now() - d.getTime()) / 86_400_000);
}

/** ISO ulke kodundan bayrak emojisi. Bilinmiyorsa globe. */
export function countryFlag(code: string | null | undefined): string {
  if (!code || !/^[A-Za-z]{2}$/.test(code)) return "\u{1F310}";
  const upper = code.toUpperCase();
  return String.fromCodePoint(
    ...[...upper].map((c) => 0x1f1e6 + c.charCodeAt(0) - 65),
  );
}

/** İndirim yuzdesi - urunun kendi listeleme fiyatlarindan, satis verisi degil. */
export function discountPercent(
  price: number | null,
  compareAt: number | null,
): number | null {
  if (price === null || compareAt === null || compareAt <= price || compareAt <= 0) {
    return null;
  }
  return Math.round(((compareAt - price) / compareAt) * 100);
}

export function storeUrl(domain: string): string {
  return `https://${domain}/`;
}
