import { getTranslations } from "next-intl/server";

import { LinkButton } from "@/components/ui";

export default async function NotFound() {
  const t = await getTranslations("common");
  const s = await getTranslations("stores");

  return (
    <div className="grid min-h-[50vh] place-items-center text-center">
      <div>
        <p className="font-mono text-5xl font-semibold text-faint">404</p>
        <h1 className="mt-3 text-lg font-semibold">{s("notFound")}</h1>
        <p className="mt-1 text-sm text-muted">{s("notFoundBody")}</p>
        <LinkButton href="/" variant="outline" className="mt-5">
          {t("backHome")}
        </LinkButton>
      </div>
    </div>
  );
}
