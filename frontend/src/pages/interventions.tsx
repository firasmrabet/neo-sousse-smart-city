import { Plus, Calendar, Clock, DollarSign } from "lucide-react";
import { useState } from "react";
import { Button } from "../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Input } from "../components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../components/ui/select";
import { Badge } from "../components/ui/badge";
import { useQuery } from "@tanstack/react-query";
import { Skeleton } from "../components/ui/skeleton";
import { CreateInterventionDialog } from "../components/create-intervention-dialog";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "../components/ui/table";
import { format } from "date-fns";

interface Intervention {
  id: number;
  sensorId: string;
  dateTime: Date;
  type: string;
  durationMinutes: number;
  cost: string;
  impactCo2: string;
}

export default function Interventions() {
  const { data: interventions, isLoading } = useQuery < Intervention[] > ({
    queryKey: ["/api/interventions"],
  });

  const [typeFilter, setTypeFilter] = useState < string > ("all");
  const [searchQuery, setSearchQuery] = useState < string > ("");

  const filteredInterventions = (interventions || []).filter((i) => {
    const matchesType = typeFilter === "all" || (i.type || "").toLowerCase() === typeFilter.toLowerCase();
    const q = searchQuery.trim().toLowerCase();
    if (!q) return matchesType;

    const idMatch = i.id.toString() === q;
    const sensorMatch = i.sensorId?.toLowerCase().includes(q);
    const typeMatch = i.type?.toLowerCase().includes(q);
    const dateMatch = new Date(i.dateTime).toLocaleString('fr-FR').toLowerCase().includes(q);
    const costMatch = i.cost?.toString().toLowerCase().includes(q);

    return matchesType && (idMatch || sensorMatch || typeMatch || dateMatch || costMatch);
  });

  const totalInterventions = interventions?.length || 0;
  const predictiveCount = interventions?.filter(i => i.type === "predictive").length || 0;
  const avgDuration = interventions?.length
    ? Math.round(interventions.reduce((sum, i) => sum + i.durationMinutes, 0) / interventions.length)
    : 0;
  const totalCost = interventions?.reduce((sum, i) => sum + parseFloat(i.cost), 0).toFixed(2) || "0.00";
  return (
    <div className="flex-1 overflow-auto">
      <div className="max-w-7xl mx-auto p-6 space-y-6">
        <div className="flex items-center justify-between gap-4 flex-wrap">
          <div>
            <h1 className="text-3xl font-bold text-foreground">Interventions</h1>
            <p className="text-muted-foreground mt-1">
              Suivi et gestion des interventions techniques
            </p>
          </div>
          <CreateInterventionDialog />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card className="hover-elevate">
            <CardHeader className="flex flex-row items-center justify-between gap-2 space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                Total ce Mois
              </CardTitle>
              <Calendar className="w-4 h-4 text-primary" />
            </CardHeader>
            <CardContent>
              {isLoading ? (
                <Skeleton className="h-10 w-20" />
              ) : (
                <>
                  <div className="text-3xl font-bold font-mono" data-testid="text-interventions-total">{totalInterventions}</div>
                  <p className="text-xs text-muted-foreground mt-1">{predictiveCount} prédictives</p>
                </>
              )}
            </CardContent>
          </Card>

          <Card className="hover-elevate">
            <CardHeader className="flex flex-row items-center justify-between gap-2 space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                Durée Moyenne
              </CardTitle>
              <Clock className="w-4 h-4 text-primary" />
            </CardHeader>
            <CardContent>
              {isLoading ? (
                <Skeleton className="h-10 w-24" />
              ) : (
                <>
                  <div className="text-3xl font-bold font-mono" data-testid="text-avg-duration">{avgDuration} min</div>
                  <p className="text-xs text-muted-foreground mt-1">Par intervention</p>
                </>
              )}
            </CardContent>
          </Card>

          <Card className="hover-elevate">
            <CardHeader className="flex flex-row items-center justify-between gap-2 space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                Coût Total
              </CardTitle>
              <DollarSign className="w-4 h-4 text-primary" />
            </CardHeader>
            <CardContent>
              {isLoading ? (
                <Skeleton className="h-10 w-28" />
              ) : (
                <>
                  <div className="text-3xl font-bold font-mono" data-testid="text-total-cost">{totalCost} TND</div>
                  <p className="text-xs text-muted-foreground mt-1">Ce mois-ci</p>
                </>
              )}
            </CardContent>
          </Card>
        </div>

        <Card>
          <CardHeader>
            <div className="flex flex-col md:flex-row gap-4 justify-between items-start md:items-center">
              <CardTitle>Liste des Interventions</CardTitle>
              <div className="flex gap-2 flex-wrap">
                <Select value={typeFilter} onValueChange={setTypeFilter}>
                  <SelectTrigger className="w-40" data-testid="select-type-filter">
                    <SelectValue placeholder="Type" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">Tous les types</SelectItem>
                    <SelectItem value="Prédictive">Prédictive</SelectItem>
                    <SelectItem value="Corrective">Corrective</SelectItem>
                    <SelectItem value="Curative">Curative</SelectItem>
                  </SelectContent>
                </Select>
                <Input
                  placeholder="Rechercher..."
                  className="w-60"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  data-testid="input-search-interventions"
                />
              </div>
            </div>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <div className="space-y-3">
                <Skeleton className="h-10 w-full" />
                <Skeleton className="h-10 w-full" />
                <Skeleton className="h-10 w-full" />
              </div>
            ) : !interventions || interventions.length === 0 ? (
              <div className="text-sm text-muted-foreground text-center py-12" data-testid="empty-interventions">
                <Calendar className="w-12 h-12 mx-auto mb-4 text-muted-foreground/50" />
                <p className="font-medium">Aucune intervention enregistrée</p>
                <p className="text-xs mt-1">Les interventions apparaîtront ici</p>
              </div>
            ) : filteredInterventions.length === 0 ? (
              <div className="text-sm text-muted-foreground text-center py-12" data-testid="empty-interventions-filtered">
                <Calendar className="w-12 h-12 mx-auto mb-4 text-muted-foreground/50" />
                <p className="font-medium">Aucune intervention correspondante</p>
                <p className="text-xs mt-1">Ajustez le filtre ou la recherche</p>
              </div>
            ) : (
              <div className="rounded-md border max-h-[400px] overflow-y-auto">
                <Table>
                  <TableHeader>
                    <TableRow className="hover:bg-transparent">
                      <TableHead className="font-semibold">Numero d'intervention</TableHead>
                      <TableHead className="font-semibold">Capteur</TableHead>
                      <TableHead className="font-semibold">Date & Heure</TableHead>
                      <TableHead className="font-semibold">Type</TableHead>
                      <TableHead className="font-semibold">Durée (min)</TableHead>
                      <TableHead className="font-semibold">Coût</TableHead>
                      <TableHead className="font-semibold">Impact CO₂</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {([...filteredInterventions].sort((a, b) => a.id - b.id)).map((i, idx) => (
                      <TableRow key={i.id} className="hover:bg-muted">
                        <TableCell className="font-mono text-xs">{idx + 1}</TableCell>
                        <TableCell className="text-xs font-mono">{i.sensorId}</TableCell>
                        <TableCell className="text-sm">{new Date(i.dateTime).toLocaleString('fr-FR')}</TableCell>
                        <TableCell>{i.type}</TableCell>
                        <TableCell>{i.durationMinutes}</TableCell>
                        <TableCell>{i.cost} TND</TableCell>
                        <TableCell>{i.impactCo2}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
