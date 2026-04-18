import { useState } from "react";
import { Plus } from "lucide-react";
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
import { insertSensorSchema } from "../../../shared/schema";
import { z } from "zod";
import { useMutation } from "@tanstack/react-query";
import { apiRequest, queryClient } from "../lib/queryClient";
import { useToast } from "../hooks/use-toast";

const formSchema = insertSensorSchema.extend({
  // Owner inline fields (optional) - if provided we'll create owner first
  ownerName: z.string().optional().or(z.literal("")),
  ownerType: z.enum(["Municipalité", "Privé"]).optional(),
  ownerAddress: z.string().optional().or(z.literal("")),
  ownerPhone: z.string().optional().or(z.literal("")),
  ownerEmail: z.string().email().optional().or(z.literal("")),
});

type FormData = z.infer<typeof formSchema>;

export function CreateSensorDialog() {
  const [open, setOpen] = useState(false);
  const { toast } = useToast();

  const form = useForm < FormData > ({
    resolver: zodResolver(formSchema),
    defaultValues: {
      type: "Qualité de l'air",
      latitude: "",
      longitude: "",
      status: "Actif",
      installationDate: new Date().toISOString().split('T')[0],
      ownerId: 1,
      ownerName: "",
      ownerType: "Municipalité",
      ownerAddress: "",
      ownerPhone: "",
      ownerEmail: "",
    },
  });

  const createSensor = useMutation({
    mutationFn: async (data: FormData) => {
      return await apiRequest("POST", "/api/sensors", data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["/api/sensors"], exact: false });
      // also refresh dashboard stats so counts update everywhere
      queryClient.invalidateQueries({ queryKey: ["/api/dashboard/stats"], exact: false });
      toast({
        title: "Capteur créé",
        description: "Le nouveau capteur a été ajouté avec succès",
      });
      setOpen(false);
      form.reset();
    },
    onError: (error: Error) => {
      toast({
        title: "Erreur",
        description: error.message || "Impossible de créer le capteur",
        variant: "destructive",
      });
    },
  });

  const onSubmit = (data: FormData) => {
    (async () => {
      try {
        // Ensure installationDate is in ISO format (YYYY-MM-DD)
        const installationDate = data.installationDate instanceof Date
          ? data.installationDate.toISOString().split('T')[0]
          : typeof data.installationDate === 'string'
            ? data.installationDate
            : new Date(data.installationDate).toISOString().split('T')[0];

        let ownerId = Number(data.ownerId || 1);

        // If owner name/email provided, create a new owner first and use its id
        if (data.ownerName && data.ownerName.trim().length > 0) {
          try {
            const ownerPayload = {
              name: data.ownerName,
              address: data.ownerAddress || "",
              phone: data.ownerPhone || "",
              email: data.ownerEmail || `no-reply+${Date.now()}@example.com`,
              ownerType: data.ownerType || "Municipalité",
            } as any;

            const createdOwner = await apiRequest("POST", "/api/owners", ownerPayload);
            ownerId = createdOwner.id;
          } catch (ownerErr) {
            console.warn("Owner creation skipped, using default owner", ownerErr);
          }
        }

        // Create payload with only fields expected by insertSensorSchema
        const payload = {
          type: data.type,
          latitude: data.latitude ? parseFloat(String(data.latitude)) : undefined,
          longitude: data.longitude ? parseFloat(String(data.longitude)) : undefined,
          status: data.status,
          installationDate: installationDate,
          ownerId: ownerId || 1,
        } as any;

        createSensor.mutate(payload);
      } catch (err: any) {
        toast({ title: "Erreur", description: err?.message || "Erreur lors de la création", variant: "destructive" });
      }
    })();
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button data-testid="button-create-sensor">
          <Plus className="w-4 h-4 mr-2" />
          Nouveau Capteur
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Ajouter un Capteur</DialogTitle>
          <DialogDescription>
            Créez un nouveau capteur dans le système Neo-Sousse
          </DialogDescription>
        </DialogHeader>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            <FormField
              control={form.control}
              name="type"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Type de Capteur</FormLabel>
                  <Select onValueChange={field.onChange} defaultValue={field.value}>
                    <FormControl>
                      <SelectTrigger data-testid="select-sensor-type">
                        <SelectValue placeholder="Sélectionner un type" />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      <SelectItem value="Qualité de l'air">Qualité de l'Air</SelectItem>
                      <SelectItem value="Trafic">Trafic</SelectItem>
                      <SelectItem value="Énergie">Énergie</SelectItem>
                      <SelectItem value="Déchets">Déchets</SelectItem>
                      <SelectItem value="Éclairage">Éclairage</SelectItem>
                    </SelectContent>
                  </Select>
                  <FormMessage />
                </FormItem>
              )}
            />

            <div className="grid grid-cols-2 gap-4">
              <FormField
                control={form.control}
                name="latitude"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Latitude</FormLabel>
                    <FormControl>
                      <Input
                        placeholder="35.8256"
                        {...field}
                        data-testid="input-latitude"
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="longitude"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Longitude</FormLabel>
                    <FormControl>
                      <Input
                        placeholder="10.6406"
                        {...field}
                        data-testid="input-longitude"
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            <div className="space-y-2">
              <FormField
                control={form.control}
                name="ownerName"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Nom du Propriétaire</FormLabel>
                    <FormControl>
                      <Input placeholder="Nom du propriétaire" {...field} data-testid="input-owner-name" />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <div className="grid grid-cols-2 gap-4">
                <FormField
                  control={form.control}
                  name="ownerType"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Type du Propriétaire</FormLabel>
                      <Select onValueChange={field.onChange} defaultValue={field.value}>
                        <FormControl>
                          <SelectTrigger data-testid="select-owner-type">
                            <SelectValue placeholder="Type" />
                          </SelectTrigger>
                        </FormControl>
                        <SelectContent>
                          <SelectItem value="Municipalité">Municipalité</SelectItem>
                          <SelectItem value="Privé">Privé</SelectItem>
                        </SelectContent>
                      </Select>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <FormField
                  control={form.control}
                  name="ownerEmail"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Email du Propriétaire</FormLabel>
                      <FormControl>
                        <Input placeholder="contact@exemple.tn" {...field} data-testid="input-owner-email" />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <FormField
                  control={form.control}
                  name="ownerPhone"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Téléphone</FormLabel>
                      <FormControl>
                        <Input placeholder="216XXXXXXXX" {...field} data-testid="input-owner-phone" />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <FormField
                  control={form.control}
                  name="ownerAddress"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Adresse</FormLabel>
                      <FormControl>
                        <Input placeholder="Adresse du propriétaire" {...field} data-testid="input-owner-address" />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </div>
            </div>

            <FormField
              control={form.control}
              name="status"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Statut</FormLabel>
                  <Select onValueChange={field.onChange} defaultValue={field.value}>
                    <FormControl>
                      <SelectTrigger data-testid="select-status">
                        <SelectValue placeholder="Sélectionner un statut" />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      <SelectItem value="Actif">Actif</SelectItem>
                      <SelectItem value="En Maintenance">Maintenance</SelectItem>
                      <SelectItem value="Hors Service">Hors Service</SelectItem>
                    </SelectContent>
                  </Select>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="installationDate"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Date d'Installation</FormLabel>
                  <FormControl>
                    <Input
                      type="date"
                      {...field}
                      data-testid="input-installation-date"
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <div className="flex gap-3 justify-end">
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
                disabled={createSensor.isPending}
                data-testid="button-submit"
              >
                {createSensor.isPending ? "Création..." : "Créer"}
              </Button>
            </div>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
}
