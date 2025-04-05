export interface Event {
  name: string;
  date_venue: string;
  reasoning: string;
  details: Record<string, string>;
}

export interface RecommendationRequest {
  zip_code: string;
  interests: string[];
}

export interface RecommendationResponse {
  recommendations: Event[];
  raw_recommendations?: string;
} 