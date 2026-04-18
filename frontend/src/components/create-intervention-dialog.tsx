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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "./ui/select";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { insertInterventionSchema } from "../../../shared/schema";
import { z } from "zod";
import { useMutation, useQuery } from "@tanstack/react-query";
import { apiRequest, queryClient } from "../lib/queryClient";
import { useToast } from "../hooks/use-toast";
import { Badge } from "./ui/badge";

interface Sensor {
  uuid: string;
  type: string;
}

interface Technician {
  id: number;
  name: string;
  certification: string;
  status?: string;
}

interface SelectedTechnician {
  id: number;
  role: "Intervenant" | "Validateur";
}

const formSchema = insertInterventionSchema.extend({
  technicians: z.array(
    z.object({
      id: z.number(),
      role: z.enum(["Intervenant", "Validateur"]),
    })
  ).min(2, "Au moins 2 techniciens requis")
    .refine(
      (techs) => techs.some((t) => t.role === "Intervenant"),
      "Au moins 1 technicien intervenant requis"
    )
    .refine(
      (techs) => techs.some((t) => t.role === "Validateur"),
      "Au moins 1 valideur requis"
    ),
});

type FormData = z.infer<typeof formSchema>;

export function CreateInterventionDialog() {
  const [open, setOpen] = useState(false);
  const { toast } = useToast();
  const [selectedTechs, setSelectedTechs] = useState < SelectedTechnician[] > ([]);

  const { data: sensors } = useQuery < Sensor[] > ({
    queryKey: ["/api/sensors"],
  });

  const { data: technicians } = useQuery < Technician[] > ({
    queryKey: ["/api/technicians"],
  });

  const activeTechnicians = technicians?.filter(t => (t.status ?? 'actif') === "actif") || [];

  const form = useForm < FormData > ({
    resolver: zodResolver(formSchema),
    defaultValues: {
      sensorId: "",
      dateTime: new Date().toISOString().slice(0, 16),
      type: "Prédictive",
      durationMinutes: 30,
      cost: "100.00",
      impactCo2: "2.50",
      technicians: [],
    },
  });

  const createIntervention = useMutation({
    mutationFn: async (payload: any) => {
      return await apiRequest("POST", "/api/interventions", payload);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["/api/interventions"] });
      // also refresh dashboard stats so counts update everywhere
      queryClient.invalidateQueries({ queryKey: ["/api/dashboard/stats"] });
      toast({
        title: "Intervention créée",
        description: "L'intervention a été programmée avec succès",
      });
      setOpen(false);
      form.reset();
      setSelectedTechs([]);
    },
    onError: (error: Error) => {
      toast({
        title: "Erreur",
        description: error.message || "Impossible de créer l'intervention",
        variant: "destructive",
      });
    },
  });

  const addTechnician = (techId: number, role: "Intervenant" | "Validateur") => {
    const existing = selectedTechs.find((t) => t.id === techId);
    if (existing) {
      existing.role = role;
    } else {
      selectedTechs.push({ id: techId, role });
    }
    const newTechs = [...selectedTechs];
    setSelectedTechs(newTechs);
    form.setValue("technicians", newTechs);
    form.trigger("technicians");
  };

  const removeTechnician = (techId: number) => {
    const newTechs = selectedTechs.filter((t) => t.id !== techId);
    setSelectedTechs(newTechs);
    form.setValue("technicians", newTechs);
    form.trigger("technicians");
  };

  const updateTechnicianRole = (techId: number, newRole: "Intervenant" | "Validateur") => {
    const tech = selectedTechs.find((t) => t.id === techId);
    if (tech) {
      tech.role = newRole;
      const newTechs = [...selectedTechs];
      setSelectedTechs(newTechs);
      form.setValue("technicians", newTechs);
      form.trigger("technicians");
    }
  };

  const onSubmit = (data: FormData) => {
    const payload = {
      intervention: {
        sensorId: data.sensorId,
        dateTime: data.dateTime,
        type: data.type,
        durationMinutes: data.durationMinutes,
        cost: data.cost,
        impactCo2: data.impactCo2,
      },
      technicians: data.technicians.map((t) => ({
        technicianId: t.id,
        role: t.role,
      })),
    };

    createIntervention.mutate(payload);
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button data-testid="button-create-intervention">
          <Plus className="w-4 h-4 mr-2" />
          Nouvelle Intervention
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Planifier une Intervention</DialogTitle>
          <DialogDescription>
            Créez une nouvelle intervention (min. 2 techniciens requis avec rôles définis)
          </DialogDescription>
        </DialogHeader>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            <FormField
              control={form.control}
              name="sensorId"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Capteur</FormLabel>
                  <Select onValueChange={field.onChange} defaultValue={field.value}>
                    <FormControl>
                      <SelectTrigger data-testid="select-sensor">
                        <SelectValue placeholder="Sélectionner un capteur" />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      {sensors?.map((sensor) => (
                        <SelectItem key={sensor.uuid} value={sensor.uuid}>
                          {sensor.type} - {sensor.uuid.substring(0, 8)}...
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <FormMessage />
                </FormItem>
              )}
            />

            <div className="grid grid-cols-2 gap-4">
              <FormField
                control={form.control}
                name="type"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Type</FormLabel>
                    <Select onValueChange={field.onChange} defaultValue={field.value}>
                      <FormControl>
                        <SelectTrigger data-testid="select-type">
                          <SelectValue placeholder="Type d'intervention" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        <SelectItem value="Prédictive">Prédictive</SelectItem>
                        <SelectItem value="Corrective">Corrective</SelectItem>
                        <SelectItem value="Curative">Curative</SelectItem>
                      </SelectContent>
                    </Select>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="dateTime"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Date et Heure</FormLabel>
                    <FormControl>
                      <Input
                        type="datetime-local"
                        {...field}
                        data-testid="input-datetime"
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            <div className="grid grid-cols-3 gap-4">
              <FormField
                control={form.control}
                name="durationMinutes"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Durée (min)</FormLabel>
                    <FormControl>
                      <Input
                        type="number"
                        {...field}
                        onChange={(e) => field.onChange(parseInt(e.target.value))}
                        data-testid="input-duration"
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="cost"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Coût (TND)</FormLabel>
                    <FormControl>
                      <Input
                        {...field}
                        data-testid="input-cost"
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="impactCo2"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Impact CO₂ (kg)</FormLabel>
                    <FormControl>
                      <Input
                        {...field}
                        data-testid="input-co2"
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            <div className="space-y-3">
              <FormLabel>Techniciens (min. 2 requis: 1 intervenant + 1 valideur)</FormLabel>
              <div className="space-y-2">
                {selectedTechs.length > 0 && (
                  <div className="space-y-2 mb-3 p-3 bg-slate-50 rounded-lg">
                    {selectedTechs.map((techSelected) => {
                      const tech = technicians?.find(t => t.id === techSelected.id);
                      return tech ? (
                        <div key={techSelected.id} className="flex items-center justify-between gap-2">
                          <span className="text-sm font-medium">{tech.name}</span>
                          <div className="flex items-center gap-2">
                            <Select
                              value={techSelected.role}
                              onValueChange={(value) => updateTechnicianRole(techSelected.id, value as "Intervenant" | "Validateur")}
                            >
                              <SelectTrigger className="w-32 h-8">
                                <SelectValue />
                              </SelectTrigger>
                              <SelectContent>
                                <SelectItem value="Intervenant">Intervenant</SelectItem>
                                <SelectItem value="Validateur">Valideur</SelectItem>
                              </SelectContent>
                            </Select>
                            <button
                              type="button"
                              onClick={() => removeTechnician(techSelected.id)}
                              className="text-destructive hover:text-destructive/80"
                            >
                              <X className="w-4 h-4" />
                            </button>
                          </div>
                        </div>
                      ) : null;
                    })}
                  </div>
                )}

                <Select onValueChange={(value) => addTechnician(parseInt(value), "Intervenant")}>
                  <SelectTrigger data-testid="select-technician">
                    <SelectValue placeholder="Ajouter un technicien..." />
                  </SelectTrigger>
                  <SelectContent>
                    {activeTechnicians.map((tech) => (
                      <SelectItem
                        key={tech.id}
                        value={tech.id.toString()}
                        disabled={selectedTechs.some(t => t.id === tech.id)}
                      >
                        {tech.name} - {tech.certification}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              {form.formState.errors.technicians && (
                <p className="text-sm text-destructive">
                  {form.formState.errors.technicians.message}
                </p>
              )}
            </div>

            <div className="flex gap-3 justify-end pt-4">
              <Button
                type="button"
                variant="outline"
                onClick={() => setOpen(false)}
                data-testid="button-cancel"
              >
                Annuler
              </Button>
              <Button
                type="submit"
                disabled={
                  createIntervention.isPending ||
                  selectedTechs.length < 2 ||
                  !selectedTechs.some(t => t.role === "Intervenant") ||
                  !selectedTechs.some(t => t.role === "Validateur")
                }
                data-testid="button-submit"
                title={
                  selectedTechs.length < 2
                    ? "Minimum 2 techniciens requis"
                    : !selectedTechs.some(t => t.role === "Intervenant")
                      ? "Au moins 1 intervenant requis"
                      : !selectedTechs.some(t => t.role === "Validateur")
                        ? "Au moins 1 valideur requis"
                        : ""
                }
              >
                {createIntervention.isPending ? "Création..." : "Créer"}
              </Button>
            </div>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
}
