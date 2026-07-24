import { useState } from "react";
import type { FormEvent } from "react";

export interface TripFormValues {
  start: string;
  finish: string;
}

interface TripPlannerFormProps {
  disabled?: boolean;
  initial?: TripFormValues;
  onSubmit: (values: TripFormValues) => void;
}

export function TripPlannerForm({
  disabled = false,
  initial,
  onSubmit,
}: TripPlannerFormProps) {
  const [start, setStart] = useState(initial?.start ?? "Chicago, IL");
  const [finish, setFinish] = useState(initial?.finish ?? "Dallas, TX");
  const [errors, setErrors] = useState<{ start?: string; finish?: string }>({});

  function validate(): boolean {
    const next: { start?: string; finish?: string } = {};
    if (start.trim().length < 2) {
      next.start = "Enter a USA city or address (e.g. Chicago, IL).";
    }
    if (finish.trim().length < 2) {
      next.finish = "Enter a USA destination (e.g. Dallas, TX).";
    }
    if (
      start.trim().length >= 2 &&
      finish.trim().length >= 2 &&
      start.trim().toLowerCase() === finish.trim().toLowerCase()
    ) {
      next.finish = "Finish must be different from start.";
    }
    setErrors(next);
    return Object.keys(next).length === 0;
  }

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (!validate()) return;
    onSubmit({ start: start.trim(), finish: finish.trim() });
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4" noValidate>
      <div>
        <label
          htmlFor="start"
          className="mb-1.5 block text-[11px] font-semibold tracking-[0.12em] text-mist uppercase"
        >
          Start
        </label>
        <input
          id="start"
          name="start"
          value={start}
          disabled={disabled}
          onChange={(e) => {
            setStart(e.target.value);
            if (errors.start) setErrors((prev) => ({ ...prev, start: undefined }));
          }}
          placeholder="Chicago, IL"
          autoComplete="address-level2"
          className="field-input text-base sm:text-sm"
          aria-invalid={Boolean(errors.start)}
          aria-describedby={errors.start ? "start-error" : "start-hint"}
        />
        {errors.start ? (
          <p id="start-error" className="mt-1.5 text-xs text-danger-soft" role="alert">
            {errors.start}
          </p>
        ) : (
          <p id="start-hint" className="sr-only">
            USA city or full address
          </p>
        )}
      </div>

      <div>
        <label
          htmlFor="finish"
          className="mb-1.5 block text-[11px] font-semibold tracking-[0.12em] text-mist uppercase"
        >
          Finish
        </label>
        <input
          id="finish"
          name="finish"
          value={finish}
          disabled={disabled}
          onChange={(e) => {
            setFinish(e.target.value);
            if (errors.finish) setErrors((prev) => ({ ...prev, finish: undefined }));
          }}
          placeholder="Dallas, TX"
          autoComplete="address-level2"
          className="field-input text-base sm:text-sm"
          aria-invalid={Boolean(errors.finish)}
          aria-describedby={errors.finish ? "finish-error" : undefined}
        />
        {errors.finish ? (
          <p id="finish-error" className="mt-1.5 text-xs text-danger-soft" role="alert">
            {errors.finish}
          </p>
        ) : null}
      </div>

      <p className="text-[11px] leading-relaxed text-mist">
        USA only · 500 mi tank · 10 MPG assumptions
      </p>

      <button
        type="submit"
        disabled={disabled}
        className="btn-primary w-full px-4 py-3 text-sm"
        aria-busy={disabled}
      >
        {disabled ? "Calculating route…" : "Calculate fuel route"}
      </button>
    </form>
  );
}
