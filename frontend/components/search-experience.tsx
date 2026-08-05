"use client";

import { useRef, useState } from "react";
import { toast } from "sonner";
import { IntentPills } from "@/components/intent-pills";
import { RecommendationCard } from "@/components/recommendation-card";
import { SearchForm } from "@/components/search-form";
import { Skeleton } from "@/components/ui/skeleton";
import {
  RateLimitError,
  fetchRecommendationsWithWakeup,
} from "@/lib/api";
import type { RecommendationResponse } from "@/lib/types";

type Status = "idle" | "loading" | "done" | "error";

export function SearchExperience() {
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState<Status>("idle");
  const [data, setData] = useState<RecommendationResponse | null>(null);
  const [waking, setWaking] = useState(false);
  const abortRef = useRef<AbortController | null>(null);

  async function handleSearch(text: string) {
    const trimmed = text.trim();
    if (!trimmed) {
      toast.info("Escribe primero qué te apetece y dónde estás.");
      return;
    }

    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;

    setStatus("loading");
    setWaking(false);
    setData(null);

    try {
      const result = await fetchRecommendationsWithWakeup(
        trimmed,
        () => setWaking(true),
        controller.signal,
      );
      setData(result);
      setStatus("done");
    } catch (error) {
      if (controller.signal.aborted) return;
      setStatus("error");
      if (error instanceof RateLimitError) {
        toast.warning(error.message);
      } else {
        toast.error(
          "El servicio ha tenido un problema procesando la búsqueda. Prueba de nuevo.",
        );
      }
    } finally {
      setWaking(false);
    }
  }

  return (
    <div className="flex w-full max-w-2xl flex-col gap-6">
      <SearchForm
        value={query}
        onChange={setQuery}
        onSearch={handleSearch}
        loading={status === "loading"}
      />

      {status === "loading" && <LoadingState waking={waking} />}
      {status === "error" && (
        <p className="rounded-lg border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive">
          No se pudo completar la búsqueda. Revisa la conexión y vuelve a intentarlo.
        </p>
      )}
      {status === "done" && data && <Results data={data} />}
    </div>
  );
}

function LoadingState({ waking }: { waking: boolean }) {
  return (
    <div className="flex flex-col gap-4">
      <p className="text-sm text-muted-foreground">
        {waking
          ? "El servicio estaba en reposo; despertándolo… la primera búsqueda puede tardar hasta ~1 min."
          : "Perfilando tu petición y buscando cafeterías de especialidad…"}
      </p>
      {[0, 1, 2].map((index) => (
        <div
          key={index}
          className="flex flex-col gap-2 rounded-xl p-4 ring-1 ring-foreground/10"
        >
          <Skeleton className="h-5 w-1/2" />
          <Skeleton className="h-4 w-2/3" />
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-8 w-36" />
        </div>
      ))}
    </div>
  );
}

function Results({ data }: { data: RecommendationResponse }) {
  const { recommendations } = data;

  if (recommendations.length === 0) {
    return (
      <p className="rounded-lg border border-border bg-secondary/50 px-4 py-3 text-sm text-secondary-foreground">
        {data.message ?? "No he encontrado cafeterías para esa búsqueda."}
      </p>
    );
  }

  return (
    <div className="flex flex-col gap-4">
      <IntentPills intent={data.intent} />
      <p className="text-sm text-muted-foreground">
        ☕ {recommendations.length}{" "}
        {recommendations.length === 1 ? "recomendación" : "recomendaciones"}
        {data.search_radius_m
          ? ` · radio de búsqueda ~${data.search_radius_m} m`
          : ""}
      </p>
      {recommendations.map((recommendation, index) => (
        <RecommendationCard
          key={`${recommendation.candidate.shop.id}-${index}`}
          recommendation={recommendation}
          rank={index + 1}
          highlight={index === 0}
        />
      ))}
    </div>
  );
}
