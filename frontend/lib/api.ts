import type { RecommendationResponse } from "@/lib/types";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

const WAKEUP_STATUSES = new Set([502, 503, 504]);
const MAX_ATTEMPTS = 4;
const RETRY_DELAY_MS = 3000;

export class RateLimitError extends Error {}

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

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
    throw new ApiError(
      response.status,
      `El servicio devolvió un error (${response.status}).`,
    );
  }

  return (await response.json()) as RecommendationResponse;
}

// Reintenta ante errores de cold-start (Render free duerme el servicio): fallo de red o
// 502/503/504. El 429 (rate limit) NO se reintenta; se propaga.
export async function fetchRecommendationsWithWakeup(
  text: string,
  onWaking: () => void,
  signal?: AbortSignal,
): Promise<RecommendationResponse> {
  let lastError: unknown;
  for (let attempt = 1; attempt <= MAX_ATTEMPTS; attempt++) {
    if (signal?.aborted) throw new DOMException("Aborted", "AbortError");
    try {
      return await fetchRecommendations(text, signal);
    } catch (error) {
      if (error instanceof RateLimitError) throw error;
      const retryable =
        error instanceof TypeError ||
        (error instanceof ApiError && WAKEUP_STATUSES.has(error.status));
      if (!retryable || attempt === MAX_ATTEMPTS) throw error;
      lastError = error;
      onWaking();
      await new Promise((resolve) => setTimeout(resolve, RETRY_DELAY_MS));
    }
  }
  throw lastError;
}
