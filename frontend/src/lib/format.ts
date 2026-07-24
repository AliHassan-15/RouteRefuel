export function formatUsd(value: number): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
  }).format(value);
}

export function formatMiles(value: number, digits = 1): string {
  return `${value.toFixed(digits)} mi`;
}

export function formatGallons(value: number): string {
  return `${value.toFixed(2)} gal`;
}

export function formatDurationHours(hours: number): string {
  const totalMinutes = Math.round(hours * 60);
  const h = Math.floor(totalMinutes / 60);
  const m = totalMinutes % 60;
  if (h === 0) return `${m}m`;
  if (m === 0) return `${h}h`;
  return `${h}h ${m}m`;
}

export function formatEta(iso: string): string {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return iso;
  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
    timeZoneName: "short",
  }).format(date);
}

export function friendlyErrorTitle(code: string): string {
  switch (code) {
    case "GEOCODE_FAILED":
      return "Location not found";
    case "LOCATION_NOT_IN_USA":
      return "USA locations only";
    case "NO_DRIVING_ROUTE":
      return "No driving route";
    case "NO_FEASIBLE_FUEL_PLAN":
      return "No viable fuel plan";
    case "ROUTING_UNAVAILABLE":
    case "GEOCODING_UNAVAILABLE":
      return "Service temporarily unavailable";
    case "RATE_LIMITED":
      return "Too many requests";
    case "STATIONS_NOT_READY":
      return "Fuel data not loaded";
    case "VALIDATION_ERROR":
      return "Check your inputs";
    default:
      return "Something went wrong";
  }
}
