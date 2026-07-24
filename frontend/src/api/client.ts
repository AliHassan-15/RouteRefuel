import type { ApiErrorResponse, RoutePlanRequest, RoutePlanResponse } from "../types/api";
import { ApiError } from "../types/api";

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
