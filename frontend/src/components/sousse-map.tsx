import React from "react";
import { MapContainer, TileLayer, CircleMarker, Popup, ZoomControl } from "react-leaflet";
import { useQuery } from "@tanstack/react-query";

type PollutedZone = { zone: string; avgValue: string };

type Props = {
  center?: [number, number];
  zoom?: number;
  height?: string;
  singleSensor?: { lat: number; lng: number; id?: string } | null;
  pollutedZones?: PollutedZone[];
};

// Approximate center coordinates for named zones in Sousse
const ZONE_COORDS: Record<string, [number, number]> = {
  centre: [35.8256, 10.63699],
  center: [35.8256, 10.63699],
  nord: [35.8800, 10.6400],
  sud: [35.7800, 10.6400],
  est: [35.8256, 10.7000],
  ouest: [35.8256, 10.5800],
  "centre-ville": [35.8256, 10.63699],
};

function sizeFromValue(v: number) {
  // scale values to a reasonable circle radius on the map
  // base 8, plus scaled up to 40
  return Math.min(40, 8 + Math.sqrt(Math.max(0, v)) * 2);
}

export default function SousseMap({
  center = [35.8256, 10.63699],
  zoom = 12,
  height = "h-96",
  singleSensor = null,
  pollutedZones = [],
}: Props) {
  const { data: sensors } = useQuery < any[] > ({
    queryKey: ["/api/sensors"],
    // poll every 5s to approximate "temps réel"
    refetchInterval: 5000,
  });

  const list = sensors || [];

  // map polluted zones to coords when possible
  const zonesWithCoords = (pollutedZones || []).map((z) => {
    const key = (z.zone || "").toLowerCase();
    const coords = ZONE_COORDS[key];
    return { ...z, coords };
  }).filter(z => z.coords) as Array<PollutedZone & { coords: [number, number] }>;

  return (
    <div className={`${height} w-full relative`}>
      <MapContainer
        center={center}
        zoom={zoom}
        scrollWheelZoom={true}
        doubleClickZoom={true}
        touchZoom={true}
        dragging={true}
        style={{ height: "100%", width: "100%" }}
      >
        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution='&copy; OpenStreetMap contributors'
        />
        <ZoomControl position="topright" />

        {singleSensor ? (
          <CircleMarker
            center={[singleSensor.lat, singleSensor.lng]}
            radius={8}
            color="blue"
            fillColor="blue"
            fillOpacity={0.8}
          >
            <Popup>{singleSensor.id || "Capteur"}</Popup>
          </CircleMarker>
        ) : (
          list.map((s: any) => {
            // Robust coordinate parsing
            const rawLat = s.latitude ?? s.lat;
            const rawLng = s.longitude ?? s.lng;

            const lat = typeof rawLat === 'string' ? parseFloat(rawLat) : Number(rawLat);
            const lng = typeof rawLng === 'string' ? parseFloat(rawLng) : Number(rawLng);

            if (!lat || !lng || Number.isNaN(lat) || Number.isNaN(lng)) {
              // console.warn('Invalid coordinates for sensor:', s.uuid, lat, lng);
              return null;
            }

            const color = (s.status || "").toLowerCase() === "actif" || (s.status || "").toLowerCase() === "active" ? "#16a34a" : "#6b7280";

            return (
              <CircleMarker
                key={s.uuid ?? s.id ?? `${lat}-${lng}`}
                center={[lat, lng]}
                radius={6}
                color={color}
                fillColor={color}
                fillOpacity={0.7}
              >
                <Popup>
                  <div style={{ minWidth: 160 }}>
                    <div style={{ fontWeight: 600 }}>{s.uuid ?? s.name ?? "Capteur"}</div>
                    <div style={{ fontSize: 12, color: "#6b7280" }}>{s.type ?? "-"}</div>
                    <div style={{ fontSize: 12 }}>Statut: {s.status ?? "-"}</div>
                  </div>
                </Popup>
              </CircleMarker>
            );
          })
        )}

        {/* polluted zone circles */}
        {zonesWithCoords.map((z: any, idx: number) => {
          const val = Number(z.avgValue) || 0;
          const radius = sizeFromValue(val);
          return (
            <CircleMarker
              key={`zone-${z.zone}-${idx}`}
              center={z.coords}
              radius={radius}
              color="#ef4444"
              fillColor="#ef4444"
              fillOpacity={0.35}
            >
              <Popup>
                <div style={{ minWidth: 160 }}>
                  <div style={{ fontWeight: 600 }}>{z.zone}</div>
                  <div style={{ fontSize: 12, color: "#6b7280" }}>Score: {Number(z.avgValue).toFixed(2)}</div>
                </div>
              </Popup>
            </CircleMarker>
          );
        })}
      </MapContainer>

      {/* Legend / key */}
      <div className="absolute top-3 right-3 bg-black/70 text-white text-xs p-2 rounded-md shadow-lg z-20">
        <div className="font-medium mb-1">Légende</div>
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <span className="inline-block w-3 h-3 rounded-full bg-green-500" />
            <span>Actif (capteur)</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="inline-block w-3 h-3 rounded-full bg-gray-500" />
            <span>Hors service (capteur)</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="inline-block w-3 h-3 rounded-full bg-red-500" />
            <span>Zone la plus polluée</span>
          </div>
        </div>
        <div className="mt-2 text-[11px] text-muted-foreground">
          <div>La taille du cercle indique l'intensité (score moyen)</div>
        </div>
      </div>
    </div>
  );
}
