import React, { useState } from "react";
import { Activity, Cpu, Users, Leaf, Play, Loader2 } from "lucide-react";
import { StatCard } from "../components/stat-card";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Skeleton } from "../components/ui/skeleton";
import SousseMap from "../components/sousse-map";
import { useQuery } from "@tanstack/react-query";
import { useMemo } from "react";
import { apiRequest } from "../lib/queryClient";
import { Badge } from "../components/ui/badge";
import { format } from "date-fns";
import { TechniciansCard } from "../components/technicians-card";
import { Button } from "../components/ui/button";
import { useToast } from "../hooks/use-toast";

interface DashboardStats {
  activeSensors: number;
  totalSensors: number;
  interventionsToday: number;
  predictiveToday: number;
  avgEngagement: number;
  totalCitizens: number;
  co2Saved: string;
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

export default function Dashboard() {
  const [launchingStreamlit, setLaunchingStreamlit] = useState(false);
  const { toast } = useToast();

  const handleLaunchStreamlit = async () => {
    setLaunchingStreamlit(true);
    try {
      // First, launch Streamlit via backend API
      const response = await fetch("/api/streamlit/launch", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ app: "professional", port: 8510 }),
      });
      const data = await response.json();
      
      if (data.success) {
        toast({
          title: "🚀 Streamlit lancé !",
          description: `Dashboard Streamlit démarré sur le port 8510`,
        });
        // Wait a bit more for Streamlit to fully initialize
        await new Promise(resolve => setTimeout(resolve, 3000));
        window.open("http://localhost:8510", "_blank");
      } else {
        // Streamlit might already be running, try to open anyway
        toast({
          title: "⚠️ Lancement en cours...",
          description: "Tentative d'ouverture du dashboard Streamlit...",
        });
        window.open("http://localhost:8510", "_blank");
      }
    } catch (error) {
      // Backend might not be reachable, try to open Streamlit directly
      toast({
        title: "📡 Ouverture Streamlit",
        description: "Ouverture du dashboard Streamlit sur port 8510...",
      });
      window.open("http://localhost:8510", "_blank");
    } finally {
      setLaunchingStreamlit(false);
    }
  };

  const { data: stats, isLoading: statsLoading } = useQuery < DashboardStats > ({
    queryKey: ["/api/dashboard/stats"],
    // keep dashboard stats fresh: refetch on window focus and every 15s
    refetchOnWindowFocus: true,
    refetchInterval: 15000,
  });

  const { data: interventions, isLoading: interventionsLoading } = useQuery < Intervention[] > ({
    queryKey: ["/api/interventions"],
  });

  const recentInterventions = interventions?.slice(0, 5) || [];

  const { data: sensors, isLoading: sensorsLoading } = useQuery({
    queryKey: ["/api/sensors"],
    queryFn: async () => await apiRequest("GET", "/api/sensors"),
    // keep sensors reasonably fresh
    refetchOnWindowFocus: false,
    refetchInterval: 20000,
  });

  const { data: owners } = useQuery({
    queryKey: ["/api/owners"],
    queryFn: async () => await apiRequest("GET", "/api/owners"),
    // owners rarely change in dev, keep cached
    refetchOnWindowFocus: false,
  });

  const ownersById = useMemo(() => {
    const map: Record<string | number, any> = {};
    (owners || []).forEach((o: any) => {
      map[o.id] = o;
    });
    return map;
  }, [owners]);

  const offlineSensors = (sensors || []).filter((s: any) => s.status === "Hors Service");

  if (statsLoading) {
    return (
      <div className="flex-1 overflow-auto">
        <div className="max-w-screen-xl mx-auto p-6 space-y-6">
          <div>
            <h1 className="text-3xl font-bold text-foreground">Dashboard</h1>
            <p className="text-muted-foreground mt-1">
              Vue d'ensemble de la plateforme Neo-Sousse 2030
            </p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {[1, 2, 3, 4].map((i) => (
              <Card key={i}>
                <CardHeader className="pb-2">
                  <Skeleton className="h-4 w-32" />
                </CardHeader>
                <CardContent>
                  <Skeleton className="h-10 w-20" />
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-auto">
    <div className="max-w-screen-xl mx-auto p-6 space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-foreground">Dashboard</h1>
            <p className="text-muted-foreground mt-1">
              Vue d'ensemble de la plateforme Neo-Sousse 2030
            </p>
          </div>
          <Button
            onClick={handleLaunchStreamlit}
            disabled={launchingStreamlit}
            className="bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 text-white font-semibold px-6 py-3 rounded-lg shadow-lg hover:shadow-xl transition-all duration-200 flex items-center gap-2"
          >
            {launchingStreamlit ? (
              <>
                <Loader2 size={18} className="animate-spin" />
                Lancement...
              </>
            ) : (
              <>
                <Play size={18} />
                Lancer Streamlit
              </>
            )}
          </Button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard
            title="Capteurs Actifs"
            value={stats?.activeSensors || 0}
            icon={Cpu}
            subtitle={`Sur ${stats?.totalSensors || 0} capteurs totaux`}
          />
          <StatCard
            title="Interventions Aujourd'hui"
            value={stats?.interventionsToday || 0}
            icon={Activity}
            subtitle={`${stats?.predictiveToday || 0} prédictives`}
          />
          <StatCard
            title="Score Engagement Moyen"
            value={stats?.avgEngagement || 0}
            icon={Users}
            subtitle={`Sur ${stats?.totalCitizens || 0} citoyens`}
          />
          <StatCard
            title="CO₂ Économisé"
            value={`${stats?.co2Saved || 0} kg`}
            icon={Leaf}
            subtitle="Ce mois-ci"
          />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Carte des Capteurs</CardTitle>
              </CardHeader>
              <CardContent>
                <div data-testid="map-sensors" className="w-full h-72 lg:h-96">
                  {/* Sousse map: shows sensors polled every 5s from backend */}
                  {/**
                   * Requires `leaflet` and `react-leaflet` packages:
                   * npm install leaflet react-leaflet
                   */}
                  <SousseMap />
                </div>
              </CardContent>
            </Card>

            {/* Alerts + Interventions grid moved below to span full page width */}
          </div>

          <div className="space-y-6">
            <TechniciansCard />
          </div>

        </div>

        {/* Full-width section: Alerts + Interventions side-by-side */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-6">
          <Card className="h-full">
            <CardHeader>
              <CardTitle>Alertes Récentes</CardTitle>
            </CardHeader>
            <CardContent className="h-80 overflow-y-auto pr-2" data-testid="list-recent-alerts">
              {sensorsLoading ? (
                <div className="space-y-2">
                  {[1, 2, 3].map((i) => (
                    <Skeleton key={i} className="h-6 w-full" />
                  ))}
                </div>
              ) : offlineSensors.length > 0 ? (
                <div className="space-y-3">
                  {offlineSensors.slice(0, 6).map((s: any) => (
                    <div
                      key={s.uuid || s.id}
                      className="flex items-center justify-between p-3 border rounded-md"
                    >
                      <div className="flex-1">
                        <div className="font-medium">{s.type || s.name || 'Capteur'}</div>
                        <div className="text-sm text-muted-foreground">{s.uuid || s.id}</div>
                        {(() => {
                          const owner = s.owner ?? ownersById[s.ownerId ?? s.owner_id];
                          if (!owner) return s.created_at ? (
                            <div className="text-xs text-muted-foreground mt-1">Installé: {format(new Date(s.created_at), 'dd/MM/yyyy')}</div>
                          ) : null;

                          return (
                            <div className="text-xs text-muted-foreground mt-1">
                              <div className="font-medium">{owner.name}</div>
                              <div>
                                {owner.phone && <span className="mr-2">📞 {owner.phone}</span>}
                                {owner.email && <span>✉️ {owner.email}</span>}
                              </div>
                            </div>
                          );
                        })()}
                        {s.created_at && (
                          <div className="text-xs text-muted-foreground mt-1">Installé: {format(new Date(s.created_at), 'dd/MM/yyyy')}</div>
                        )}
                      </div>
                      <div>
                        <span className="inline-flex items-center rounded-full bg-red-600 text-white px-2 py-0.5 text-xs font-semibold">Hors service</span>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-sm text-muted-foreground text-center py-8">
                  Aucune alerte pour le moment
                </div>
              )}
            </CardContent>
          </Card>

          <Card className="h-full">
            <CardHeader>
              <CardTitle>Interventions réalisées ce mois-ci, et leurs économie générée en CO₂</CardTitle>
            </CardHeader>
            <CardContent className="h-80 overflow-y-auto pr-2" data-testid="list-recent-interventions">
              {interventionsLoading ? (
                <div className="space-y-3">
                  {[1, 2, 3].map((i) => (
                    <Skeleton key={i} className="h-16 w-full" />
                  ))}
                </div>
              ) : recentInterventions.length > 0 ? (
                <div className="space-y-3">
                  {recentInterventions.map((intervention) => (
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
                  Aucune intervention enregistrée
                </div>
              )}
            </CardContent>
          </Card>
        </div>

      </div>
    </div>
  );
}
