import type {
  ApiErrorResponse,
  PlaceSuggestion,
  RoutePlanRequest,
  RoutePlanResponse,
} from "../types/api";
import { ApiError } from "../types/api";

export type { PlaceSuggestion };

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "";

export async function planRoute(payload: RoutePlanRequest): Promise<RoutePlanResponse> {
  const response = await fetch(`${API_BASE}/api/v1/route/`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
    },
    body: JSON.stringify(payload),
  });

  let data: unknown = null;
  try {
    data = await response.json();
  } catch {
    throw new ApiError(response.status, {
      code: "INVALID_RESPONSE",
      message: "The server returned an unreadable response. Is the API running?",
    });
  }

  if (!response.ok) {
    const err = data as ApiErrorResponse;
    if (err?.error?.code && err?.error?.message) {
      throw new ApiError(response.status, err.error);
    }
    throw new ApiError(response.status, {
      code: "REQUEST_FAILED",
      message: `Request failed with status ${response.status}.`,
    });
  }

  return data as RoutePlanResponse;
}

export async function suggestPlaces(
  query: string,
  signal?: AbortSignal
): Promise<PlaceSuggestion[]> {
  const trimmed = query.trim();
  if (trimmed.length < 1) return [];

  const params = new URLSearchParams({ q: trimmed, limit: "12" });
  const response = await fetch(
    `${API_BASE}/api/v1/places/suggest/?${params.toString()}`,
    {
      method: "GET",
      headers: { Accept: "application/json" },
      signal,
    }
  );

  if (!response.ok) return [];

  const data = (await response.json()) as {
    suggestions?: PlaceSuggestion[];
  };
  return Array.isArray(data.suggestions) ? data.suggestions : [];
}
