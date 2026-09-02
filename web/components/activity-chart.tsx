"use client";

import { useTranslations } from "next-intl";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import type { StoreActivityPoint } from "@/lib/types";

/**
 * Katalog aktivitesi grafigi: eklenen / cikan urun ve fiyat degisimi.
 * BU SATIS GRAFIGI DEGILDIR ve oyle yorumlanacak bir seri eklenmez.
 */
export function ActivityChart({ data }: { data: StoreActivityPoint[] }) {
  const t = useTranslations("stores");

  const series = data.map((d) => ({
    date: d.date.slice(5),
    new: d.new_products,
    removed: -d.removed_products,
    changes: d.price_changes,
  }));

  return (
    <div>
      <div className="h-56 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={series} margin={{ top: 4, right: 4, bottom: 0, left: -24 }}>
            <CartesianGrid stroke="#232a35" vertical={false} />
            <XAxis
              dataKey="date"
              tick={{ fill: "#5d6675", fontSize: 10 }}
              tickLine={false}
              axisLine={{ stroke: "#232a35" }}
              minTickGap={16}
            />
            <YAxis
              tick={{ fill: "#5d6675", fontSize: 10 }}
              tickLine={false}
              axisLine={false}
              width={44}
            />
            <Tooltip
              contentStyle={{
                background: "#11141a",
                border: "1px solid #232a35",
                borderRadius: 8,
                fontSize: 12,
              }}
              labelStyle={{ color: "#8b94a3" }}
              formatter={(value, name) => [Math.abs(Number(value ?? 0)), String(name ?? "")]}
            />
            <Legend wrapperStyle={{ fontSize: 11, color: "#8b94a3" }} />
            <Bar dataKey="new" name="+ new" fill="#3fb950" radius={[2, 2, 0, 0]} />
            <Bar dataKey="removed" name="− removed" fill="#f85149" radius={[0, 0, 2, 2]} />
            <Bar dataKey="changes" name="price changes" fill="#4c8dff" radius={[2, 2, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
      <p className="mt-2 text-[11px] leading-4 text-faint">{t("activityNote")}</p>
    </div>
  );
}
