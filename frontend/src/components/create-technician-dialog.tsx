import { useState } from "react";
import { Plus } from "lucide-react";
import { Button } from "./ui/button";
import {
  Dialog,
  DialogContent,
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
import { insertTechnicianSchema } from "../../../shared/schema";
import { z } from "zod";
import { useMutation } from "@tanstack/react-query";
import { apiRequest, queryClient } from "../lib/queryClient";
import { useToast } from "../hooks/use-toast";

type FormData = z.infer<typeof insertTechnicianSchema>;

export function CreateTechnicianDialog() {
  const [open, setOpen] = useState(false);
  const [submitError, setSubmitError] = useState < string | null > (null);
  const { toast } = useToast();

  const form = useForm < FormData > ({
    resolver: zodResolver(insertTechnicianSchema),
    defaultValues: { name: "" },
  });

  const createTechnician = useMutation({
    mutationFn: async (data: FormData) => apiRequest("POST", "/api/technicians", data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["/api/technicians"], exact: false });
      queryClient.invalidateQueries({ queryKey: ["/api/dashboard/stats"], exact: false });
      toast({ title: "Technicien ajouté", description: "Le technicien a été enregistré" });
      setSubmitError(null);
      setOpen(false);
      form.reset();
    },
    onError: (err: any) => {
      const message = err?.message || String(err) || "Impossible d'ajouter le technicien";
      setSubmitError(message);
      toast({ title: "Erreur", description: message, variant: "destructive" });
    },
  });

  const onSubmit = async (data: FormData) => {
    console.log("CreateTechnicianDialog onSubmit", data);
    setSubmitError(null);
    try {
      await createTechnician.mutateAsync(data);
    } catch (err: any) {
      console.error("Error creating technician:", err);
      const message = err?.message || String(err) || "Erreur lors de la création";
      setSubmitError(message);
    }
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button data-testid="button-create-technician">
          <Plus className="w-4 h-4 mr-2" />
          Nouveau Technicien
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Ajouter un Technicien</DialogTitle>
        </DialogHeader>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            <FormField control={form.control} name="name" render={({ field }) => (
              <FormItem>
                <FormLabel>Nom</FormLabel>
                <FormControl>
                  <Input {...field} data-testid="input-tech-name" />
                </FormControl>
                <FormMessage />
              </FormItem>
            )} />
            <FormField control={form.control} name="numero" render={({ field }) => (
              <FormItem>
                <FormLabel>Numéro de téléphone</FormLabel>
                <FormControl>
                  <Input {...field} data-testid="input-tech-numero" placeholder="Ex: +216 XX XXX XXX" />
                </FormControl>
                <FormMessage />
              </FormItem>
            )} />

            <div className="flex gap-3 justify-end">
              <Button type="button" variant="outline" onClick={() => setOpen(false)}>Annuler</Button>
              <Button
                type="submit"
                disabled={createTechnician.isLoading}
                data-testid="button-submit-tech"
                onClick={(e) => {
                  // ensure the form submit handler is invoked even if the native submit doesn't fire
                  try {
                    e.preventDefault();
                    console.log("Create button clicked");
                    void form.handleSubmit(onSubmit)();
                  } catch (err) {
                    console.error("Error invoking submit:", err);
                  }
                }}
              >
                {createTechnician.isLoading ? "Création..." : "Créer"}
              </Button>
            </div>
            {submitError && (
              <div className="text-sm text-red-500 mt-2" role="alert">{submitError}</div>
            )}
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
}
