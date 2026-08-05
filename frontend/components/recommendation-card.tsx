import { Coffee, MapPin, Navigation, Sparkles, Wifi } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { buttonVariants } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import type { Recommendation } from "@/lib/types";

function directionsUrl(lat: number, lon: number) {
  return `https://www.google.com/maps/dir/?api=1&destination=${lat},${lon}&travelmode=walking`;
}

type Props = {
  recommendation: Recommendation;
  rank?: number;
  highlight?: boolean;
  active?: boolean;
};

export function RecommendationCard({
  recommendation,
  rank,
  highlight,
  active,
}: Props) {
  const { candidate, reasoning } = recommendation;
  const { shop } = candidate;

  return (
    <Card className={cn("transition-shadow", active && "ring-2 ring-primary")}>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-lg">
          {rank != null && <span className="text-muted-foreground">{rank}.</span>}
          <span className="flex-1">{shop.name}</span>
          {highlight && (
            <Badge>
              <Sparkles /> Mejor opción
            </Badge>
          )}
        </CardTitle>
        <div className="flex flex-wrap gap-1.5 pt-1">
          {candidate.is_open === true && (
            <Badge variant="secondary" className="text-green-700">
              Abierta ahora
            </Badge>
          )}
          {candidate.is_open === false && (
            <Badge variant="secondary" className="text-red-700">
              Cerrada ahora
            </Badge>
          )}
          {candidate.distance_m != null && (
            <Badge variant="outline">
              <MapPin /> a unos {Math.round(candidate.distance_m)} m
            </Badge>
          )}
          {shop.is_coffee_shop && (
            <Badge variant="outline">
              <Coffee /> Especialidad
            </Badge>
          )}
          {shop.has_wifi && (
            <Badge variant="outline">
              <Wifi /> Wifi
            </Badge>
          )}
        </div>
      </CardHeader>
      <CardContent className="flex flex-col gap-3">
        {shop.address && (
          <p className="text-sm text-muted-foreground">{shop.address}</p>
        )}
        <p className="text-sm">{reasoning}</p>
        <a
          href={directionsUrl(shop.lat, shop.lon)}
          target="_blank"
          rel="noopener noreferrer"
          className={buttonVariants({
            variant: "outline",
            size: "sm",
            className: "w-fit",
          })}
        >
          <Navigation /> Cómo llegar
        </a>
      </CardContent>
    </Card>
  );
}
