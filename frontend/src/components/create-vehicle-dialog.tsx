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
import { insertVehicleSchema } from "../../../shared/schema";
import { z } from "zod";
import { useMutation } from "@tanstack/react-query";
import { apiRequest, queryClient } from "../lib/queryClient";
import { useToast } from "../hooks/use-toast";

type FormData = z.infer<typeof insertVehicleSchema>;

type TripInput = {
  origin: string;
  destination: string;
  durationMinutes: number | string;
  co2Saving: number | string;
};

export function CreateVehicleDialog() {
  const [open, setOpen] = useState(false);
  const { toast } = useToast();

  const form = useForm < FormData > ({
    resolver: zodResolver(insertVehicleSchema),
    defaultValues: {
      plate: "",
      // use canonical values for backend while showing French labels
      vehicleType: "navette_autonome",
      energy: "Électrique",
    },
  });

  const [trips, setTrips] = useState < TripInput[] > ([]);

  const addEmptyTrip = () => setTrips((s) => [...s, { origin: "", destination: "", durationMinutes: "", co2Saving: "" }]);
  const removeTrip = (idx: number) => setTrips((s) => s.filter((_, i) => i !== idx));
  const updateTrip = (idx: number, patch: Partial<TripInput>) => setTrips((s) => s.map((t, i) => i === idx ? { ...t, ...patch } : t));

  const createVehicle = useMutation({
    mutationFn: async (data: FormData & { trips?: TripInput[] }) => {
      // Extract trips from data and create vehicle without them
      const { trips: tripsToCreate, ...vehicleData } = data;

      // Create vehicle first
      const vehicle = await apiRequest("POST", "/api/vehicles", vehicleData);

      // If trips provided, create them linking to the vehicle plate
      if (tripsToCreate && tripsToCreate.length > 0) {
        const createTripPromises = tripsToCreate.map((t) => {
          const tripPayload = {
            vehicleId: vehicleData.plate,
            origin: t.origin,
            destination: t.destination,
            startTime: new Date().toISOString(),
            durationMinutes: Number(t.durationMinutes) || 0,
            co2Saving: String(t.co2Saving || "0"),
          };
          return apiRequest("POST", "/api/trips", tripPayload);
        });
        await Promise.all(createTripPromises);
      }
      return vehicle;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["/api/vehicles"], exact: false });
      queryClient.invalidateQueries({ queryKey: ["/api/trips"], exact: false });
      queryClient.invalidateQueries({ queryKey: ["/api/dashboard/stats"], exact: false });
      toast({ title: "Véhicule ajouté", description: "Le véhicule et ses trajets ont été enregistrés" });
      setOpen(false);
      form.reset();
      setTrips([]);
    },
    onError: (error: Error) => {
      const errorMessage = error.message || "";
      let description = "Impossible d'ajouter le véhicule";

      // Check for duplicate plate number error
      if (errorMessage.includes("Duplicate entry") && errorMessage.includes("PRIMARY")) {
        description = "Cette plaque d'immatriculation existe déjà dans la base de données.";
      } else if (errorMessage) {
        description = errorMessage;
      }

      toast({ title: "Erreur", description, variant: "destructive" });
    },
  });

  const onSubmit = (data: FormData) => {
    // Attach trips array to payload
    createVehicle.mutate({ ...data, trips });
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button data-testid="button-add-vehicle">
          <Plus className="w-4 h-4 mr-2" />
          Ajouter un Véhicule
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Ajouter un Véhicule</DialogTitle>
          <DialogDescription>Enregistrez un véhicule dans la flotte municipale</DialogDescription>
        </DialogHeader>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            <FormField
              control={form.control}
              name="plate"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Plaque</FormLabel>
                  <FormControl>
                    <Input placeholder="TN-1234" {...field} data-testid="input-plate" required />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="vehicleType"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Type de véhicule</FormLabel>
                  <Select onValueChange={field.onChange} defaultValue={field.value}>
                    <FormControl>
                      <SelectTrigger data-testid="select-vehicle-type">
                        <SelectValue placeholder="Type de véhicule" />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      <SelectItem value="navette_autonome">Navette Autonome</SelectItem>
                      <SelectItem value="camion">Camion</SelectItem>
                      <SelectItem value="voiture">Voiture</SelectItem>
                    </SelectContent>
                  </Select>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="energy"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Énergie</FormLabel>
                  <Select onValueChange={field.onChange} defaultValue={field.value}>
                    <FormControl>
                      <SelectTrigger data-testid="select-energy">
                        <SelectValue placeholder="Type d'énergie" />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      <SelectItem value="Électrique">Électrique</SelectItem>
                      <SelectItem value="Hybride">Hybride</SelectItem>
                      <SelectItem value="Hydrogène">Hydrogène</SelectItem>
                    </SelectContent>
                  </Select>
                  <FormMessage />
                </FormItem>
              )}
            />

            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <div className="text-sm font-medium">Trajets associés</div>
                <Button type="button" variant="ghost" onClick={addEmptyTrip} data-testid="button-add-trip">
                  <Plus className="w-4 h-4 mr-2" /> Ajouter un trajet
                </Button>
              </div>

              <div className="space-y-2">
                {trips.map((t, idx) => (
                  <div key={idx} className="grid grid-cols-4 gap-2 items-end">
                    <div>
                      <label className="text-xs">Origine</label>
                      <Input value={t.origin} onChange={(e) => updateTrip(idx, { origin: e.target.value })} data-testid={`input-trip-origin-${idx}`} />
                    </div>
                    <div>
                      <label className="text-xs">Destination</label>
                      <Input value={t.destination} onChange={(e) => updateTrip(idx, { destination: e.target.value })} data-testid={`input-trip-destination-${idx}`} />
                    </div>
                    <div>
                      <label className="text-xs">Durée (min)</label>
                      <Input value={String(t.durationMinutes)} onChange={(e) => updateTrip(idx, { durationMinutes: e.target.value })} data-testid={`input-trip-duration-${idx}`} />
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="flex-1">
                        <label className="text-xs">Économie CO₂ (kg)</label>
                        <Input value={String(t.co2Saving)} onChange={(e) => updateTrip(idx, { co2Saving: e.target.value })} data-testid={`input-trip-co2-${idx}`} />
                      </div>
                      <Button type="button" variant="destructive" onClick={() => removeTrip(idx)} data-testid={`button-remove-trip-${idx}`}>
                        <X className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>
                ))}
              </div>

              <div className="flex gap-3 justify-end">
                <Button type="button" variant="outline" onClick={() => setOpen(false)} data-testid="button-cancel">
                  Annuler
                </Button>
                <Button type="submit" disabled={createVehicle.isPending} data-testid="button-submit-vehicle">
                  {createVehicle.isPending ? "Création..." : "Créer"}
                </Button>
              </div>
            </div>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
}
