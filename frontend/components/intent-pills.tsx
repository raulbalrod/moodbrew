import { Clock, MapPin, Ruler, Wifi } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import type { IntentProfile } from "@/lib/types";

export function IntentPills({ intent }: { intent: IntentProfile }) {
  const pills = [
    intent.area && (
      <Badge key="area" variant="secondary">
        <MapPin /> {intent.area}
      </Badge>
    ),
    intent.needs_wifi && (
      <Badge key="wifi" variant="secondary">
        <Wifi /> wifi
      </Badge>
    ),
    intent.open_now && (
      <Badge key="open" variant="secondary">
        <Clock /> abierto ahora
      </Badge>
    ),
    intent.radius_m && (
      <Badge key="radius" variant="secondary">
        <Ruler /> radio ~{intent.radius_m} m
      </Badge>
    ),
  ].filter(Boolean);

  if (pills.length === 0) return null;

  return (
    <div className="flex flex-col gap-1.5">
      <span className="text-xs text-muted-foreground">Entendí que buscas:</span>
      <div className="flex flex-wrap gap-1.5">{pills}</div>
    </div>
  );
}
