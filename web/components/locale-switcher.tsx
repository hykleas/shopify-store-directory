"use client";

import { useLocale } from "next-intl";
import { useRouter } from "next/navigation";
import { useTransition } from "react";

import { Select } from "@/components/ui";

const OPTIONS = [
  { value: "en", label: "EN" },
  { value: "tr", label: "TR" },
];

/** Dil cerezi ayarlanip sayfa yenilenir; URL degismez (bkz. i18n/request.ts). */
export function LocaleSwitcher() {
  const locale = useLocale();
  const router = useRouter();
  const [pending, startTransition] = useTransition();

  return (
    <Select
      aria-label="Language"
      className="h-8 w-[68px] text-xs"
      value={locale}
      disabled={pending}
      onChange={(e) => {
        const next = e.target.value;
        document.cookie = `locale=${next}; path=/; max-age=31536000; samesite=lax`;
        startTransition(() => router.refresh());
      }}
    >
      {OPTIONS.map((o) => (
        <option key={o.value} value={o.value}>
          {o.label}
        </option>
      ))}
    </Select>
  );
}
