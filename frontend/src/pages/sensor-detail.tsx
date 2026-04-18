import { useParams, useLocation } from "wouter";
import { ArrowLeft, MapPin, Calendar, AlertCircle, Activity } from "lucide-react";
import { Button } from "../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { useQuery } from "@tanstack/react-query";
import { apiRequest } from "../lib/queryClient";
import { Skeleton } from "../components/ui/skeleton";
import { StatusBadge } from "../components/status-badge";
import { Badge } from "../components/ui/badge";
import SousseMap from "../components/sousse-map";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import { format } from "date-fns";

interface Sensor {
  uuid: string;
  type: string;
  latitude: string;
  longitude: string;
  status: string;
  installationDate: string;
  ownerId: number;
}

interface SensorMeasure {
  id: number;
  sensorId: string;
  ts: Date;
  metric: string;
  value: string;
  unit: string;
  zone: string | null;
}

interface Intervention {
  id: number;
  sensorId: string;
  dateTime: Date;
  type: string;
  durationMinutes: number;
  cost: string;
  impactCo2: string;
}

interface InterventionTechnician {
  interventionId: number;
  technicianId: number;
  role: string;
}

interface TechnicianSimple {
  id: number;
  name: string;
}

const sensorTypeLabels: Record<string, string> = {
  "Qualité de l'air": "Qualité de l'Air",
  "Trafic": "Trafic",
  "Énergie": "Énergie",
  "Déchets": "Déchets",
  "Éclairage": "Éclairage",
};

const sensorTypeIcons: Record<string, string> = {
  "Qualité de l'air": "🌫️",
  "Trafic": "🚗",
  "Énergie": "⚡",
  "Déchets": "♻️",
  "Éclairage": "💡",
};

export default function SensorDetail() {
  const { id } = useParams();
  const [, setLocation] = useLocation();

  const { data: sensor, isLoading: sensorLoading } = useQuery < Sensor > ({
    queryKey: ["/api/sensors", id],
  });

  const { data: owner, isLoading: ownerLoading } = useQuery(
    {
      queryKey: ["/api/owners", sensor?.ownerId],
      enabled: !!sensor?.ownerId,
      queryFn: async () => {
        if (!sensor?.ownerId) return null;
        return await apiRequest("GET", `/api/owners/${sensor.ownerId}`);
      },
    }
  );

  const { data: measures, isLoading: measuresLoading } = useQuery < SensorMeasure[] > ({
    queryKey: ["/api/sensors", id, "measures"],
    enabled: !!id,
    queryFn: async () => {
      if (!id) return [];
      // fetch up to 2000 measurements for the sensor (seed generates 72 per sensor)
      return await apiRequest("GET", `/api/sensors/${id}/measurements?limit=2000`);
    },
  });

  const { data: interventions, isLoading: interventionsLoading } = useQuery < Intervention[] > ({
    queryKey: ["/api/interventions"],
  });

  // Load all technicians once so we can map ids to names
  const { data: allTechnicians } = useQuery < TechnicianSimple[] > ({
    queryKey: ["/api/technicians"],
    queryFn: async () => await apiRequest("GET", "/api/technicians"),
  });

  const sensorInterventions = interventions?.filter(i => i.sensorId === id) || [];

  const techsById = new Map < number, string> ((allTechnicians || []).map(t => [t.id, t.name]));

  function InterventionTechList({ interventionId }: { interventionId: number }) {
    const { data: itList, isLoading: itLoading } = useQuery < InterventionTechnician[] > ({
      queryKey: ["/api/interventions", interventionId, "technicians"],
      queryFn: async () => await apiRequest("GET", `/api/interventions/${interventionId}/technicians`),
    });

    if (itLoading) return <div className="text-sm text-muted-foreground">Chargement...</div>;
    if (!itList || itList.length === 0) return <div className="text-sm text-muted-foreground">Aucun technicien</div>;

    return (
      <div className="mt-2 flex flex-wrap gap-2">
        {itList.map((it) => (
          <div key={it.technicianId} className="flex items-center gap-2 bg-muted/10 rounded-md px-3 py-1 text-sm">
            <div className="font-medium">{techsById.get(it.technicianId) || `Technician #${it.technicianId}`}</div>
            <div className="text-xs text-muted-foreground">•</div>
            <div className="text-xs px-2 py-0.5 rounded bg-transparent border border-border text-muted-foreground">
              {it.role === 'Validateur' ? 'Valideur' : it.role === 'Intervenant' ? 'Intervenant' : it.role}
            </div>
          </div>
        ))}
      </div>
    );
  }

  // Group measurements by metric for chart
  const chartData = measures?.reduce((acc, measure) => {
    // Use id as timestamp since we don't have a ts field
    const timestamp = measure.id;
    const existing = acc.find((d: any) => d.timestamp === timestamp);
    const metricName = measure.grandeur || 'Unknown';

    if (existing) {
      existing[metricName] = parseFloat(measure.value);
    } else {
      acc.push({
        timestamp,
        time: `M${measure.id}`, // Use measurement ID as label
        [metricName]: parseFloat(measure.value),
      });
    }

    return acc;
  }, [] as any[]).sort((a, b) => a.timestamp - b.timestamp).slice(-24) || [];

  const metrics = [...new Set(measures?.map(m => m.grandeur) || [])];


  if (sensorLoading) {
    return (
      <div className="flex-1 overflow-auto">
        <div className="max-w-7xl mx-auto p-6 space-y-6">
          <Skeleton className="h-10 w-64" />
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <Skeleton className="h-96 lg:col-span-2" />
            <Skeleton className="h-96" />
          </div>
        </div>
      </div>
    );
  }

  if (!sensor) {
    return (
      <div className="flex-1 overflow-auto">
        <div className="max-w-7xl mx-auto p-6">
          <div className="text-center py-12">
            <AlertCircle className="w-12 h-12 mx-auto mb-4 text-muted-foreground" />
            <p className="font-medium">Capteur non trouvé</p>
            <Button
              variant="outline"
              onClick={() => setLocation("/sensors")}
              className="mt-4"
              data-testid="button-back-to-sensors"
            >
              <ArrowLeft className="w-4 h-4 mr-2" />
              Retour aux capteurs
            </Button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-auto">
      <div className="max-w-7xl mx-auto p-6 space-y-6">
        <div className="flex items-center gap-4">
          <Button
            variant="outline"
            size="icon"
            onClick={() => setLocation("/sensors")}
            data-testid="button-back"
          >
            <ArrowLeft className="w-4 h-4" />
          </Button>
          <div className="flex-1">
            <h1 className="text-3xl font-bold text-foreground">
              {sensorTypeLabels[sensor.type]} {sensorTypeIcons[sensor.type]}
            </h1>
            <p className="text-muted-foreground mt-1">
              {sensor.uuid}
            </p>
          </div>
          <StatusBadge status={sensor.status} />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                Position
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-2 text-sm">
                <MapPin className="w-4 h-4 text-primary" />
                <span className="font-mono">{sensor.latitude}, {sensor.longitude}</span>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                Installation
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-2 text-sm">
                <Calendar className="w-4 h-4 text-primary" />
                <span>{new Date(sensor.installationDate).toLocaleDateString('fr-FR')}</span>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                Interventions
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-2 text-sm">
                <Activity className="w-4 h-4 text-primary" />
                <span className="font-mono">{sensorInterventions.length} total</span>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                Propriétaire
              </CardTitle>
            </CardHeader>
            <CardContent>
              {ownerLoading ? (
                <Skeleton className="h-16 w-full" />
              ) : owner ? (
                <div className="space-y-2 text-sm">
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="font-medium">{owner.name}</div>
                    </div>
                    <div className="text-right">
                      <div className="text-xs text-muted-foreground">Type</div>
                      <div className="font-medium">{owner.ownerType === 'municipalite' ? 'Municipalité' : 'Privé'}</div>
                    </div>
                  </div>

                  {owner.address && (
                    <div>
                      <div className="text-xs text-muted-foreground">Adresse</div>
                      <div className="text-sm">{owner.address}</div>
                    </div>
                  )}

                  <div className="grid grid-cols-1 gap-1">
                    {owner.phone && (
                      <div>
                        <div className="text-xs text-muted-foreground">Téléphone</div>
                        <div className="text-sm">
                          <a className="text-primary underline" href={`tel:${owner.phone}`}>{owner.phone}</a>
                        </div>
                      </div>
                    )}

                    {owner.email && (
                      <div>
                        <div className="text-xs text-muted-foreground">Email</div>
                        <div className="text-sm">
                          <a className="text-primary underline" href={`mailto:${owner.email}`}>{owner.email}</a>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              ) : (
                <div className="text-sm text-muted-foreground">Aucun propriétaire enregistré</div>
              )}
            </CardContent>
          </Card>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <Card className="lg:col-span-2">
            <CardHeader>
              <CardTitle>Mesures en Temps Réel (24h)</CardTitle>
            </CardHeader>
            <CardContent>
              {measuresLoading ? (
                <Skeleton className="h-80 w-full" />
              ) : chartData.length > 0 ? (
                <ResponsiveContainer width="100%" height={320}>
                  <LineChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                    <XAxis
                      dataKey="time"
                      className="text-xs"
                      stroke="hsl(var(--muted-foreground))"
                    />
                    <YAxis
                      className="text-xs"
                      stroke="hsl(var(--muted-foreground))"
                    />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: "hsl(var(--card))",
                        border: "1px solid hsl(var(--border))",
                        borderRadius: "8px",
                      }}
                    />
                    <Legend />
                    {metrics.map((metric, index) => (
                      <Line
                        key={metric}
                        type="monotone"
                        dataKey={metric}
                        stroke={`hsl(${120 + index * 60}, 70%, 50%)`}
                        strokeWidth={2}
                        dot={false}
                      />
                    ))}
                  </LineChart>
                </ResponsiveContainer>
              ) : (
                <div className="h-80 flex items-center justify-center text-muted-foreground">
                  <div className="text-center">
                    <Activity className="w-12 h-12 mx-auto mb-2 opacity-50" />
                    <p>Aucune mesure disponible</p>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Carte</CardTitle>
            </CardHeader>
            <CardContent>
              <div data-testid="sensor-map">
                {/* Focused map for single sensor */}
                <SousseMap
                  center={[parseFloat(sensor.latitude as any) || 35.8256, parseFloat(sensor.longitude as any) || 10.63699]}
                  zoom={15}
                  height="h-80"
                  singleSensor={{ lat: parseFloat(sensor.latitude as any) || 0, lng: parseFloat(sensor.longitude as any) || 0, id: sensor.uuid }}
                />
              </div>
            </CardContent>
          </Card>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Historique des Interventions</CardTitle>
          </CardHeader>
          <CardContent>
            {interventionsLoading ? (
              <div className="space-y-3">
                {[1, 2, 3].map((i) => (
                  <Skeleton key={i} className="h-16 w-full" />
                ))}
              </div>
            ) : sensorInterventions.length > 0 ? (
              <div className="space-y-3" data-testid="list-interventions">
                {sensorInterventions.map((intervention) => (
                  <div
                    key={intervention.id}
                    className="flex items-center justify-between p-4 border rounded-md hover-elevate"
                  >
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <span className="font-medium">Intervention #{intervention.id}</span>
                        <Badge
                          variant="secondary"
                          className={
                            intervention.type === "predictive"
                              ? "bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300"
                              : intervention.type === "corrective"
                                ? "bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-300"
                                : "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300"
                          }
                        >
                          {intervention.type}
                        </Badge>
                      </div>
                      <p className="text-sm text-muted-foreground mt-1">
                        {format(new Date(intervention.dateTime), "dd/MM/yyyy HH:mm")} • {intervention.durationMinutes} min • {intervention.cost} TND
                      </p>
                      {/* Technicians who participated */}
                      <InterventionTechList interventionId={intervention.id} />
                    </div>
                    <div className="text-right">
                      <p className="text-sm font-medium text-green-600 dark:text-green-400">
                        -{intervention.impactCo2} kg CO₂
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-sm text-muted-foreground text-center py-8">
                Aucune intervention enregistrée pour ce capteur
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
