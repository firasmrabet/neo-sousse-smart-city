import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

// Map backend/canonical vehicle type values to French display labels
export function vehicleTypeLabel(type?: string) {
  if (!type) return "Inconnu";
  const t = String(type).toLowerCase();
  if (t === "car" || t === "voiture") return "Voiture";
  if (t === "camion" || t === "truck") return "Camion";
  if (t === "autonomous_shuttle" || t === "navette_autonome" || t === "navette autonome") return "Navette Autonome";
  if (t.includes("shuttle")) return "Navette Autonome";
  // Fallback: capitalize first letter
  return type.charAt(0).toUpperCase() + type.slice(1);
}

// Map energy canonical values to French display labels
export function energyLabel(energy?: string) {
  if (!energy) return "Inconnu";
  const e = String(energy).toLowerCase();
  if (e === "electrique" || e === "electric") return "Électrique";
  if (e === "hybride" || e === "hybrid") return "Hybride";
  if (e === "hydrogene" || e === "hydrogene" || e === "hydrogen") return "Hydrogène";
  return energy.charAt(0).toUpperCase() + energy.slice(1);
}
