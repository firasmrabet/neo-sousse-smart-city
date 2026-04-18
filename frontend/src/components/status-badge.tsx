import { Badge } from "./ui/badge";
import { cn } from "../lib/utils";

type SensorStatus = "Actif" | "En Maintenance" | "Hors Service";
type TechnicianStatus = "actif" | "inactif";

interface StatusBadgeProps {
  status: SensorStatus | TechnicianStatus | string;
  className?: string;
}

export function StatusBadge({ status, className }: StatusBadgeProps) {
  const getStatusConfig = (status: string) => {
    switch (status) {
      case "Actif":
        return {
          label: "Actif",
          className: "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300",
        };
      case "En Maintenance":
        return {
          label: "En Maintenance",
          className: "bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-300",
        };
      case "Hors Service":
        return {
          label: "Hors Service",
          className: "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300",
        };
      case "actif":
        return {
          label: "Actif",
          className: "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300",
        };
      case "inactif":
        return {
          label: "Inactif",
          className: "bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-300",
        };
      default:
        return {
          label: status,
          className: "bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-300",
        };
    }
  };

  const config = getStatusConfig(status);

  return (
    <Badge
      variant="secondary"
      className={cn("text-xs font-medium px-2.5 py-0.5", config.className, className)}
      data-testid={`badge-status-${status}`}
    >
      {config.label}
    </Badge>
  );
}
