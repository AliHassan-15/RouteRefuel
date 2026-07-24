import { useEffect, useMemo, useState } from "react";
import {
  MapContainer,
  TileLayer,
  Polyline,
  Marker,
  Popup,
  useMap,
} from "react-leaflet";
import L from "leaflet";
import type { FuelStop, RoutePlanResponse } from "../types/api";
import { formatUsd } from "../lib/format";

/** Contiguous USA — first impression for reviewers (not world/continent zoom). */
const USA_BOUNDS = L.latLngBounds(
  [24.4, -124.8], // SW (S. California / Florida keys band)
  [49.0, -66.9] // NE (Maine / northern border)
);

interface RouteMapProps {
  plan: RoutePlanResponse | null;
  activeStopId: number | null;
  onSelectStop: (stationId: number | null) => void;
  isLoading?: boolean;
}

function pinIcon(
  kind: "start" | "finish" | "stop",
  label: string,
  active = false,
  delayMs = 0
) {
  const cls = `marker-pin ${kind}${active ? " active" : ""}`;
  return L.divIcon({
    className: "",
    html: `<div class="${cls}" style="--delay:${delayMs}ms">${label}</div>`,
    iconSize: [32, 32],
    iconAnchor: [16, 16],
    popupAnchor: [0, -16],
  });
}

function UsaDefaultView({ enabled }: { enabled: boolean }) {
  const map = useMap();
  useEffect(() => {
    if (!enabled) return;

    const frameUsa = () => {
      map.invalidateSize();
      const size = map.getSize();
      // Landscape map panels: composed mid-CONUS frame (fitBounds leaves ocean gutters).
      // Portrait / short maps: slightly tighter zoom so Canada/Mexico/ocean don't dominate.
      if (size.x >= 720) {
        map.setView([38.6, -96.5], 6, { animate: false });
      } else if (size.x >= 480) {
        map.setView([39.0, -97.0], 5.25, { animate: false });
      } else {
        map.setView([39.5, -97.5], 4.6, { animate: false });
      }
    };

    map.whenReady(frameUsa);
    const t = window.setTimeout(frameUsa, 100);
    map.on("resize", frameUsa);
    return () => {
      window.clearTimeout(t);
      map.off("resize", frameUsa);
    };
  }, [map, enabled]);
  return null;
}

function FitRoute({ positions }: { positions: [number, number][] }) {
  const map = useMap();
  useEffect(() => {
    if (positions.length < 2) return;
    const bounds = L.latLngBounds(positions);
    const size = map.getSize();
    const pad = size.x < 480 ? 36 : 56;
    map.fitBounds(bounds, { padding: [pad, pad], maxZoom: 11, animate: true });
  }, [map, positions]);
  return null;
}

function AnimatedPolyline({ positions }: { positions: [number, number][] }) {
  const [drawn, setDrawn] = useState<[number, number][]>([]);
  const reduceMotion =
    typeof window !== "undefined" &&
    window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  useEffect(() => {
    if (positions.length < 2) {
      setDrawn([]);
      return;
    }
    if (reduceMotion) {
      setDrawn(positions);
      return;
    }
    setDrawn(positions.slice(0, 2));
    const frames = Math.min(72, positions.length);
    const chunk = Math.max(1, Math.ceil(positions.length / frames));
    let i = 2;
    const id = window.setInterval(() => {
      i = Math.min(positions.length, i + chunk);
      setDrawn(positions.slice(0, i));
      if (i >= positions.length) window.clearInterval(id);
    }, 18);
    return () => window.clearInterval(id);
  }, [positions, reduceMotion]);

  if (drawn.length < 2) return null;

  return (
    <Polyline
      positions={drawn}
      pathOptions={{
        color: "#0F2A3D",
        weight: 5,
        opacity: 0.92,
        lineCap: "round",
        lineJoin: "round",
      }}
    />
  );
}

function StopMarker({
  stop,
  active,
  delayMs,
  onSelect,
}: {
  stop: FuelStop;
  active: boolean;
  delayMs: number;
  onSelect: () => void;
}) {
  const icon = useMemo(
    () => pinIcon("stop", String(stop.sequence), active, delayMs),
    [stop.sequence, active, delayMs]
  );

  return (
    <Marker
      position={[stop.latitude, stop.longitude]}
      icon={icon}
      eventHandlers={{ click: onSelect }}
      keyboard
      title={`Stop ${stop.sequence}: ${stop.name}`}
      alt={`Fuel stop ${stop.sequence}`}
    >
      <Popup>
        <div className="min-w-[180px] p-0.5 text-sm">
          <div className="font-semibold text-ink">{stop.name}</div>
          <div className="text-xs text-slate-600">
            {stop.city}, {stop.state}
          </div>
          <div className="mt-2 space-y-0.5 font-mono text-xs text-ink">
            <div>{formatUsd(stop.price_per_gallon)} / gal</div>
            <div>Stop cost {formatUsd(stop.cost_usd)}</div>
          </div>
        </div>
      </Popup>
    </Marker>
  );
}

function MapLegend() {
  return (
    <div
      className="pointer-events-none absolute inset-x-3 bottom-3 z-[600] sm:inset-x-4 sm:bottom-4"
      aria-hidden="true"
    >
      <div className="flex flex-wrap items-center gap-2 rounded-xl border border-ink/10 bg-ink/88 px-3 py-2 text-[11px] text-mist-bright shadow-[var(--shadow-float)] backdrop-blur-md sm:gap-3 sm:px-3.5 sm:py-2.5 sm:text-xs">
        <span className="font-semibold tracking-wide text-paper uppercase">
          Legend
        </span>
        <span className="inline-flex items-center gap-1.5">
          <span className="marker-pin start !h-5 !w-5 !animate-none !opacity-100 !text-[10px]">
            S
          </span>
          Start
        </span>
        <span className="inline-flex items-center gap-1.5">
          <span className="marker-pin stop !h-5 !w-5 !animate-none !opacity-100 !text-[10px]">
            1
          </span>
          Fuel stop
        </span>
        <span className="inline-flex items-center gap-1.5">
          <span className="marker-pin finish !h-5 !w-5 !animate-none !opacity-100 !text-[10px]">
            F
          </span>
          Finish
        </span>
        <span className="ml-auto hidden font-mono text-[10px] text-mist sm:inline">
          OSM · OSRM corridor
        </span>
      </div>
    </div>
  );
}

function EmptyMapOverlay() {
  return (
    <div className="pointer-events-none absolute inset-0 z-[500] flex items-end justify-center p-2.5 sm:items-center sm:p-6">
      <div className="animate-fade-up mb-12 w-full max-w-md rounded-2xl border border-white/55 bg-white/92 p-3 shadow-[var(--shadow-float)] backdrop-blur-md sm:mb-0 sm:p-5">
        <p className="text-[10px] font-semibold tracking-[0.14em] text-fuel-deep uppercase">
          Continental USA
        </p>
        <h2 className="font-display mt-0.5 text-base font-semibold text-ink sm:mt-1 sm:text-xl">
          Your corridor appears here
        </h2>
        <p className="mt-1 text-[11px] leading-relaxed text-slate-600 sm:mt-1.5 sm:text-[13px]">
          Calculate a route to draw the live path and numbered fuel stops.
        </p>
        <div className="mt-2.5 grid grid-cols-3 gap-1.5 sm:mt-3 sm:gap-2">
          {[
            ["Path", "OSRM polyline"],
            ["Stops", "Cost-ranked"],
            ["Fit", "Auto-bounds"],
          ].map(([k, v]) => (
            <div
              key={k}
              className="rounded-lg border border-slate-200 bg-slate-50 px-1.5 py-1.5 sm:px-2 sm:py-2"
            >
              <div className="text-[9px] font-semibold tracking-wide text-slate-500 uppercase sm:text-[10px]">
                {k}
              </div>
              <div className="mt-0.5 text-[10px] font-semibold text-ink sm:text-xs">
                {v}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export function RouteMap({
  plan,
  activeStopId,
  onSelectStop,
  isLoading = false,
}: RouteMapProps) {
  const positions = plan?.coordinates ?? [];
  const startIcon = useMemo(() => pinIcon("start", "S", false, 120), []);
  const finishIcon = useMemo(
    () =>
      pinIcon("finish", "F", false, 180 + (plan?.fuel_stops.length ?? 0) * 55),
    [plan?.fuel_stops.length]
  );

  return (
    <div
      className="relative h-full w-full overflow-hidden bg-[#cfdce6] lg:rounded-2xl lg:border lg:border-slate-line/30 lg:shadow-[var(--shadow-float)]"
      role="region"
      aria-label="Interactive route map"
    >
      {isLoading ? (
        <div className="pointer-events-none absolute inset-x-0 top-0 z-[1000] bg-gradient-to-b from-ink/80 via-ink/40 to-transparent px-4 py-3.5">
          <p className="text-xs font-semibold text-paper sm:text-sm">
            Drawing live route geometry…
          </p>
          <p className="text-[11px] text-mist">
            Fitting bounds after OSRM returns the corridor
          </p>
        </div>
      ) : null}

      <MapContainer
        center={[38.6, -96.5]}
        zoom={6}
        minZoom={3.5}
        className="h-full w-full"
        scrollWheelZoom
        maxBounds={USA_BOUNDS.pad(0.15)}
        maxBoundsViscosity={0.9}
        aria-label="OpenStreetMap route view"
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        <UsaDefaultView enabled={!plan} />

        {positions.length >= 2 ? (
          <>
            <FitRoute positions={positions} />
            <AnimatedPolyline positions={positions} />
          </>
        ) : null}

        {plan ? (
          <>
            <Marker
              position={[
                plan.route_summary.start.latitude,
                plan.route_summary.start.longitude,
              ]}
              icon={startIcon}
              title="Start"
              alt="Trip start"
            >
              <Popup>
                <strong>Start</strong>
                <div className="text-xs">{plan.route_summary.start.address}</div>
              </Popup>
            </Marker>

            <Marker
              position={[
                plan.route_summary.finish.latitude,
                plan.route_summary.finish.longitude,
              ]}
              icon={finishIcon}
              title="Finish"
              alt="Trip finish"
            >
              <Popup>
                <strong>Finish</strong>
                <div className="text-xs">{plan.route_summary.finish.address}</div>
              </Popup>
            </Marker>

            {plan.fuel_stops.map((stop, index) => (
              <StopMarker
                key={stop.station_id}
                stop={stop}
                active={activeStopId === stop.station_id}
                delayMs={200 + index * 55}
                onSelect={() =>
                  onSelectStop(
                    activeStopId === stop.station_id ? null : stop.station_id
                  )
                }
              />
            ))}
          </>
        ) : null}
      </MapContainer>

      {!plan && !isLoading ? <EmptyMapOverlay /> : null}
      <MapLegend />
    </div>
  );
}
