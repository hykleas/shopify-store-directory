"use client";

import { useTranslations } from "next-intl";
import { useState } from "react";

import { Button, Field, Input, Textarea } from "@/components/ui";

type State = "idle" | "sending" | "done" | "error" | "limited";

export function RemovalForm() {
  const t = useTranslations("bot");
  const [state, setState] = useState<State>("idle");
  const [domain, setDomain] = useState("");
  const [email, setEmail] = useState("");
  const [reason, setReason] = useState("");

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setState("sending");
    try {
      const res = await fetch("/api/removal-requests", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ domain, email: email || undefined, reason: reason || undefined }),
      });
      if (res.status === 429) {
        setState("limited");
        return;
      }
      if (!res.ok) {
        setState("error");
        return;
      }
      setState("done");
      setDomain("");
      setEmail("");
      setReason("");
    } catch {
      setState("error");
    }
  }

  return (
    <form onSubmit={submit} className="max-w-md space-y-3">
      <Field label={t("domain")}>
        <Input
          required
          value={domain}
          onChange={(e) => setDomain(e.target.value)}
          placeholder="example.com"
          autoComplete="off"
        />
      </Field>
      <Field label={t("email")}>
        <Input
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="you@example.com"
          autoComplete="email"
        />
      </Field>
      <Field label={t("reason")}>
        <Textarea value={reason} onChange={(e) => setReason(e.target.value)} rows={3} />
      </Field>

      <Button type="submit" variant="primary" disabled={state === "sending"}>
        {state === "sending" ? t("submitting") : t("submit")}
      </Button>

      {state === "done" ? (
        <p className="text-sm text-positive">{t("success")}</p>
      ) : null}
      {state === "error" ? <p className="text-sm text-negative">{t("error")}</p> : null}
      {state === "limited" ? (
        <p className="text-sm text-warning">{t("rateLimited")}</p>
      ) : null}
    </form>
  );
}
