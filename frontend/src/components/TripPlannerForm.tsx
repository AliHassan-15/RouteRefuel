import { useState } from "react";
import type { FormEvent } from "react";
import { PlaceAutocomplete } from "./PlaceAutocomplete";

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
      <PlaceAutocomplete
        id="start"
        name="start"
        label="Start"
        value={start}
        disabled={disabled}
        placeholder="Start typing a USA city…"
        error={errors.start}
        onChange={(value) => {
          setStart(value);
          if (errors.start) setErrors((prev) => ({ ...prev, start: undefined }));
        }}
      />

      <PlaceAutocomplete
        id="finish"
        name="finish"
        label="Finish"
        value={finish}
        disabled={disabled}
        placeholder="Start typing a USA city…"
        error={errors.finish}
        onChange={(value) => {
          setFinish(value);
          if (errors.finish)
            setErrors((prev) => ({ ...prev, finish: undefined }));
        }}
      />

      <p className="text-[11px] leading-relaxed text-mist">
        USA only · type to search cities · 500 mi tank · 10 MPG
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
