'use client';

import 'maplibre-gl/dist/maplibre-gl.css';
import { useEffect, useRef } from 'react';
import * as maplibregl from 'maplibre-gl';
import type {
  Map as MlMap,
  Marker as MlMarker,
  StyleSpecification,
} from 'maplibre-gl';

const KEY = process.env.NEXT_PUBLIC_GEOAPIFY_MAP_KEY;
const STYLE = process.env.NEXT_PUBLIC_GEOAPIFY_MAP_STYLE ?? 'osm-bright-grey';

export type MapMarker = {
  id: string;
  lat: number;
  lon: number;
  name: string;
  kind: 'curated' | 'nearby';
  label?: string;
};

type Props = {
  markers: MapMarker[];
  activeId?: string | null;
  onHover?: (id: string | null) => void;
};

function mapStyle(): StyleSpecification {
  const tiles = KEY
    ? [
        `https://maps.geoapify.com/v1/tile/${STYLE}/{z}/{x}/{y}@2x.png?apiKey=${KEY}`,
      ]
    : ['https://tile.openstreetmap.org/{z}/{x}/{y}.png'];
  const attribution = KEY
    ? 'Powered by Geoapify | © OpenMapTiles © OpenStreetMap'
    : '© OpenStreetMap';
  return {
    version: 8,
    sources: {
      base: { type: 'raster', tiles, tileSize: 256, attribution },
    },
    layers: [{ id: 'base', type: 'raster', source: 'base' }],
  } satisfies StyleSpecification;
}

// El wrapper lo posiciona maplibre (transform de traslación); el inner (marcado con
// data-marker-id) es lo que escalamos en el hover, sin pisar esa traslación.
function markerElement(
  marker: MapMarker,
  onHover?: (id: string | null) => void,
): HTMLDivElement {
  const wrapper = document.createElement('div');
  const inner = document.createElement('div');
  inner.dataset.markerId = marker.id;
  inner.className =
    marker.kind === 'curated'
      ? 'flex h-7 min-w-7 cursor-pointer items-center justify-center rounded-full bg-primary px-2 text-xs font-semibold text-primary-foreground shadow ring-2 ring-white'
      : 'h-3.5 w-3.5 cursor-pointer rounded-full bg-accent shadow ring-2 ring-white';
  inner.style.transition = 'transform 120ms ease, box-shadow 120ms ease';
  if (marker.kind === 'curated' && marker.label) inner.textContent = marker.label;
  wrapper.addEventListener('mouseenter', () => onHover?.(marker.id));
  wrapper.addEventListener('mouseleave', () => onHover?.(null));
  wrapper.appendChild(inner);
  return wrapper;
}

export function MapPanel({ markers, activeId, onHover }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<MlMap | null>(null);
  const onHoverRef = useRef(onHover);

  useEffect(() => {
    onHoverRef.current = onHover;
  }, [onHover]);

  useEffect(() => {
    if (!containerRef.current) return;
    const map = new maplibregl.Map({
      container: containerRef.current,
      style: mapStyle(),
      center: [0, 0],
      zoom: 2,
      attributionControl: { compact: true },
    });
    map.addControl(
      new maplibregl.NavigationControl({ showCompass: false }),
      'top-right',
    );
    mapRef.current = map;

    const observer = new ResizeObserver(() => map.resize());
    observer.observe(containerRef.current);

    return () => {
      observer.disconnect();
      map.remove();
      mapRef.current = null;
    };
  }, []);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || markers.length === 0) return;

    const instances: MlMarker[] = [];
    const bounds = new maplibregl.LngLatBounds();

    for (const marker of markers) {
      instances.push(
        new maplibregl.Marker({
          element: markerElement(marker, (id) => onHoverRef.current?.(id)),
        })
          .setLngLat([marker.lon, marker.lat])
          .setPopup(new maplibregl.Popup({ offset: 16 }).setText(marker.name))
          .addTo(map),
      );
      bounds.extend([marker.lon, marker.lat]);
    }

    if (markers.length === 1) {
      map.setCenter([markers[0].lon, markers[0].lat]);
      map.setZoom(14);
    } else {
      map.fitBounds(bounds, { padding: 48, maxZoom: 15 });
    }

    return () => instances.forEach((instance) => instance.remove());
  }, [markers]);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;
    const nodes = container.querySelectorAll<HTMLElement>('[data-marker-id]');
    nodes.forEach((node) => {
      const active = node.dataset.markerId === activeId;
      node.style.transform = active ? 'scale(1.35)' : '';
      node.style.boxShadow = active ? '0 0 0 3px var(--primary)' : '';
      if (node.parentElement) node.parentElement.style.zIndex = active ? '10' : '';
    });
  }, [activeId]);

  return (
    <div
      ref={containerRef}
      className="h-full w-full overflow-hidden rounded-xl ring-1 ring-foreground/10"
    />
  );
}
