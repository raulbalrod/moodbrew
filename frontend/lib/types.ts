export interface IntentProfile {
  area: string | null;
  needs_wifi: boolean;
  open_now: boolean;
  radius_m: number;
}

export interface CoffeeShop {
  id: number;
  name: string;
  address: string | null;
  city: string | null;
  lat: number;
  lon: number;
  external_id: string | null;
  opening_hours: string | null;
  has_wifi: boolean;
  is_coffee_shop: boolean;
  attributes: Record<string, unknown>;
  specialty_score: number;
}

export interface CoffeeShopCandidate {
  shop: CoffeeShop;
  is_open: boolean | null;
  distance_m: number | null;
}

export interface Recommendation {
  candidate: CoffeeShopCandidate;
  reasoning: string;
}

export interface RecommendationResponse {
  query: string;
  intent: IntentProfile;
  recommendations: Recommendation[];
  nearby: Recommendation[];
  search_radius_m: number | null;
  message: string | null;
}
