import { memo, useMemo } from "react";
import type { TripSummary, RouteSummary, RoutePlanMeta } from "../types/api";
import {
  formatDurationHours,
  formatGallons,
  formatMiles,
  formatUsd,
} from "../lib/format";

interface TripStatsProps {
  route: RouteSummary;
  trip: TripSummary;
  meta?: RoutePlanMeta;
  layout?: "compact" | "wide";
}

function TripStatsComponent({
  route,
  trip,
  meta,
  layout = "compact",
}: TripStatsProps) {
  const tiles = useMemo(
    () => [
      {
        label: "Fuel cost",
        value: formatUsd(trip.total_fuel_cost_usd),
        accent: true,
        hero: true,
      },
      {
        label: "Distance",
        value: formatMiles(route.distance_miles, 0),
        accent: false,
        hero: true,
      },
      {
        label: "Drive time",
        value: formatDurationHours(route.duration_hours),
        accent: false,
        hero: false,
      },
      {
        label: "Gallons",
        value: formatGallons(trip.total_gallons_used),
        accent: false,
        hero: false,
      },
      {
        label: "Stops",
        value: String(trip.stop_count),
        accent: false,
        hero: false,
      },
      {
        label: "Avg $/gal",
        value:
          trip.stop_count > 0 ? formatUsd(trip.average_price_per_gallon_usd) : "—",
        accent: false,
        hero: false,
      },
    ],
    [route, trip]
  );

  if (layout === "wide") {
    return (
      <div className="animate-fade-up space-y-3" aria-label="Trip summary">
        <div className="flex flex-wrap items-end justify-between gap-2 border-b border-white/5 pb-3">
          <div>
            <h2 className="font-display text-base font-semibold text-paper">
              Trip summary
            </h2>
            <p className="mt-0.5 text-[11px] text-mist">
              Cost-optimal plan for this corridor
            </p>
          </div>
          {meta ? (
            <p className="font-mono text-[11px] text-mist">
              {meta.response_time_ms.toFixed(0)} ms ·{" "}
              {meta.external_calls.total} external call
              {meta.external_calls.total === 1 ? "" : "s"}
            </p>
          ) : null}
        </div>

        <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-6">
          {tiles.map((item) => (
            <div
              key={item.label}
              className={`elevated-inset flex h-full flex-col justify-between px-3 py-3 ${
                item.accent ? "ring-1 ring-fuel/30" : ""
              }`}
            >
              <div className="text-[10px] font-semibold tracking-[0.12em] text-mist uppercase">
                {item.label}
              </div>
              <div
                className={`mt-2 leading-none font-semibold tracking-tight tabular-nums ${
                  item.hero
                    ? "font-display text-2xl"
                    : "font-mono text-lg sm:text-xl"
                } ${item.accent ? "text-fuel" : "text-paper"}`}
              >
                {item.value}
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  const heroes = tiles.filter((t) => t.hero);
  const secondary = tiles.filter((t) => !t.hero);

  return (
    <div className="animate-fade-up space-y-2" aria-label="Trip summary">
      <div className="grid grid-cols-2 gap-2">
        {heroes.map((item) => (
          <div
            key={item.label}
            className={`elevated-inset px-3 py-2.5 ${
              item.accent ? "ring-1 ring-fuel/30" : ""
            }`}
          >
            <div className="text-[10px] font-semibold tracking-[0.12em] text-mist uppercase">
              {item.label}
            </div>
            <div
              className={`font-display mt-0.5 text-2xl leading-none font-semibold tracking-tight sm:text-[1.75rem] ${
                item.accent ? "text-fuel" : "text-paper"
              }`}
            >
              {item.value}
            </div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
        {secondary.map((item) => (
          <div key={item.label} className="elevated-inset px-2.5 py-2">
            <div className="text-[10px] font-semibold tracking-[0.12em] text-mist uppercase">
              {item.label}
            </div>
            <div className="mt-0.5 font-mono text-sm font-semibold text-paper">
              {item.value}
            </div>
          </div>
        ))}
      </div>

      {meta ? (
        <p className="text-[11px] text-mist">
          Planned in{" "}
          <span className="font-mono text-mist-bright">
            {meta.response_time_ms.toFixed(0)} ms
          </span>{" "}
          · {meta.external_calls.total} external API call
          {meta.external_calls.total === 1 ? "" : "s"}
        </p>
      ) : null}
    </div>
  );
}

export const TripStats = memo(TripStatsComponent);
