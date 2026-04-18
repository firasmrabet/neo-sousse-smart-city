import { Calendar, Download, Filter } from "lucide-react";
import { Button } from "../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../components/ui/select";
import { useQuery } from "@tanstack/react-query";
import { apiRequest } from "../lib/queryClient";
import { useState } from "react";
import SousseMap from "../components/sousse-map";
import { SensorMeasurementsChart } from "../components/sensor-measurements-chart";
import type { Sensor } from "@shared/schema";

export default function Analytics() {
  const [period, setPeriod] = useState < string > ("24h");
  const [zone, setZone] = useState < string > ("all");
  const [selectedSensorId, setSelectedSensorId] = useState<string | undefined>(undefined);

  const hours = period === "24h" ? 24 : period === "7days" ? 168 : period === "30days" ? 720 : 8760;

  // Fetch sensors list
  const { data: sensors } = useQuery({
    queryKey: ["/api/sensors"],
    queryFn: async () => (await apiRequest("GET", "/api/sensors")) as Sensor[],
  });

  const { data: pollutedZones, isLoading: pollutedLoading } = useQuery({
    queryKey: ["/api/analytics/polluted-zones", hours],
    queryFn: async () => (await apiRequest("GET", `/api/analytics/polluted-zones?hours=${hours}`)) as Array<{ zone: string; metric: string; avgValue: string }>,
  });

  const { data: availability, isLoading: availabilityLoading } = useQuery({
    queryKey: ["/api/analytics/sensor-availability"],
    queryFn: async () => (await apiRequest("GET", "/api/analytics/sensor-availability")) as Array<{ zone: string; activeCount: number; totalCount: number }>,
  });

  const { data: predictiveStats, isLoading: predictiveLoading } = useQuery({
    queryKey: ["/api/analytics/predictive-interventions", new Date().toISOString().slice(0, 7)],
    queryFn: async () => (await apiRequest("GET", `/api/analytics/predictive-interventions?month=${encodeURIComponent(new Date().toISOString().slice(0, 10))}`)) as { count: number; totalCo2Saving: string },
  });

  const { data: topTrips, isLoading: tripsLoading } = useQuery({
    queryKey: ["/api/analytics/top-co2-trips"],
    queryFn: async () => (await apiRequest("GET", "/api/analytics/top-co2-trips?limit=10")) as Array<any>,
  });

  return (
    <div className="flex-1 overflow-auto">
      <div className="max-w-7xl mx-auto p-6 space-y-6">
        <div className="flex items-center justify-between gap-4 flex-wrap">
          <div>
            <h1 className="text-3xl font-bold text-foreground">Analytics</h1>
            <p className="text-muted-foreground mt-1">
              Analyses avancées et rapports environnementaux
            </p>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" data-testid="button-filter">
              <Filter className="w-4 h-4 mr-2" />
              Filtres
            </Button>
            <Button variant="outline" data-testid="button-export">
              <Download className="w-4 h-4 mr-2" />
              Exporter
            </Button>
          </div>
        </div>

        <Card>
          <CardHeader>
            <div className="flex flex-col md:flex-row gap-4 justify-between items-start md:items-center">
              <CardTitle>Contrôles</CardTitle>
              <div className="flex gap-2 flex-wrap">
                <Select value={period} onValueChange={setPeriod}>
                  <SelectTrigger className="w-40" data-testid="select-period">
                    <SelectValue placeholder="Période" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="24h">Dernières 24h</SelectItem>
                    <SelectItem value="7days">7 derniers jours</SelectItem>
                    <SelectItem value="30days">30 derniers jours</SelectItem>
                    <SelectItem value="year">Cette année</SelectItem>
                  </SelectContent>
                </Select>
                <Select value={zone} onValueChange={setZone}>
                  <SelectTrigger className="w-40" data-testid="select-zone">
                    <SelectValue placeholder="Zone" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">Toutes les zones</SelectItem>
                    <SelectItem value="centre">Centre</SelectItem>
                    <SelectItem value="nord">Nord</SelectItem>
                    <SelectItem value="sud">Sud</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
          </CardHeader>
        </Card>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card>
            <CardHeader>
              <CardTitle>Zones les Plus Polluées (24h)</CardTitle>
            </CardHeader>
            <CardContent>
              {pollutedLoading ? (
                <div className="h-64 flex items-center justify-center">Chargement...</div>
              ) : (
                <div className="space-y-3">
                  {/* Always render the map (it will show circles when pollutedZones provided) */}
                  <SousseMap height="h-64" pollutedZones={pollutedZones || []} />

                  {/* If there are zones, show a compact ranked list; otherwise show helper text */}
                  {(pollutedZones && pollutedZones.length > 0) ? (
                    <div className="space-y-2">
                      {pollutedZones
                        .slice()
                        .sort((a, b) => Number(b.avgValue) - Number(a.avgValue))
                        .map((z, idx) => (
                          <div key={`${z.zone}-${idx}`} className="flex items-center justify-between p-2 border rounded">
                            <div>
                              <div className="font-medium">{z.zone}</div>
                              <div className="text-xs text-muted-foreground">Score pollution (moyenne métriques)</div>
                            </div>
                            <div className="text-right font-mono">{Number(z.avgValue).toFixed(2)}</div>
                          </div>
                        ))}
                    </div>
                  ) : (
                    <div className="text-sm text-muted-foreground text-center py-4">Aucune donnée de pollution pour la période sélectionnée</div>
                  )}
                </div>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Disponibilité des Capteurs dans la ville</CardTitle>
            </CardHeader>
            <CardContent>
              {availabilityLoading ? (
                <div className="h-40 flex items-center justify-center">Chargement...</div>
              ) : availability && availability.length > 0 ? (
                <div className="space-y-2">
                  {availability.map((a) => (
                    <div key={a.zone} className="flex items-center justify-between p-2 border rounded">
                      <div>
                        <div className="font-medium">{a.zone}</div>
                        <div className="text-xs text-muted-foreground">Capteurs actifs: {a.activeCount} / {a.totalCount}</div>
                      </div>
                      <div className="text-right font-mono">{((a.activeCount / Math.max(1, a.totalCount)) * 100).toFixed(0)}%</div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="h-40 flex items-center justify-center bg-muted rounded-md" data-testid="chart-availability">
                  <p className="text-sm text-muted-foreground">Aucune donnée de disponibilité</p>
                </div>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Les trajets de véhicules autonomes ont permis la plus grande réduction de CO2</CardTitle>

            </CardHeader>
            <CardContent>
              {tripsLoading ? (
                <div className="h-40 flex items-center justify-center">Chargement...</div>
              ) : topTrips && topTrips.length > 0 ? (
                <div className="space-y-2 max-h-[350px] overflow-y-auto pr-2">
                  {topTrips.map((t: any, idx: number) => (
                    <div key={t.id} className="flex items-center justify-between p-2 border rounded">
                      <div>
                        <div className="font-medium">Trajet #{idx + 1} - {t.vehiclePlate || t.vehicleId || "Véhicule"}</div>
                        <div className="text-xs text-muted-foreground">Début: {new Date(t.date || t.startTime).toLocaleString('fr-FR')}</div>
                      </div>
                      <div className="text-right font-mono">{Number(t.co2Saving).toFixed(2)} kg CO₂</div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="h-40 flex items-center justify-center bg-muted rounded-md" data-testid="chart-impact">
                  <p className="text-sm text-muted-foreground">Aucune donnée d'impact</p>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Sensor Measurements Real-time Chart */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-2xl font-bold">Mesures en Temps Réel</h2>
            {sensors && sensors.length > 0 && (
              <Select value={selectedSensorId || ""} onValueChange={setSelectedSensorId}>
                <SelectTrigger className="w-64" data-testid="select-sensor">
                  <SelectValue placeholder="Sélectionner un capteur" />
                </SelectTrigger>
                <SelectContent>
                  {sensors.map((sensor) => (
                    <SelectItem key={sensor.uuid} value={sensor.uuid}>
                      {sensor.type} - ({sensor.uuid.slice(0, 8)})
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}
          </div>
          
          {selectedSensorId && (
            <SensorMeasurementsChart
              sensorId={selectedSensorId}
              sensorName={
                sensors?.find((s) => s.uuid === selectedSensorId)?.type || "Capteur"
              }
              limit={50}
            />
          )}
        </div>
      </div>
    </div>
  );
}
