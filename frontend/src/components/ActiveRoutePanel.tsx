import { formatMiles, formatUsd } from "../lib/format";
import type { RoutePlanResponse } from "../types/api";

interface ActiveRoutePanelProps {
  plan: RoutePlanResponse;
  onJumpToResults?: () => void;
}

const GUIDE = [
  {
    title: "Map markers",
    body: "Green S is start, amber numbers are fuel stops, dark F is finish. Click a stop in the journey list to highlight it on the map.",
  },
  {
    title: "Why these stops",
    body: "Each stop is the cheapest station still reachable within the remaining 500-mile tank — not the nearest pump.",
  },
  {
    title: "Verify the math",
    body: "Gallons × $/gal at every stop rolls up to the trip fuel cost. Σ in the journey header should match.",
  },
] as const;

export function ActiveRoutePanel({
  plan,
  onJumpToResults,
}: ActiveRoutePanelProps) {
  const { route_summary: route, trip_summary: trip, meta } = plan;

  return (
    <div
      className="animate-fade-up flex h-full min-h-0 flex-col"
      aria-labelledby="active-route-heading"
    >
      <div className="min-h-0 flex-1 space-y-3 overflow-y-auto pr-0.5">
        <div>
          <p className="mb-1.5 text-[11px] font-semibold tracking-[0.14em] text-fuel uppercase">
            Route live
          </p>
          <h2
            id="active-route-heading"
            className="font-display text-[1.2rem] leading-snug font-semibold text-paper"
          >
            {route.start.query}
            <span className="mx-1.5 text-mist">→</span>
            {route.finish.query}
          </h2>
          <p className="mt-1.5 text-xs leading-relaxed text-mist">
            Corridor is on the map. Full stats and the stop-by-stop journey sit
            in the results band below — scroll down to audit every dollar.
          </p>
        </div>

        <div className="grid grid-cols-3 gap-2">
          <div className="elevated-inset px-2.5 py-2">
            <div className="text-[10px] font-semibold tracking-wide text-mist uppercase">
              Cost
            </div>
            <div className="mt-0.5 font-display text-lg leading-none font-semibold text-fuel">
              {formatUsd(trip.total_fuel_cost_usd)}
            </div>
          </div>
          <div className="elevated-inset px-2.5 py-2">
            <div className="text-[10px] font-semibold tracking-wide text-mist uppercase">
              Miles
            </div>
            <div className="mt-0.5 font-mono text-lg leading-none font-semibold text-paper">
              {formatMiles(route.distance_miles, 0)}
            </div>
          </div>
          <div className="elevated-inset px-2.5 py-2">
            <div className="text-[10px] font-semibold tracking-wide text-mist uppercase">
              Stops
            </div>
            <div className="mt-0.5 font-mono text-lg leading-none font-semibold text-paper">
              {trip.stop_count}
            </div>
          </div>
        </div>

        <ul className="space-y-2" role="list">
          {GUIDE.map((item, index) => (
            <li
              key={item.title}
              className={`elevated-inset flex gap-2.5 px-3 py-2.5 stagger-${index + 1}`}
            >
              <span
                className="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-fuel/15 font-mono text-[10px] font-semibold text-fuel"
                aria-hidden="true"
              >
                {index + 1}
              </span>
              <div className="min-w-0">
                <div className="text-sm font-semibold text-paper">
                  {item.title}
                </div>
                <div className="text-xs leading-relaxed text-mist">
                  {item.body}
                </div>
              </div>
            </li>
          ))}
        </ul>

        <div className="elevated-inset space-y-2 px-3 py-2.5">
          <p className="text-[11px] font-semibold tracking-[0.12em] text-mist uppercase">
            How this plan was built
          </p>
          <p className="text-xs leading-relaxed text-mist">
            One OSRM drive path, local station search along a 25-mile corridor,
            then greedy cheapest-in-range selection. No per-stop map API calls —
            prices come from the assessment CSV already on the server.
          </p>
        </div>
      </div>

      <div className="mt-3 shrink-0 space-y-2 border-t border-white/5 pt-3">
        <div className="elevated-inset grid grid-cols-3 gap-2 px-3 py-2.5">
          {[
            ["Range", "500 mi"],
            ["MPG", "10"],
            ["Corridor", "25 mi"],
          ].map(([label, value]) => (
            <div key={label}>
              <div className="text-[10px] font-semibold tracking-wide text-mist uppercase">
                {label}
              </div>
              <div className="mt-0.5 font-mono text-sm font-semibold text-paper">
                {value}
              </div>
            </div>
          ))}
        </div>
        <p className="text-[11px] text-mist">
          Planned in{" "}
          <span className="font-mono text-mist-bright">
            {meta.response_time_ms.toFixed(0)} ms
          </span>{" "}
          · {meta.external_calls.total} external call
          {meta.external_calls.total === 1 ? "" : "s"}
        </p>
        {onJumpToResults ? (
          <button
            type="button"
            onClick={onJumpToResults}
            className="w-full rounded-lg border border-slate-line bg-slate-elevated/80 px-3 py-2.5 text-left text-xs font-semibold text-mist-bright transition hover:border-fuel/40 hover:text-paper"
          >
            View full journey &amp; cost breakdown ↓
          </button>
        ) : null}
      </div>
    </div>
  );
}
