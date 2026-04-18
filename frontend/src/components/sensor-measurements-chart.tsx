import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useSensorMeasurements, groupMeasurementsByType } from "@/hooks/use-sensor-measurements";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from "recharts";
import { Loader2 } from "lucide-react";

interface SensorMeasurementsChartProps {
  sensorId: string | undefined;
  sensorName?: string;
  limit?: number;
}

export function SensorMeasurementsChart({
  sensorId,
  sensorName = "Capteur",
  limit = 50,
}: SensorMeasurementsChartProps) {
  const { data: measurements, isLoading, error } = useSensorMeasurements(sensorId, limit);

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Mesures en Temps Réel (24h)</CardTitle>
          <CardDescription>{sensorName}</CardDescription>
        </CardHeader>
        <CardContent className="flex items-center justify-center h-64">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </CardContent>
      </Card>
    );
  }

  if (error || !measurements || measurements.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Mesures en Temps Réel (24h)</CardTitle>
          <CardDescription>{sensorName}</CardDescription>
        </CardHeader>
        <CardContent className="flex items-center justify-center h-64 text-muted-foreground">
          <p>Aucune mesure disponible</p>
        </CardContent>
      </Card>
    );
  }

  // Group measurements by type for multi-line chart
  const groupedByType = groupMeasurementsByType(measurements);
  const chartData = measurements.map((m, idx) => ({
    index: idx,
    [m.grandeur]: parseFloat(String(m.value)),
  }));

  // Merge all values into single dataset by index
  const mergedData = measurements.reduce((acc, m, idx) => {
    if (!acc[idx]) {
      acc[idx] = { index: idx };
    }
    acc[idx][m.grandeur] = parseFloat(String(m.value));
    return acc;
  }, {} as Record<number, any>);

  const finalData = Object.values(mergedData);

  // Get distinct measurement types for legend
  const measurementTypes = Array.from(new Set(measurements.map(m => m.grandeur)));

  // Color palette for different measurement types
  const colors = [
    "#3b82f6", // blue
    "#ef4444", // red
    "#10b981", // green
    "#f59e0b", // amber
    "#8b5cf6", // purple
    "#ec4899", // pink
    "#06b6d4", // cyan
    "#14b8a6", // teal
  ];

  return (
    <Card>
      <CardHeader>
        <CardTitle>Mesures en Temps Réel (24h)</CardTitle>
        <CardDescription>
          {sensorName} - {measurements.length} mesures ({measurementTypes.length} types)
        </CardDescription>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={finalData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis 
              dataKey="index" 
              label={{ value: "Temps", position: "insideBottomRight", offset: -5 }}
            />
            <YAxis 
              label={{ value: "Valeur", angle: -90, position: "insideLeft" }}
            />
            <Tooltip 
              contentStyle={{
                backgroundColor: "rgba(0, 0, 0, 0.8)",
                border: "1px solid #ccc",
              }}
              formatter={(value: any) => {
                if (typeof value === 'number') {
                  return value.toFixed(2);
                }
                return value;
              }}
            />
            <Legend />
            {measurementTypes.map((type, idx) => (
              <Line
                key={type}
                type="monotone"
                dataKey={type}
                stroke={colors[idx % colors.length]}
                dot={false}
                isAnimationActive={true}
                strokeWidth={2}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
        
        {/* Summary Statistics */}
        <div className="mt-6 grid grid-cols-2 md:grid-cols-4 gap-4">
          {measurementTypes.map(type => {
            const typeData = measurements.filter(m => m.grandeur === type);
            const values = typeData.map(m => parseFloat(String(m.value)));
            const min = Math.min(...values);
            const max = Math.max(...values);
            const avg = (values.reduce((a, b) => a + b, 0) / values.length).toFixed(2);
            
            return (
              <div key={type} className="p-3 bg-secondary rounded-lg">
                <p className="text-sm font-medium text-muted-foreground truncate">{type}</p>
                <p className="text-xs text-muted-foreground mt-1">
                  Min: {min.toFixed(2)} | Max: {max.toFixed(2)}
                </p>
                <p className="text-sm font-semibold mt-1">Moy: {avg}</p>
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}
