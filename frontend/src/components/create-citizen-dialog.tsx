import { useState } from "react";
import { Plus, X } from "lucide-react";
import { Button } from "./ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "./ui/dialog";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "./ui/form";
import { Input } from "./ui/input";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { insertCitizenSchema } from "../../../shared/schema";
import { z } from "zod";
import { useMutation } from "@tanstack/react-query";
import { apiRequest, queryClient } from "../lib/queryClient";
import { useToast } from "../hooks/use-toast";

type CitizenForm = z.infer<typeof insertCitizenSchema>;

type ConsultationInput = {
  date: string;
  heure: string;
  topic: string;
  mode: string;
};

export function CreateCitizenDialog() {
  const [open, setOpen] = useState(false);
  const { toast } = useToast();

  const form = useForm < CitizenForm > ({
    resolver: zodResolver(insertCitizenSchema),
    defaultValues: {
      name: "",
      address: "",
      phone: "",
      email: "",
      engagementScore: 50,
      mobilityPrefs: "",
    } as any,
  });

  const [consultations, setConsultations] = useState < ConsultationInput[] > ([]);
  const addConsultation = () => setConsultations(s => [...s, { date: new Date().toISOString().slice(0, 10), heure: new Date().toTimeString().slice(0, 5), topic: "", mode: "En ligne" }]);
  const removeConsultation = (i: number) => setConsultations(s => s.filter((_, idx) => idx !== i));
  const updateConsultation = (i: number, patch: Partial<ConsultationInput>) => setConsultations(s => s.map((c, idx) => idx === i ? { ...c, ...patch } : c));

  const createCitizen = useMutation({
    mutationFn: async (data: CitizenForm & { consultations?: ConsultationInput[] }) => {
      // Send citizen with embedded consultations - backend will handle creating both
      const citizen = await apiRequest("POST", "/api/citizens", data);
      return citizen;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["/api/citizens"], exact: false });
      queryClient.invalidateQueries({ queryKey: ["/api/consultations"], exact: false });
      queryClient.invalidateQueries({ queryKey: ["/api/citizens/top"], exact: false });
      queryClient.invalidateQueries({ queryKey: ["/api/dashboard/stats"], exact: false });
      toast({ title: "Citoyen ajouté", description: "Le citoyen et son historique ont été enregistrés" });
      setOpen(false);
      form.reset();
      setConsultations([]);
    },
    onError: (error: any) => {
      toast({ title: "Erreur", description: error?.message || "Impossible d'ajouter le citoyen", variant: "destructive" });
    }
  });

  const onSubmit = (data: CitizenForm) => {
    // Stringify mobilityPrefs for TEXT field storage
    let mobilityPrefsStr = "";
    if (typeof data.mobilityPrefs === 'string') {
      mobilityPrefsStr = data.mobilityPrefs;
    } else if (data.mobilityPrefs) {
      // If it's an object/array, stringify it
      mobilityPrefsStr = JSON.stringify(data.mobilityPrefs);
    }

    // Ensure numeric fields are numbers
    const normalized: any = {
      ...data,
      mobilityPrefs: mobilityPrefsStr,
      consultations
    };

    if (typeof normalized.engagementScore === 'string' && normalized.engagementScore !== '') {
      normalized.engagementScore = Number(normalized.engagementScore);
    }

    createCitizen.mutate(normalized);
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button data-testid="button-add-citizen">
          <Plus className="w-4 h-4 mr-2" /> Ajouter un Citoyen
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-2xl">
        <DialogHeader>
          <DialogTitle>Ajouter un Citoyen</DialogTitle>
          <DialogDescription>Créer un citoyen et renseigner son historique de consultations</DialogDescription>
        </DialogHeader>

        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            <FormField control={form.control} name="name" render={({ field }) => (
              <FormItem>
                <FormLabel>Nom complet</FormLabel>
                <FormControl>
                  <Input placeholder="Nom de citoyen" {...field} value={field.value || ""} data-testid="input-citizen-name" />
                </FormControl>
                <FormMessage />
              </FormItem>
            )} />

            <FormField control={form.control} name="address" render={({ field }) => (
              <FormItem>
                <FormLabel>Adresse</FormLabel>
                <FormControl>
                  <Input placeholder="Rue ..." {...field} value={field.value || ""} data-testid="input-citizen-address" />
                </FormControl>
                <FormMessage />
              </FormItem>
            )} />

            <div className="grid grid-cols-2 gap-2">
              <FormField control={form.control} name="phone" render={({ field }) => (
                <FormItem>
                  <FormLabel>Téléphone</FormLabel>
                  <FormControl>
                    <Input placeholder="+216 xx xxx xxx" {...field} value={field.value || ""} data-testid="input-citizen-phone" />
                  </FormControl>
                </FormItem>
              )} />
              <FormField control={form.control} name="email" render={({ field }) => (
                <FormItem>
                  <FormLabel>Email</FormLabel>
                  <FormControl>
                    <Input placeholder="ex@exemple.tn" {...field} value={field.value || ""} data-testid="input-citizen-email" />
                  </FormControl>
                </FormItem>
              )} />
            </div>

            <FormField control={form.control} name="engagementScore" render={({ field }) => (
              <FormItem>
                <FormLabel>Score d'engagement (0-100)</FormLabel>
                <FormControl>
                  <Input
                    type="number"
                    value={field.value ?? ""}
                    onChange={(e) => {
                      const v = e.target.value;
                      // keep empty string to allow clearing; otherwise store number
                      field.onChange(v === "" ? "" : Number(v));
                    }}
                    data-testid="input-citizen-score"
                  />
                </FormControl>
                <FormMessage />
              </FormItem>
            )} />

            <FormField control={form.control} name="mobilityPrefs" render={({ field }) => (
              <FormItem>
                <FormLabel>Préférences mobilité (JSON ou liste séparée par des virgules)</FormLabel>
                <FormControl>
                  <Input placeholder="Ex: vélo, marche" {...field} value={field.value || ""} data-testid="input-citizen-mobility" />
                </FormControl>
                <FormMessage />
              </FormItem>
            )} />

            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <div className="text-sm font-medium">Historique de consultations</div>
                <Button type="button" variant="ghost" onClick={addConsultation} data-testid="button-add-consultation">
                  <Plus className="w-4 h-4 mr-2" /> Ajouter une consultation
                </Button>
              </div>

              <div className="space-y-2">
                {consultations.map((c, idx) => (
                  <div key={idx} className="grid grid-cols-5 gap-2 items-end">
                    <div>
                      <label className="text-xs">Date</label>
                      <Input value={c.date} type="date" onChange={(e) => updateConsultation(idx, { date: e.target.value })} data-testid={`input-consultation-date-${idx}`} />
                    </div>
                    <div>
                      <label className="text-xs">Heure</label>
                      <Input value={c.heure} type="time" onChange={(e) => updateConsultation(idx, { heure: e.target.value })} data-testid={`input-consultation-heure-${idx}`} />
                    </div>
                    <div>
                      <label className="text-xs">Sujet</label>
                      <Input value={c.topic} onChange={(e) => updateConsultation(idx, { topic: e.target.value })} data-testid={`input-consultation-topic-${idx}`} />
                    </div>
                    <div>
                      <label className="text-xs">Mode</label>
                      <Input value={c.mode} onChange={(e) => updateConsultation(idx, { mode: e.target.value })} data-testid={`input-consultation-mode-${idx}`} />
                    </div>
                    <div className="flex items-center gap-2">
                      <Button type="button" variant="destructive" onClick={() => removeConsultation(idx)} data-testid={`button-remove-consultation-${idx}`}>
                        <X className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="flex gap-3 justify-end">
              <Button type="button" variant="outline" onClick={() => setOpen(false)} data-testid="button-cancel-citizen">Annuler</Button>
              <Button type="submit" disabled={createCitizen.isPending} data-testid="button-submit-citizen">{createCitizen.isPending ? "Création..." : "Créer"}</Button>
            </div>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
}