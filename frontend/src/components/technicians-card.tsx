import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { useQuery } from "@tanstack/react-query";
import { apiRequest } from "../lib/queryClient";
import { Phone } from "lucide-react";

export function TechniciansCard() {
  const { data: technicians, isLoading } = useQuery({
    queryKey: ["/api/technicians"],
    queryFn: async () => await apiRequest("GET", "/api/technicians"),
  });

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Phone className="w-5 h-5" />
          Techniciens Disponibles
        </CardTitle>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="text-sm text-muted-foreground">Chargement...</div>
        ) : (technicians || []).length === 0 ? (
          <div className="text-sm text-muted-foreground">Aucun technicien</div>
        ) : (
          <div className="space-y-3 max-h-80 overflow-y-auto pr-2">
            {(technicians || []).map((t: any) => (
              <div key={t.id} className="p-3 border rounded-lg hover:bg-muted/50 transition">
                <div className="flex items-start justify-between gap-3">
                  <div className="flex-1">
                    <div className="font-medium text-foreground">{t.name}</div>
                    {t.numero && (
                      <div className="text-sm text-muted-foreground flex items-center gap-1 mt-1">
                        <Phone className="w-3.5 h-3.5" />
                        {t.numero}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
