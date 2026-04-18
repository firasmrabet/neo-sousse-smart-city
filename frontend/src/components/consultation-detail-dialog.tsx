import React from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "./ui/dialog";
import { Button } from "./ui/button";
import { Calendar, User, Tag, Clock } from "lucide-react";
import { format } from "date-fns";
import { fr } from "date-fns/locale";

interface ConsultationProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  consultation: {
    id: number;
    topic: string;
    participationMode: string;
    participationDate?: string | Date;
    date?: string | Date;
    heure?: string;
    citizenName?: string;
    citizenId?: number;
  } | null;
}

export function ConsultationDetailDialog({ open, onOpenChange, consultation }: ConsultationProps) {
  if (!consultation) return null;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Détails de la Consultation</DialogTitle>
          <DialogDescription>
            Informations sur la participation
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6 py-4">
          <div className="space-y-1">
            <h3 className="font-medium text-lg leading-none">{consultation.topic}</h3>
            <div className="flex items-center text-sm text-muted-foreground">
              <Tag className="mr-1 h-3 w-3" />
              {consultation.participationMode}
            </div>
          </div>

          <div className="grid gap-4">
            <div className="flex items-center gap-3 p-3 rounded-lg border bg-card text-card-foreground shadow-sm">
              <User className="h-5 w-5 text-primary" />
              <div>
                <div className="text-xs text-muted-foreground">Participant</div>
                <div className="font-medium">{consultation.citizenName || "Anonyme"}</div>
              </div>
            </div>

            <div className="flex items-center gap-3 p-3 rounded-lg border bg-card text-card-foreground shadow-sm">
              <Calendar className="h-5 w-5 text-primary" />
              <div>
                <div className="text-xs text-muted-foreground">Date</div>
                <div className="font-medium">
                  {consultation.participationDate ? format(new Date(consultation.participationDate), "dd MMMM yyyy", { locale: fr }) : (consultation.date ? format(new Date(consultation.date), "dd MMMM yyyy", { locale: fr }) : "-")}
                </div>
              </div>
            </div>

            {consultation.heure && (
              <div className="flex items-center gap-3 p-3 rounded-lg border bg-card text-card-foreground shadow-sm">
                <Clock className="h-5 w-5 text-primary" />
                <div>
                  <div className="text-xs text-muted-foreground">Heure</div>
                  <div className="font-medium">{consultation.heure}</div>
                </div>
              </div>
            )}
          </div>

          <div className="flex justify-end">
            <Button onClick={() => onOpenChange(false)}>Fermer</Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
