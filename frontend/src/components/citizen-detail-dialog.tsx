import React from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "./ui/dialog";
import { Button } from "./ui/button";
import { useQuery } from "@tanstack/react-query";
import { apiRequest } from "../lib/queryClient";
import { Skeleton } from "./ui/skeleton";
import { Calendar, FileText } from "lucide-react";
import { format } from "date-fns";

interface CitizenProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  citizen: {
    id: number;
    name: string;
    address?: string | null;
    phone?: string | null;
    email?: string | null;
    engagementScore?: number;
    mobilityPrefs?: any;
  } | null;
}

export function CitizenDetailDialog({ open, onOpenChange, citizen }: CitizenProps) {
  const { data: consultations, isLoading: consultationsLoading } = useQuery({
    queryKey: ["/api/citizens", citizen?.id, "consultations"],
    queryFn: async () => {
      if (!citizen?.id) return [];
      return await apiRequest("GET", `/api/citizens/${citizen.id}/consultations`);
    },
    enabled: !!citizen?.id && open,
  });

  if (!citizen) return null;

  const mobility = typeof citizen.mobilityPrefs === "string"
    ? citizen.mobilityPrefs
    : JSON.stringify(citizen.mobilityPrefs || {}, null, 2);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Détails du Citoyen</DialogTitle>
          <DialogDescription>Informations complètes et historique des consultations</DialogDescription>
        </DialogHeader>

        <div className="space-y-4 mt-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <div className="text-xs text-muted-foreground">Nom complet</div>
              <div className="font-medium">{citizen.name}</div>
            </div>

            <div>
              <div className="text-xs text-muted-foreground">Score d'engagement</div>
              <div className="font-medium text-lg">{citizen.engagementScore ?? "-"}</div>
            </div>
          </div>

          <div>
            <div className="text-xs text-muted-foreground">Adresse</div>
            <div className="font-medium">{citizen.address || "-"}</div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <div className="text-xs text-muted-foreground">Téléphone</div>
              <div className="font-medium">{citizen.phone || "-"}</div>
            </div>
            <div>
              <div className="text-xs text-muted-foreground">Email</div>
              <div className="font-medium">{citizen.email || "-"}</div>
            </div>
          </div>

          <div>
            <div className="text-xs text-muted-foreground">Préférences mobilité</div>
            <pre className="font-mono text-xs bg-muted/5 p-2 rounded">{mobility}</pre>
          </div>

        

          <div className="flex justify-end pt-2">
            <Button variant="outline" onClick={() => onOpenChange(false)}>Fermer</Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}

export default CitizenDetailDialog;

