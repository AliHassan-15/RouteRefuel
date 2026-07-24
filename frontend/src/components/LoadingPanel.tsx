import { useEffect, useState } from "react";

const STEPS = [
  "Resolving start & finish",
  "Fetching driving route",
  "Scoring fuel stops locally",
] as const;

export function LoadingPanel() {
  const [activeStep, setActiveStep] = useState(0);

  useEffect(() => {
    const id = window.setInterval(() => {
      setActiveStep((prev) => (prev + 1) % STEPS.length);
    }, 900);
    return () => window.clearInterval(id);
  }, []);

  return (
    <div
      className="animate-fade-up flex min-h-[300px] flex-col gap-4 lg:min-h-[380px]"
      aria-live="polite"
      aria-busy="true"
      role="status"
    >
      <div className="flex items-start gap-3">
        <div className="loading-orb shrink-0" aria-hidden="true" />
        <div>
          <div className="font-display text-lg font-semibold text-paper">
            Building your fuel plan
          </div>
          <p className="mt-1 text-xs leading-relaxed text-mist sm:text-[13px]">
            Geocoding endpoints, one routing call, then local optimization —
            no per-stop map API calls.
          </p>
        </div>
      </div>

      <ol className="space-y-1.5" aria-label="Planning progress">
        {STEPS.map((step, index) => {
          const isActive = index === activeStep;
          const isDone = index < activeStep;
          return (
            <li
              key={step}
              className={`elevated-inset flex items-center gap-2.5 px-3 py-2.5 text-xs transition-colors ${
                isActive
                  ? "ring-1 ring-fuel/35 text-paper"
                  : isDone
                    ? "text-mist-bright"
                    : "text-mist/70"
              }`}
            >
              <span
                className={`h-2 w-2 rounded-full ${
                  isActive
                    ? "bg-fuel shadow-[0_0_0_4px_rgba(245,165,36,0.2)]"
                    : isDone
                      ? "bg-go"
                      : "bg-slate-line"
                }`}
                aria-hidden="true"
              />
              <span className={isActive ? "font-semibold" : ""}>{step}</span>
            </li>
          );
        })}
      </ol>

      <div className="grid grid-cols-3 gap-2" aria-hidden="true">
        <div className="skeleton h-16" />
        <div className="skeleton h-16" />
        <div className="skeleton h-16" />
      </div>
      <div className="mt-auto space-y-2" aria-hidden="true">
        <div className="skeleton h-14" />
        <div className="skeleton h-14" />
        <div className="skeleton h-14" />
      </div>
    </div>
  );
}
