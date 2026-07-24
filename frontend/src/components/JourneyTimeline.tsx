import { memo, useMemo } from "react";
import type { FuelStop, Place, RouteSummary } from "../types/api";
import {
  formatEta,
  formatGallons,
  formatMiles,
  formatUsd,
} from "../lib/format";

interface JourneyTimelineProps {
  route: RouteSummary;
  stops: FuelStop[];
  activeStopId: number | null;
  onSelectStop: (stationId: number | null) => void;
  layout?: "compact" | "wide";
}

/** Shared wide-row grid — keeps every journey row column-aligned. */
const WIDE_ROW =
  "grid w-full items-center gap-x-4 gap-y-1 px-3.5 py-3 " +
  "grid-cols-[2.25rem_minmax(0,1fr)_auto] " +
  "sm:grid-cols-[2.25rem_minmax(12rem,1.8fr)_minmax(9rem,0.85fr)_auto] " +
  "md:grid-cols-[2.25rem_minmax(13rem,1.9fr)_minmax(9rem,0.85fr)_5rem_auto] " +
  "lg:grid-cols-[2.25rem_minmax(14rem,2fr)_minmax(9.5rem,0.9fr)_5rem_7.75rem_4.75rem]";

function PlaceNode({
  kind,
  title,
  subtitle,
  delayClass,
  layout,
}: {
  kind: "start" | "finish";
  title: string;
  subtitle: string;
  delayClass?: string;
  layout: "compact" | "wide";
}) {
  const badge =
    kind === "start"
      ? "bg-go text-white"
      : "bg-ink text-white ring-1 ring-slate-line";

  if (layout === "wide") {
    return (
      <div
        className={`animate-fade-up elevated-inset ${WIDE_ROW} ${delayClass ?? ""}`}
      >
        <div
          className={`flex h-9 w-9 items-center justify-center rounded-full text-xs font-bold ${badge}`}
          aria-hidden="true"
        >
          {kind === "start" ? "S" : "F"}
        </div>
        <div className="min-w-0">
          <div className="text-[10px] font-semibold tracking-[0.12em] text-mist uppercase">
            {kind === "start" ? "Start" : "Finish"}
          </div>
          <div className="truncate text-sm font-semibold text-paper">{title}</div>
        </div>
        <div className="col-span-1 min-w-0 text-xs leading-relaxed text-mist sm:col-span-1 md:col-span-2 lg:col-span-3">
          {subtitle}
        </div>
        <div className="hidden lg:block" aria-hidden="true" />
      </div>
    );
  }

  return (
    <div className={`animate-fade-up flex gap-3 ${delayClass ?? ""}`}>
      <div className="flex w-8 flex-col items-center" aria-hidden="true">
        <div
          className={`flex h-8 w-8 items-center justify-center rounded-full text-xs font-bold ${badge}`}
        >
          {kind === "start" ? "S" : "F"}
        </div>
      </div>
      <div className="min-w-0 flex-1 pb-5">
        <div className="text-[10px] font-semibold tracking-[0.12em] text-mist uppercase">
          {kind === "start" ? "Start" : "Finish"}
        </div>
        <div className="truncate text-sm font-semibold text-paper">{title}</div>
        <div className="mt-0.5 line-clamp-2 text-xs text-mist">{subtitle}</div>
      </div>
    </div>
  );
}

function StopNode({
  stop,
  active,
  isLast,
  index,
  onSelect,
  layout,
}: {
  stop: FuelStop;
  active: boolean;
  isLast: boolean;
  index: number;
  onSelect: () => void;
  layout: "compact" | "wide";
}) {
  const priceLine = useMemo(
    () =>
      `${formatUsd(stop.price_per_gallon)}/gal × ${formatGallons(stop.gallons_purchased)}`,
    [stop.price_per_gallon, stop.gallons_purchased]
  );

  if (layout === "wide") {
    return (
      <button
        type="button"
        onClick={onSelect}
        aria-pressed={active}
        aria-label={`Fuel stop ${stop.sequence}: ${stop.name}, ${formatUsd(stop.cost_usd)}`}
        className={`animate-fade-up interactive-lift elevated-inset min-h-[56px] text-left focus-visible:outline-offset-2 ${WIDE_ROW} ${
          active ? "ring-1 ring-fuel/45" : ""
        }`}
        style={{ animationDelay: `${120 + index * 55}ms` }}
      >
        <div
          className="flex h-9 w-9 items-center justify-center rounded-full bg-fuel-deep text-xs font-bold text-white shadow-[0_4px_12px_rgba(224,142,18,0.35)]"
          aria-hidden="true"
        >
          {stop.sequence}
        </div>

        <div className="min-w-0">
          <div className="truncate text-sm font-semibold text-paper">
            {stop.name}
          </div>
          <div className="truncate text-xs text-mist">
            {stop.city}, {stop.state} · {formatMiles(stop.distance_from_start_miles)}
          </div>
          <div className="mt-1 font-mono text-[11px] text-mist-bright sm:hidden">
            {priceLine}
          </div>
        </div>

        <div className="hidden min-w-0 sm:block">
          <div className="text-[10px] font-semibold tracking-wide text-mist uppercase">
            Fuel math
          </div>
          <div className="font-mono text-xs text-mist-bright">{priceLine}</div>
        </div>

        <div className="hidden md:block">
          <div className="text-[10px] font-semibold tracking-wide text-mist uppercase">
            Range in
          </div>
          <div className="font-mono text-xs text-mist-bright">
            {formatMiles(stop.remaining_range_before_refuel_miles, 0)}
          </div>
        </div>

        <div className="hidden lg:block">
          <div className="text-[10px] font-semibold tracking-wide text-mist uppercase">
            ETA
          </div>
          <div className="font-mono text-xs text-mist-bright">
            {formatEta(stop.eta)}
          </div>
        </div>

        <div className="justify-self-end text-right font-mono text-sm font-semibold text-fuel tabular-nums">
          {formatUsd(stop.cost_usd)}
        </div>
      </button>
    );
  }

  return (
    <button
      type="button"
      onClick={onSelect}
      aria-pressed={active}
      aria-label={`Fuel stop ${stop.sequence}: ${stop.name}, ${formatUsd(stop.cost_usd)}`}
      className={`animate-fade-up interactive-lift flex min-h-[44px] w-full gap-3 rounded-lg px-1 text-left focus-visible:outline-offset-2 ${
        active
          ? "bg-slate-elevated/95 ring-1 ring-fuel/45"
          : "hover:bg-slate-elevated/55"
      }`}
      style={{ animationDelay: `${120 + index * 55}ms` }}
    >
      <div className="flex w-8 flex-col items-center" aria-hidden="true">
        <div className="flex h-8 w-8 items-center justify-center rounded-full bg-fuel-deep text-xs font-bold text-white shadow-[0_4px_12px_rgba(224,142,18,0.35)]">
          {stop.sequence}
        </div>
        {!isLast ? <div className="my-1 w-px flex-1 bg-slate-line" /> : null}
      </div>
      <div className={`min-w-0 flex-1 ${isLast ? "pb-1" : "pb-5"}`}>
        <div className="flex items-start justify-between gap-2">
          <div className="min-w-0">
            <div className="truncate text-sm font-semibold text-paper">
              {stop.name}
            </div>
            <div className="text-xs text-mist">
              {stop.city}, {stop.state} · {formatMiles(stop.distance_from_start_miles)}
            </div>
          </div>
          <div className="shrink-0 font-mono text-sm font-semibold text-fuel">
            {formatUsd(stop.cost_usd)}
          </div>
        </div>
        <div className="mt-2 grid grid-cols-2 gap-x-3 gap-y-1 text-[11px] text-mist">
          <span>{priceLine}</span>
          <span className="text-right">
            Range in: {formatMiles(stop.remaining_range_before_refuel_miles, 0)}
          </span>
          <span className="col-span-2">ETA {formatEta(stop.eta)}</span>
        </div>
      </div>
    </button>
  );
}

function JourneyTimelineComponent({
  route,
  stops,
  activeStopId,
  onSelectStop,
  layout = "compact",
}: JourneyTimelineProps) {
  const start: Place = route.start;
  const finish: Place = route.finish;

  const stopCostSum = useMemo(
    () => stops.reduce((sum, s) => sum + s.cost_usd, 0),
    [stops]
  );

  const finishSubtitle = useMemo(
    () => `${finish.address} · arrive ${formatEta(route.destination_eta)}`,
    [finish.address, route.destination_eta]
  );

  return (
    <div className="animate-fade-up stagger-2" aria-label="Journey timeline">
      <div className="mb-3 flex flex-wrap items-end justify-between gap-2 border-b border-white/5 pb-3">
        <div>
          <h3 className="font-display text-base font-semibold text-paper">
            Journey
          </h3>
          <p className="mt-0.5 text-[11px] text-mist">
            Ordered corridor stops from start fill to destination
          </p>
        </div>
        {stops.length > 0 ? (
          <span className="font-mono text-xs text-mist" title="Sum of stop costs">
            Σ stops{" "}
            <span className="font-semibold text-fuel">
              {formatUsd(stopCostSum)}
            </span>
          </span>
        ) : (
          <span className="rounded-full bg-go/15 px-2 py-0.5 text-[10px] font-semibold tracking-wide text-go uppercase">
            One tank
          </span>
        )}
      </div>

      {layout === "wide" && stops.length > 0 ? (
        <div
          className={`${WIDE_ROW} mb-1.5 hidden px-3 text-[10px] font-semibold tracking-[0.12em] text-mist uppercase lg:grid`}
          aria-hidden="true"
        >
          <span />
          <span>Station</span>
          <span>Fuel math</span>
          <span>Range in</span>
          <span>ETA</span>
          <span className="justify-self-end">Cost</span>
        </div>
      ) : null}

      <div className={layout === "wide" ? "space-y-2" : "space-y-0"}>
        <PlaceNode
          kind="start"
          title={start.query}
          subtitle={start.address}
          delayClass="stagger-1"
          layout={layout}
        />

        {stops.length === 0 ? (
          <div
            className={`elevated-inset space-y-2 px-3 py-3 ${
              layout === "wide" ? "" : "mb-4 ml-0 sm:ml-11"
            }`}
          >
            <div className="text-sm font-semibold text-paper">
              No intermediate fuel stop
            </div>
            <p className="text-xs leading-relaxed text-mist sm:max-w-3xl">
              This leg fits inside the 500-mile tank. You still consume{" "}
              <span className="font-mono text-mist-bright">
                {(route.distance_miles / 10).toFixed(1)} gal
              </span>{" "}
              from the starting fill — no purchase is required on-route, so trip
              fuel cost is $0.00 under assessment rules.
            </p>
            <div className="grid max-w-md grid-cols-2 gap-2 pt-1">
              <div>
                <div className="text-[10px] font-semibold tracking-wide text-mist uppercase">
                  Tank used
                </div>
                <div className="font-mono text-sm font-semibold text-paper">
                  {((route.distance_miles / 500) * 100).toFixed(0)}%
                </div>
              </div>
              <div>
                <div className="text-[10px] font-semibold tracking-wide text-mist uppercase">
                  Range left
                </div>
                <div className="font-mono text-sm font-semibold text-paper">
                  {formatMiles(500 - route.distance_miles, 0)}
                </div>
              </div>
            </div>
          </div>
        ) : (
          <div
            className={layout === "wide" ? "space-y-2" : "space-y-0"}
            role="list"
          >
            {stops.map((stop, index) => (
              <div key={stop.station_id} role="listitem">
                <StopNode
                  stop={stop}
                  active={activeStopId === stop.station_id}
                  isLast={index === stops.length - 1}
                  index={index}
                  layout={layout}
                  onSelect={() =>
                    onSelectStop(
                      activeStopId === stop.station_id ? null : stop.station_id
                    )
                  }
                />
              </div>
            ))}
          </div>
        )}

        <PlaceNode
          kind="finish"
          title={finish.query}
          subtitle={finishSubtitle}
          delayClass="stagger-4"
          layout={layout}
        />
      </div>

      <div
        className={`mt-4 grid gap-2 ${
          layout === "wide"
            ? "grid-cols-1 border-t border-white/5 pt-4 sm:grid-cols-[minmax(0,20rem)_1fr] sm:items-end"
            : ""
        }`}
      >
        <div className="elevated-inset grid grid-cols-3 gap-2 px-3 py-2.5">
          {[
            ["Range", "500 mi"],
            ["Economy", "10 MPG"],
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
        {stops.length > 0 ? (
          <p className="text-[11px] leading-relaxed text-mist sm:text-right">
            Click a stop to highlight it on the map. Cost at each stop = gallons
            × $/gal; Σ matches trip fuel cost.
          </p>
        ) : null}
      </div>
    </div>
  );
}

export const JourneyTimeline = memo(JourneyTimelineComponent);
