import { lazy, Suspense, useCallback, useMemo, useState } from "react";
import { Toaster, toast } from "sonner";
import { planRoute } from "./api/client";
import { TripPlannerForm, type TripFormValues } from "./components/TripPlannerForm";
import { TripStats } from "./components/TripStats";
import { JourneyTimeline } from "./components/JourneyTimeline";
import { LoadingPanel } from "./components/LoadingPanel";
import { EmptyState } from "./components/EmptyState";
import { ErrorState } from "./components/ErrorState";
import { ActiveRoutePanel } from "./components/ActiveRoutePanel";
import { friendlyErrorTitle } from "./lib/format";
import { ApiError, type RoutePlanResponse } from "./types/api";

const RouteMap = lazy(async () => {
  const mod = await import("./components/RouteMap");
  return { default: mod.RouteMap };
});

type UiState = "idle" | "loading" | "ready" | "error";

function MapFallback() {
  return (
    <div
      className="flex h-full w-full items-center justify-center bg-[#cfdce6] lg:rounded-2xl"
      role="status"
      aria-label="Loading map"
    >
      <div className="rounded-xl bg-white/85 px-4 py-3 text-center text-xs text-slate-600 shadow-sm">
        Loading map…
      </div>
    </div>
  );
}

export default function App() {
  const [state, setState] = useState<UiState>("idle");
  const [plan, setPlan] = useState<RoutePlanResponse | null>(null);
  const [activeStopId, setActiveStopId] = useState<number | null>(null);
  const [lastError, setLastError] = useState<string | null>(null);
  const [lastErrorCode, setLastErrorCode] = useState<string | undefined>();

  const handleSelectStop = useCallback((stationId: number | null) => {
    setActiveStopId(stationId);
  }, []);

  const jumpToResults = useCallback(() => {
    document
      .getElementById("trip-results")
      ?.scrollIntoView({ behavior: "smooth", block: "start" });
  }, []);

  const handlePlan = useCallback(
    async (values: TripFormValues) => {
      const hadPlan = Boolean(plan);
      setState("loading");
      setLastError(null);
      setLastErrorCode(undefined);
      setActiveStopId(null);

      try {
        const result = await planRoute({
          start: values.start,
          finish: values.finish,
        });
        setPlan(result);
        setState("ready");
        toast.success("Route calculated", {
          description: `${result.trip_summary.stop_count} fuel stop${
            result.trip_summary.stop_count === 1 ? "" : "s"
          } · ${result.meta.response_time_ms.toFixed(0)} ms`,
        });
      } catch (err) {
        setState(hadPlan ? "ready" : "error");
        if (err instanceof ApiError) {
          setLastError(err.message);
          setLastErrorCode(err.code);
          toast.error(friendlyErrorTitle(err.code), {
            description: err.message,
          });
        } else {
          const message =
            err instanceof Error ? err.message : "Unexpected network error.";
          setLastError(message);
          setLastErrorCode("REQUEST_FAILED");
          toast.error("Request failed", { description: message });
        }
      }
    },
    [plan]
  );

  const resultsKey = useMemo(
    () =>
      plan ? `${plan.meta.depart_at}-${plan.trip_summary.stop_count}` : "empty",
    [plan]
  );

  const showSidebarStatus =
    state === "idle" ||
    state === "loading" ||
    (state === "error" && !plan);

  const showResults = Boolean(plan && state !== "loading");

  return (
    <div className="flex min-h-dvh flex-col">
      <Toaster
        position="top-right"
        richColors
        closeButton
        toastOptions={{ className: "font-sans" }}
      />

      <a
        href="#planner-form"
        className="sr-only focus:not-sr-only focus:absolute focus:top-2 focus:left-2 focus:z-[2000] focus:rounded-md focus:bg-fuel focus:px-3 focus:py-2 focus:text-sm focus:font-semibold focus:text-ink"
      >
        Skip to trip planner
      </a>

      <header className="relative z-20 border-b border-white/5 bg-ink/95 text-paper backdrop-blur-md">
        <div className="mx-auto flex max-w-[1600px] items-center justify-between gap-4 px-4 py-3 sm:px-6 lg:px-8">
          <div className="flex items-center gap-3">
            <div
              className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-fuel-glow to-fuel font-display text-lg font-bold text-ink shadow-[0_6px_16px_rgba(245,165,36,0.3)]"
              aria-hidden="true"
            >
              R
            </div>
            <div>
              <div className="font-display text-base font-semibold tracking-tight">
                RouteRefuel
              </div>
              <p className="text-[11px] text-mist">
                Cost-optimal fuel stops for USA routes
              </p>
            </div>
          </div>
          <p className="hidden text-right text-[11px] text-mist md:block">
            500 mi range · 10 MPG · production Django API
          </p>
        </div>
      </header>

      <main className="mx-auto flex w-full max-w-[1600px] flex-1 flex-col xl:max-w-[1720px]">
        <div className="flex flex-col lg:grid lg:h-[calc(100dvh-61px)] lg:grid-cols-[minmax(340px,400px)_1fr] lg:gap-5 lg:overflow-hidden lg:p-5 xl:grid-cols-[minmax(360px,420px)_1fr] xl:gap-6 xl:p-6">
          <section
            className="relative order-1 h-[min(38vh,300px)] min-h-[220px] w-full sm:h-[42vh] sm:min-h-[260px] lg:order-2 lg:h-auto lg:min-h-0"
            aria-label="Map"
          >
            <Suspense fallback={<MapFallback />}>
              <RouteMap
                plan={plan}
                activeStopId={activeStopId}
                onSelectStop={handleSelectStop}
                isLoading={state === "loading"}
              />
            </Suspense>
          </section>

          <aside
            className="order-2 z-10 -mt-4 flex flex-col gap-3 px-3 pt-2 sm:px-4 lg:order-1 lg:mt-0 lg:grid lg:h-full lg:min-h-0 lg:grid-rows-[auto_minmax(0,1fr)] lg:gap-3 lg:overflow-hidden lg:p-0"
            aria-label="Trip planner"
          >
            <div className="sheet-handle lg:hidden" aria-hidden="true" />

            <section
              id="planner-form"
              className="panel-surface shrink-0 p-4 text-paper"
            >
              <div className="mb-2.5">
                <h1 className="font-display text-lg font-semibold tracking-tight sm:text-xl">
                  Plan a trip
                </h1>
                <p className="mt-1 text-xs leading-relaxed text-mist">
                  USA start and finish — cost-optimal stops along the corridor.
                </p>
              </div>
              <TripPlannerForm
                disabled={state === "loading"}
                onSubmit={handlePlan}
              />
            </section>

            {showSidebarStatus ? (
              <section className="panel-surface min-h-0 overflow-y-auto p-4 text-paper lg:h-full">
                {state === "loading" ? <LoadingPanel /> : null}
                {state === "idle" ? <EmptyState /> : null}
                {state === "error" && !plan ? (
                  <ErrorState
                    message={lastError ?? "Check your locations and try again."}
                    code={lastErrorCode}
                  />
                ) : null}
              </section>
            ) : null}

            {showResults && plan ? (
              <section className="panel-surface flex h-full min-h-0 flex-col overflow-hidden p-4 text-paper">
                <ActiveRoutePanel
                  plan={plan}
                  onJumpToResults={jumpToResults}
                />
              </section>
            ) : null}
          </aside>
        </div>

        {showResults && plan ? (
          <section
            key={resultsKey}
            id="trip-results"
            className="w-full px-3 pb-[max(1.25rem,env(safe-area-inset-bottom))] sm:px-4 lg:px-5 lg:pb-6 xl:px-6"
            aria-label="Trip results"
          >
            <div className="panel-surface space-y-6 p-4 text-paper sm:p-5 lg:p-6">
              <TripStats
                route={plan.route_summary}
                trip={plan.trip_summary}
                meta={plan.meta}
                layout="wide"
              />
              <JourneyTimeline
                route={plan.route_summary}
                stops={plan.fuel_stops}
                activeStopId={activeStopId}
                onSelectStop={handleSelectStop}
                layout="wide"
              />
            </div>
          </section>
        ) : null}
      </main>
    </div>
  );
}
