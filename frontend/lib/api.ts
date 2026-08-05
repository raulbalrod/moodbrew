import type { RecommendationResponse } from "@/lib/types";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export class RateLimitError extends Error {}
export class ApiError extends Error {}

export async function fetchRecommendations(
  text: string,
  signal?: AbortSignal,
): Promise<RecommendationResponse> {
  const response = await fetch(`${API_BASE_URL}/api/recommendations`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
    signal,
  });

  if (response.status === 429) {
    throw new RateLimitError(
      "Demasiadas búsquedas seguidas. Espera un momento y vuelve a intentarlo.",
    );
  }
  if (!response.ok) {
    throw new ApiError(`El servicio devolvió un error (${response.status}).`);
  }

  return (await response.json()) as RecommendationResponse;
}
