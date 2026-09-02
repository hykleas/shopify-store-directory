import type { Metadata } from "next";
import { getTranslations } from "next-intl/server";

import { RemovalForm } from "@/components/removal-form";
import { Card, CardBody, CardHeader, CardTitle } from "@/components/ui";

export const revalidate = 3600;

export async function generateMetadata(): Promise<Metadata> {
  const t = await getTranslations("bot");
  return { title: t("title"), description: t("intro"), alternates: { canonical: "/bot" } };
}

export default async function BotPage() {
  const t = await getTranslations("bot");
  const userAgent =
    process.env.BOT_USER_AGENT ??
    `StoreDirectoryBot/1.0 (+${process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3000"}/bot)`;

  const dos = [t("do1"), t("do2"), t("do3"), t("do4"), t("do5")];
  const donts = [t("dont1"), t("dont2"), t("dont3"), t("dont4"), t("dont5")];

  return (
    <div className="max-w-3xl space-y-6">
      <header>
        <h1 className="text-xl font-semibold tracking-tight">{t("title")}</h1>
        <p className="mt-2 text-sm leading-relaxed text-muted">{t("intro")}</p>
      </header>

      <div>
        <p className="mb-1 text-[11px] uppercase tracking-wide text-faint">
          {t("userAgent")}
        </p>
        <code className="block overflow-x-auto rounded-md border border-border bg-surface-2 px-3 py-2 font-mono text-xs text-fg">
          {userAgent}
        </code>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>{t("doTitle")}</CardTitle>
          </CardHeader>
          <CardBody>
            <ul className="space-y-2 text-sm leading-relaxed text-muted">
              {dos.map((line) => (
                <li key={line} className="flex gap-2">
                  <span className="text-positive">✓</span>
                  <span>{line}</span>
                </li>
              ))}
            </ul>
          </CardBody>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>{t("dontTitle")}</CardTitle>
          </CardHeader>
          <CardBody>
            <ul className="space-y-2 text-sm leading-relaxed text-muted">
              {donts.map((line) => (
                <li key={line} className="flex gap-2">
                  <span className="text-negative">✕</span>
                  <span>{line}</span>
                </li>
              ))}
            </ul>
          </CardBody>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>{t("removalTitle")}</CardTitle>
        </CardHeader>
        <CardBody className="space-y-4">
          <p className="text-sm leading-relaxed text-muted">{t("removalBody")}</p>
          <RemovalForm />
        </CardBody>
      </Card>
    </div>
  );
}
