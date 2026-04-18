import { useState, useMemo } from "react";
import { Plus, Grid3X3, List, MapPin, Cpu } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { useLocation } from "wouter";
import { apiRequest } from "../lib/queryClient";
import { Button } from "../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Input } from "../components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../components/ui/tabs";
import { StatusBadge } from "../components/status-badge";
import { Badge } from "../components/ui/badge";
import { Skeleton } from "../components/ui/skeleton";
import SousseMap from "../components/sousse-map";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "../components/ui/table";
import { CreateSensorDialog } from "../components/create-sensor-dialog";

interface Sensor {
  uuid: string;
  type: string;
  latitude: string | number;
  longitude: string | number;
  status: string;
  installationDate: string;
  ownerId: number;
}

const sensorTypeLabels: Record<string, string> = {
  "Qualité de l'air": "Qualité de l'Air",
  "Trafic": "Trafic",
  "Énergie": "Énergie",
  "Déchets": "Déchets",
  "Éclairage": "Éclairage",
};

const sensorTypeIcons = {
  "Qualité de l'air": "🌫️",
  "Trafic": "🚦",
  "Énergie": "⚡",
  "Déchets": "♻️",
  "Éclairage": "💡",
};

export default function Sensors() {
  const [view, setView] = useState < "grid" | "list" > ("grid");
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState < string > ("all");
  const [typeFilter, setTypeFilter] = useState < string > ("all");
  const [, setLocation] = useLocation();

  const { data: sensors, isLoading } = useQuery < Sensor[] > ({
    queryKey: ["/api/sensors"],
  });

  const { data: owners } = useQuery({
    queryKey: ["/api/owners"],
    queryFn: async () => await apiRequest("GET", "/api/owners"),
    refetchOnWindowFocus: false,
  });

  const ownersById = useMemo(() => {
    const map: Record<string | number, any> = {};
    (owners || []).forEach((o: any) => (map[o.id] = o));
    return map;
  }, [owners]);

  const filteredSensors = sensors?.filter((sensor) => {
    const matchesStatus = statusFilter === "all" || sensor.status === statusFilter;
    const matchesType = typeFilter === "all" || sensor.type === typeFilter;
    const ownerName = ownersById[sensor.ownerId]?.name || "";
    const matchesSearch = searchQuery === "" ||
      sensor.uuid.toLowerCase().includes(searchQuery.toLowerCase()) ||
      `${sensor.latitude}, ${sensor.longitude}`.includes(searchQuery) ||
      ownerName.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesStatus && matchesType && matchesSearch;
  }) || [];

  console.log(`Total capteurs chargés: ${sensors?.length}, Affichés: ${filteredSensors.length}`);

  return (
    <div className="w-full h-full flex flex-col">
      <div className="flex-1 overflow-auto">
        <div className="max-w-7xl mx-auto p-6 space-y-6">
          <div className="flex items-center justify-between gap-4 flex-wrap">
            <div>
              <h1 className="text-3xl font-bold text-foreground">Capteurs Intelligents</h1>
              <p className="text-muted-foreground mt-1">
                Gestion et surveillance des capteurs urbains
              </p>
            </div>
            <CreateSensorDialog />
          </div>

          <Card>
            <CardHeader className="pb-4">
              <div className="flex flex-col md:flex-row gap-4 justify-between">
                <div className="flex-1 max-w-md">
                  <Input
                    placeholder="Rechercher par UUID ou localisation..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    data-testid="input-search-sensors"
                    className="w-full"
                  />
                </div>
                <div className="flex gap-2 flex-wrap">
                  <Select value={typeFilter} onValueChange={setTypeFilter}>
                    <SelectTrigger className="w-40" data-testid="select-type-filter">
                      <SelectValue placeholder="Type" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">Tous les types</SelectItem>
                      <SelectItem value="Qualité de l'air">Qualité de l'Air</SelectItem>
                      <SelectItem value="Trafic">Trafic</SelectItem>
                      <SelectItem value="Énergie">Énergie</SelectItem>
                      <SelectItem value="Déchets">Déchets</SelectItem>
                      <SelectItem value="Éclairage">Éclairage</SelectItem>
                    </SelectContent>
                  </Select>
                  <Select value={statusFilter} onValueChange={setStatusFilter}>
                    <SelectTrigger className="w-40" data-testid="select-status-filter">
                      <SelectValue placeholder="Statut" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">Tous les statuts</SelectItem>
                      <SelectItem value="Actif">Actif</SelectItem>
                      <SelectItem value="En Maintenance">Maintenance</SelectItem>
                      <SelectItem value="Hors Service">Hors Service</SelectItem>
                    </SelectContent>
                  </Select>
                  <div className="flex gap-1 border rounded-md p-1">
                    <Button
                      variant={view === "grid" ? "secondary" : "ghost"}
                      size="icon"
                      onClick={() => setView("grid")}
                      data-testid="button-view-grid"
                      className="h-8 w-8"
                    >
                      <Grid3X3 className="w-4 h-4" />
                    </Button>
                    <Button
                      variant={view === "list" ? "secondary" : "ghost"}
                      size="icon"
                      onClick={() => setView("list")}
                      data-testid="button-view-list"
                      className="h-8 w-8"
                    >
                      <List className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <Tabs defaultValue="overview" className="w-full">
                <TabsList className="mb-4">
                  <TabsTrigger value="overview" data-testid="tab-overview">Vue d'ensemble</TabsTrigger>
                  <TabsTrigger value="map" data-testid="tab-map">Carte</TabsTrigger>
                </TabsList>
                <TabsContent value="overview" className="mt-0">
                  {isLoading ? (
                    <div className={view === "grid" ? "grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4" : "space-y-3"}>
                      {[1, 2, 3, 4, 5, 6].map((i) => (
                        <Skeleton key={i} className="h-40 w-full" />
                      ))}
                    </div>
                  ) : filteredSensors.length === 0 ? (
                    <div className="text-sm text-muted-foreground text-center py-12" data-testid="empty-sensors">
                      <Cpu className="w-12 h-12 mx-auto mb-4 text-muted-foreground/50" />
                      <p className="font-medium">Aucun capteur trouvé</p>
                      <p className="text-xs mt-1">Essayez d'ajuster vos filtres</p>
                    </div>
                  ) : view === "grid" ? (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                      {filteredSensors.map((sensor) => (
                        <Card
                          key={sensor.uuid}
                          className="hover-elevate cursor-pointer"
                          onClick={() => setLocation(`/sensors/${sensor.uuid}`)}
                          data-testid={`card-sensor-${sensor.uuid}`}
                        >
                          <CardHeader className="pb-3">
                            <div className="flex items-start justify-between gap-2">
                              <div className="flex items-center gap-2">
                                <div className="text-2xl">{sensorTypeIcons[sensor.type as keyof typeof sensorTypeIcons]}</div>
                                <div>
                                  <CardTitle className="text-sm font-medium">
                                    {sensorTypeLabels[sensor.type as keyof typeof sensorTypeLabels]}
                                  </CardTitle>
                                  <p className="text-xs text-muted-foreground mt-0.5">
                                    {sensor.uuid.substring(0, 8)}...
                                  </p>
                                </div>
                              </div>
                              <StatusBadge status={sensor.status} />
                            </div>
                          </CardHeader>
                          <CardContent className="space-y-2">
                            <div className="flex items-center gap-2 text-xs text-muted-foreground">
                              <MapPin className="w-3 h-3" />
                              <span>{sensor.latitude}, {sensor.longitude}</span>
                            </div>
                            <div className="text-xs text-muted-foreground">
                              Installé le {new Date(sensor.installationDate).toLocaleDateString('fr-FR')}
                            </div>
                            {(() => {
                              const owner = sensor.owner ?? ownersById[sensor.ownerId ?? sensor.owner_id];
                              if (!owner) return null;
                              return (
                                <div className="text-xs text-muted-foreground mt-1">
                                  <div className="font-medium">Propriétaire: {owner.name}</div>
                                  <div className="text-[11px]">
                                    {owner.phone && <span className="mr-2">📞 {owner.phone}</span>}
                                    {owner.email && <span>✉️ {owner.email}</span>}
                                  </div>
                                </div>
                              );
                            })()}
                          </CardContent>
                        </Card>
                      ))}
                    </div>
                  ) : (
                    <div className="rounded-md border">
                      <Table>
                        <TableHeader>
                          <TableRow className="hover:bg-transparent">
                            <TableHead className="font-semibold">Type</TableHead>
                            <TableHead className="font-semibold">UUID</TableHead>
                            <TableHead className="font-semibold">Localisation</TableHead>
                            <TableHead className="font-semibold">Statut</TableHead>
                            <TableHead className="font-semibold">Date Installation</TableHead>
                            <TableHead className="font-semibold">Propriétaire</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {filteredSensors.map((sensor) => (
                            <TableRow
                              key={sensor.uuid}
                              className="cursor-pointer hover:bg-muted"
                              onClick={() => setLocation(`/sensors/${sensor.uuid}`)}
                              data-testid={`row-sensor-${sensor.uuid}`}
                            >
                              <TableCell className="font-medium">
                                <div className="flex items-center gap-2">
                                  <span>{sensorTypeIcons[sensor.type as keyof typeof sensorTypeIcons]}</span>
                                  <span>{sensorTypeLabels[sensor.type as keyof typeof sensorTypeLabels]}</span>
                                </div>
                              </TableCell>
                              <TableCell className="text-xs font-mono">{sensor.uuid}</TableCell>
                              <TableCell className="text-sm">
                                {sensor.latitude}, {sensor.longitude}
                              </TableCell>
                              <TableCell>
                                <StatusBadge status={sensor.status} />
                              </TableCell>
                              <TableCell className="text-sm">
                                {new Date(sensor.installationDate).toLocaleDateString('fr-FR')}
                              </TableCell>
                              <TableCell className="text-sm">
                                {(() => {
                                  const owner = sensor.owner ?? ownersById[sensor.ownerId ?? sensor.owner_id];
                                  if (!owner) return '—';
                                  return owner.name + (owner.phone ? ` • ${owner.phone}` : '');
                                })()}
                              </TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </div>
                  )}
                </TabsContent>
                <TabsContent value="map" className="mt-0">
                  <div data-testid="map-view">
                    <SousseMap height="h-96" />
                  </div>
                </TabsContent>
              </Tabs>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
