import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Input } from "../components/ui/input";
import { useQuery } from "@tanstack/react-query";
import { apiRequest } from "../lib/queryClient";
import { CreateTechnicianDialog } from "../components/create-technician-dialog";
import { ChevronDown, ChevronUp, Phone } from "lucide-react";

export default function Technicians() {
  const [searchQuery, setSearchQuery] = useState("");
  const [expandedId, setExpandedId] = useState<number | null>(null);

  const { data: technicians, isLoading } = useQuery({
    queryKey: ["/api/technicians"],
    queryFn: async () => await apiRequest("GET", "/api/technicians"),
  });

  const filtered = (technicians || []).filter((t: any) => {
    if (!searchQuery) return true;
    return t.name.toLowerCase().includes(searchQuery.toLowerCase()) || (t.email || "").toLowerCase().includes(searchQuery.toLowerCase());
  });

  const toggleExpanded = (id: number) => {
    setExpandedId(expandedId === id ? null : id);
  };

  return (
    <div className="flex-1 overflow-auto">
      <div className="max-w-7xl mx-auto p-6 space-y-6">
        <div className="flex items-center justify-between gap-4 flex-wrap">
          <div>
            <h1 className="text-3xl font-bold text-foreground">Techniciens</h1>
            <p className="text-muted-foreground mt-1">Gestion des techniciens intervenants</p>
          </div>
          <div className="flex gap-2">
            <CreateTechnicianDialog />
          </div>
        </div>

        <Card>
          <CardHeader>
            <div className="flex items-center justify-between gap-4">
              <CardTitle>Liste des Techniciens</CardTitle>
              <div className="flex gap-2">
                <Input placeholder="Rechercher par nom ou email" onChange={(e) => setSearchQuery(e.target.value)} />
              </div>
            </div>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <div>Chargement...</div>
            ) : filtered.length === 0 ? (
              <div className="text-sm text-muted-foreground text-center py-8">Aucun technicien trouvé</div>
            ) : (
              <div className="grid grid-cols-1 gap-2">
                {filtered.map((t: any) => (
                  <div key={t.id} className="border rounded-md overflow-hidden">
                    <div
                      onClick={() => toggleExpanded(t.id)}
                      className="p-3 flex justify-between items-center cursor-pointer hover:bg-muted/50 transition"
                    >
                      <div className="font-medium">{t.name}</div>
                      <div className="flex items-center gap-2">
                        {t.numero && <Phone className="w-4 h-4 text-muted-foreground" />}
                        {expandedId === t.id ? (
                          <ChevronUp className="w-5 h-5" />
                        ) : (
                          <ChevronDown className="w-5 h-5" />
                        )}
                      </div>
                    </div>
                    {expandedId === t.id && (
                      <div className="px-3 py-2 bg-muted/30 border-t">
                        {t.numero ? (
                          <div className="flex items-center gap-2 text-sm">
                            <Phone className="w-4 h-4 text-primary" />
                            <span className="font-medium">{t.numero}</span>
                          </div>
                        ) : (
                          <div className="text-sm text-muted-foreground">Aucun numéro enregistré</div>
                        )}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
