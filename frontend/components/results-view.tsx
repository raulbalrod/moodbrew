"use client";

import { useMemo, useState } from "react";
import dynamic from "next/dynamic";
import { List, Map as MapIcon } from "lucide-react";
import { IntentPills } from "@/components/intent-pills";
import { RecommendationCard } from "@/components/recommendation-card";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";
import type { MapMarker } from "@/components/map-panel";
import type { RecommendationResponse } from "@/lib/types";

const MapPanel = dynamic(
  () => import("@/components/map-panel").then((mod) => mod.MapPanel),
  { ssr: false, loading: () => <Skeleton className="h-full w-full rounded-xl" /> },
);

export function ResultsView({ data }: { data: RecommendationResponse }) {
  const [view, setView] = useState<"list" | "map">("list");
  const [activeId, setActiveId] = useState<string | null>(null);
  const { recommendations, nearby } = data;

  const markers = useMemo<MapMarker[]>(
    () => [
      ...recommendations.map((rec, index) => ({
        id: `c-${rec.candidate.shop.id}-${index}`,
        lat: rec.candidate.shop.lat,
        lon: rec.candidate.shop.lon,
        name: rec.candidate.shop.name,
        kind: "curated" as const,
        label: String(index + 1),
      })),
      ...nearby.map((rec, index) => ({
        id: `n-${rec.candidate.shop.id}-${index}`,
        lat: rec.candidate.shop.lat,
        lon: rec.candidate.shop.lon,
        name: rec.candidate.shop.name,
        kind: "nearby" as const,
      })),
    ],
    [recommendations, nearby],
  );

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

      <div className="flex items-center justify-between gap-2">
        <p className="text-sm text-muted-foreground">
          ☕ {recommendations.length}{" "}
          {recommendations.length === 1 ? "recomendación" : "recomendaciones"}
          {nearby.length > 0 ? ` · ${nearby.length} cerca` : ""}
          {data.search_radius_m ? ` · radio ~${data.search_radius_m} m` : ""}
        </p>

        <div className="flex gap-1 lg:hidden">
          <Button
            size="sm"
            variant={view === "list" ? "default" : "outline"}
            onClick={() => setView("list")}
          >
            <List /> Lista
          </Button>
          <Button
            size="sm"
            variant={view === "map" ? "default" : "outline"}
            onClick={() => setView("map")}
          >
            <MapIcon /> Mapa
          </Button>
        </div>
      </div>

      <div className="lg:grid lg:grid-cols-[minmax(0,1fr)_minmax(0,1fr)] lg:gap-6">
        <div
          className={cn(
            "flex flex-col gap-6",
            view === "map" && "hidden",
            "lg:flex",
          )}
        >
          <section className="flex flex-col gap-4">
            {recommendations.map((rec, index) => {
              const id = `c-${rec.candidate.shop.id}-${index}`;
              return (
                <div
                  key={id}
                  onMouseEnter={() => setActiveId(id)}
                  onMouseLeave={() => setActiveId(null)}
                >
                  <RecommendationCard
                    recommendation={rec}
                    rank={index + 1}
                    highlight={index === 0}
                    active={activeId === id}
                  />
                </div>
              );
            })}
          </section>

          {nearby.length > 0 && (
            <section className="flex flex-col gap-3">
              <h2 className="text-sm font-medium text-muted-foreground">
                También cerca · quizá te gusten
              </h2>
              {nearby.map((rec, index) => {
                const id = `n-${rec.candidate.shop.id}-${index}`;
                return (
                  <div
                    key={id}
                    onMouseEnter={() => setActiveId(id)}
                    onMouseLeave={() => setActiveId(null)}
                  >
                    <RecommendationCard
                      recommendation={rec}
                      active={activeId === id}
                    />
                  </div>
                );
              })}
            </section>
          )}
        </div>

        <div className={cn(view === "list" && "hidden", "lg:block")}>
          <div className="h-[70vh] lg:sticky lg:top-6">
            <MapPanel markers={markers} activeId={activeId} onHover={setActiveId} />
          </div>
        </div>
      </div>
    </div>
  );
}
