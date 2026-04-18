import { useQuery } from '@tanstack/react-query';
import type { SensorMeasure } from '@shared/schema';

export function useSensorMeasurements(sensorId: string | undefined, limit: number = 100) {
  return useQuery({
    queryKey: ['sensor-measurements', sensorId, limit],
    queryFn: async () => {
      if (!sensorId) return [];
      
      const response = await fetch(
        `/api/sensor-measurements/${sensorId}?limit=${limit}`,
        { cache: 'no-store' }
      );
      
      if (!response.ok) {
        throw new Error('Failed to fetch measurements');
      }
      
      const data: SensorMeasure[] = await response.json();
      return data;
    },
    enabled: !!sensorId,
    staleTime: 0,
    refetchInterval: 30000, // Refetch every 30 seconds for real-time updates
  });
}

// Group measurements by type (grandeur)
export function groupMeasurementsByType(measurements: SensorMeasure[]) {
  return measurements.reduce((acc, m) => {
    const key = m.grandeur;
    if (!acc[key]) {
      acc[key] = [];
    }
    acc[key].push(m);
    return acc;
  }, {} as Record<string, SensorMeasure[]>);
}

// Format measurements for chart display
export function formatMeasurementsForChart(measurements: SensorMeasure[]) {
  return measurements.map((m, idx) => ({
    index: idx,
    value: parseFloat(String(m.value)),
    label: m.grandeur,
  }));
}
