/** Types matching backend serializers / API_CONTRACT.md */

export interface PlaceSuggestion {
  label: string;
  city: string;
  state: string;
  latitude: number;
  longitude: number;
}

export interface Place {
  query: string;
  address: string;
  latitude: number;
  longitude: number;
}

export interface RouteSummary {
  distance_miles: number;
  duration_seconds: number;
  duration_hours: number;
  destination_eta: string;
  start: Place;
  finish: Place;
}

export interface FuelStop {
  sequence: number;
  station_id: number;
  name: string;
  address: string;
  city: string;
  state: string;
  latitude: number;
  longitude: number;
  price_per_gallon: number;
  distance_from_start_miles: number;
  gallons_purchased: number;
  cost_usd: number;
  remaining_range_before_refuel_miles: number;
  eta: string;
  dwell_minutes: number;
}

export interface TripSummary {
  total_gallons_used: number;
  total_fuel_cost_usd: number;
  average_price_per_gallon_usd: number;
  stop_count: number;
}

export interface Vehicle {
  mpg: number;
  max_range_miles: number;
  tank_capacity_gallons: number;
  range_reserve_miles: number;
  route_corridor_miles: number;
}

export interface ExternalCalls {
  geocode: number;
  routing: number;
  total: number;
  geocode_cache_hits: number;
  routing_cache_hits: number;
  per_station: number;
}

export interface RoutePlanMeta {
  response_time_ms: number;
  external_calls: ExternalCalls;
  stations_considered: number;
  stations_in_route_bbox: number;
  depart_at: string;
  currency_rounding: string;
}

export interface GeoJsonLineString {
  type: "LineString";
  coordinates: [number, number][]; // [lon, lat]
}

export interface RoutePlanResponse {
  route_summary: RouteSummary;
  route_geometry: GeoJsonLineString;
  coordinates: [number, number][]; // [lat, lon] Leaflet-friendly
  fuel_stops: FuelStop[];
  trip_summary: TripSummary;
  vehicle: Vehicle;
  meta: RoutePlanMeta;
}

export interface RoutePlanRequest {
  start: string;
  finish: string;
  depart_at?: string;
}

export interface ApiErrorBody {
  code: string;
  message: string;
  details?: Record<string, unknown>;
}

export interface ApiErrorResponse {
  error: ApiErrorBody;
}

export class ApiError extends Error {
  status: number;
  code: string;
  details: Record<string, unknown>;

  constructor(status: number, body: ApiErrorBody) {
    super(body.message);
    this.name = "ApiError";
    this.status = status;
    this.code = body.code;
    this.details = body.details ?? {};
  }
}
