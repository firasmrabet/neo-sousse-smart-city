import React from "react";
import { Plus, Truck as TruckIcon, Leaf, Route, Zap } from "lucide-react";
import { Button } from "../components/ui/button";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { apiRequest } from "../lib/queryClient";
import { vehicleTypeLabel, energyLabel } from "../lib/utils";
import { CreateVehicleDialog } from "../components/create-vehicle-dialog";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Input } from "../components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../components/ui/select";
import { Badge } from "../components/ui/badge";
import { Skeleton } from "../components/ui/skeleton";

export default function Vehicles() {
  const [energyFilter, setEnergyFilter] = useState("all");
  const [searchQuery, setSearchQuery] = useState("");

  const { data: vehicles, isLoading } = useQuery({
    queryKey: ["/api/vehicles"],
    queryFn: async () => await apiRequest("GET", "/api/vehicles"),
  });

  const filteredVehicles = (vehicles || []).filter((v: any) => {
    if (energyFilter !== "all") {
      const vEnergy = String(v.energy || "").toLowerCase();
      const filterEnergy = energyFilter.toLowerCase();

      // Direct match or partial match for robustness
      if (!vEnergy.includes(filterEnergy) && vEnergy !== filterEnergy) {
        return false;
      }
    }
    if (!searchQuery) return true;
    const vehicleLabel = vehicleTypeLabel(v.vehicleType || v.vehicleType);
    const energyLbl = energyLabel(v.energy);
    return (v.plate || "").toLowerCase().includes(searchQuery.toLowerCase())
      || (vehicleLabel || "").toLowerCase().includes(searchQuery.toLowerCase())
      || (energyLbl || "").toLowerCase().includes(searchQuery.toLowerCase());
  }).sort((a: any, b: any) => (a.plate || "").localeCompare(b.plate || ""));

  const { data: trips, isLoading: isLoadingTrips } = useQuery({
    queryKey: ["/api/trips"],
    queryFn: async () => await apiRequest("GET", "/api/trips"),
  });

  const { data: topTrips, isLoading: topTripsLoading } = useQuery({
    queryKey: ["/api/analytics/top-co2-trips"],
    queryFn: async () => await apiRequest("GET", "/api/analytics/top-co2-trips?limit=10"),
  });

  
  const activeVehiclesCount = (vehicles || []).length;

  const todayStart = new Date();
  todayStart.setHours(0, 0, 0, 0);
  const todayStr = todayStart.toDateString(); 

  const tripsTodayCount = (trips || []).filter((t: any) => {
    const dateStr = t.date || t.Date || t.startTime || t.start_time;
    if (!dateStr) return false;
    const ts = new Date(dateStr);
    return ts.toDateString() === todayStr;
  }).length;

  // CO2 saved this month
  const now = new Date();
  const currentMonth = now.getMonth();
  const currentYear = now.getFullYear();

  const monthTrips = (trips || []).filter((t: any) => {
    const dateStr = t.date || t.Date || t.startTime || t.start_time;
    if (!dateStr) return false;
    const tripDate = new Date(dateStr);
    return tripDate.getMonth() === currentMonth && tripDate.getFullYear() === currentYear;
  });
  const co2Saved = monthTrips.reduce((sum: number, t: any) => {
    const val = t.co2Saving || t.co2_saving || t.ÉconomieCO2 || 0;
    return sum + (Number(val) || 0);
  }, 0);

  const electricCount = (vehicles || []).filter((v: any) => {
    const energy = String(v.energy || v.energy_type || "").toLowerCase();
    return energy === "électrique" || energy === "electrique";
  }).length;

  // Group trips by vehicleId (plate)
  const tripsByVehicle: Record<string, any[]> = (trips || []).reduce((acc: any, t: any) => {
    const key = t.vehicleId || t.vehicle_id || t.vehicle || "";
    if (!acc[key]) acc[key] = [];
    acc[key].push(t);
    return acc;
  }, {} as Record<string, any[]>);

  const [expanded, setExpanded] = useState < Record < string, boolean>> ({});
  const toggleExpand = (plate: string) => setExpanded(prev => ({ ...prev, [plate]: !prev[plate] }));

  return (
    <div className="flex-1 overflow-auto">
      <div className="max-w-7xl mx-auto p-6 space-y-6">
        <div className="flex items-center justify-between gap-4 flex-wrap">
          <div>
            <h1 className="text-3xl font-bold text-foreground">Flotte Municipale</h1>
            <p className="text-muted-foreground mt-1">
              Gestion des véhicules autonomes et suivi des trajets
            </p>
          </div>
          <CreateVehicleDialog />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card className="hover-elevate">
            <CardHeader className="flex flex-row items-center justify-between gap-2 space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                Véhicules Actifs
              </CardTitle>
              <TruckIcon className="w-4 h-4 text-primary" />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold font-mono" data-testid="text-total-vehicles">{activeVehiclesCount}</div>
              <p className="text-xs text-muted-foreground mt-1">Dans la flotte</p>
            </CardContent>
          </Card>

          <Card className="hover-elevate">
            <CardHeader className="flex flex-row items-center justify-between gap-2 space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                Trajets Aujourd'hui
              </CardTitle>
              <Route className="w-4 h-4 text-primary" />
            </CardHeader>
            <CardContent>
              {isLoadingTrips ? (
                <Skeleton className="h-8 w-16" />
              ) : (
                <>
                  <div className="text-3xl font-bold font-mono" data-testid="text-trips-today">{tripsTodayCount}</div>
                  <p className="text-xs text-muted-foreground mt-1">Trajets complétés</p>
                </>
              )}
            </CardContent>
          </Card>

          <Card className="hover-elevate">
            <CardHeader className="flex flex-row items-center justify-between gap-2 space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                CO₂ Économisé
              </CardTitle>
              <Leaf className="w-4 h-4 text-primary" />
            </CardHeader>
            <CardContent>
              {isLoadingTrips ? (
                <Skeleton className="h-8 w-24" />
              ) : (
                <>
                  <div className="text-3xl font-bold font-mono" data-testid="text-co2-saved">{co2Saved.toFixed(2)} kg</div>
                  <p className="text-xs text-muted-foreground mt-1">Ce mois-ci</p>
                </>
              )}
            </CardContent>
          </Card>

          <Card className="hover-elevate">
            <CardHeader className="flex flex-row items-center justify-between gap-2 space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                Électriques
              </CardTitle>
              <Zap className="w-4 h-4 text-primary" />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold font-mono" data-testid="text-electric-vehicles">{electricCount}</div>
              <p className="text-xs text-muted-foreground mt-1">Véhicules zéro émission</p>
            </CardContent>
          </Card>
        </div>

        <Card>
          <CardHeader>
            <div className="flex flex-col md:flex-row gap-4 justify-between items-start md:items-center">
              <CardTitle>Liste des Véhicules</CardTitle>
              <div className="flex gap-2 flex-wrap">
                <Select defaultValue="all" onValueChange={(v) => setEnergyFilter(v)}>
                  <SelectTrigger className="w-40" data-testid="select-energy-filter">
                    <SelectValue placeholder="Énergie" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">Toutes énergies</SelectItem>
                    <SelectItem value="Électrique">Électrique</SelectItem>
                    <SelectItem value="Hybride">Hybride</SelectItem>
                    <SelectItem value="Hydrogène">Hydrogène</SelectItem>
                  </SelectContent>
                </Select>
                <Input
                  placeholder="Rechercher par plaque..."
                  className="w-60"
                  data-testid="input-search-vehicles"
                  onChange={(e) => setSearchQuery(e.target.value)}
                />

              </div>
            </div>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <div>Chargement...</div>
            ) : filteredVehicles.length === 0 ? (
              <div className="text-sm text-muted-foreground text-center py-12" data-testid="empty-vehicles">
                <TruckIcon className="w-12 h-12 mx-auto mb-4 text-muted-foreground/50" />
                <p className="font-medium">Aucun véhicule trouvé</p>
                <p className="text-xs mt-1">Essayez d'ajouter un véhicule ou ajustez vos filtres</p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="min-w-full text-sm">
                  <thead>
                    <tr className="text-left text-muted-foreground">
                      <th className="px-4 py-2">Plaque</th>
                      <th className="px-4 py-2">Type</th>
                      <th className="px-4 py-2">Énergie</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredVehicles.map((v: any) => (
                      <React.Fragment key={v.plate}>
                        <tr key={v.plate} className="border-t">
                          <td className="px-4 py-2 font-mono">
                            <button className="underline" onClick={() => toggleExpand(v.plate)}>{v.plate}</button>
                          </td>
                          <td className="px-4 py-2">{vehicleTypeLabel(v.vehicleType)}</td>
                          <td className="px-4 py-2">{energyLabel(v.energy)}</td>
                        </tr>
                        {expanded[v.plate] && (
                          <tr key={v.plate + "-trips"} className="bg-muted/5">
                            <td colSpan={3} className="px-4 py-2">
                              <div className="text-sm font-medium mb-2">Trajets pour {v.plate}</div>
                              {(tripsByVehicle[v.plate] || []).length === 0 ? (
                                <div className="text-xs text-muted-foreground">Aucun trajet enregistré pour ce véhicule</div>
                              ) : (
                                <table className="w-full text-sm">
                                  <thead>
                                    <tr className="text-left text-muted-foreground">
                                      <th className="px-2 py-1">Origine</th>
                                      <th className="px-2 py-1">Destination</th>
                                      <th className="px-2 py-1">Durée (min)</th>
                                      <th className="px-2 py-1">Économie CO₂ (kg)</th>
                                    </tr>
                                  </thead>
                                  <tbody>
                                    {(tripsByVehicle[v.plate] || []).map((t: any, idx: number) => (
                                      <tr key={idx} className="border-t">
                                        <td className="px-2 py-1">{t.origin}</td>
                                        <td className="px-2 py-1">{t.destination}</td>
                                        <td className="px-2 py-1">{t.durationMinutes}</td>
                                        <td className="px-2 py-1">{t.co2Saving}</td>
                                      </tr>
                                    ))}
                                  </tbody>
                                </table>
                              )}
                            </td>
                          </tr>
                        )}
                      </React.Fragment>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </CardContent>
        </Card>

      </div>
    </div>
  );
}
