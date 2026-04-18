import {
  type Sensor, type InsertSensor,
  type SensorMeasure, type InsertSensorMeasure,
  type Technician, type InsertTechnician,
  type Intervention, type InsertIntervention,
  type InterventionTechnician, type InsertInterventionTechnician,
  type Citizen, type InsertCitizen,
  type Consultation, type InsertConsultation,
  type Vehicle, type InsertVehicle,
  type Trip, type InsertTrip
} from "@shared/schema";
// @ts-ignore
import { v4 as uuidv4 } from "uuid";

// Type definitions for memory storage
type Owner = { id: number; name: string; email: string; phone?: string };
type InsertOwner = { name: string; email: string; phone?: string };

// In-memory storage for development when MySQL is unavailable
export class MemoryStorage {
  private owners: Map<number, Owner> = new Map();
  private sensors: Map<string, Sensor> = new Map();
  private measurements: Map<string, SensorMeasure[]> = new Map();
  private technicians: Map<number, Technician> = new Map();
  private interventions: Map<number, Intervention> = new Map();
  private interventionTechs: Map<number, InterventionTechnician[]> = new Map();
  private citizens: Map<number, Citizen> = new Map();
  private consultations: Map<number, Consultation> = new Map();
  private vehicles: Map<string, Vehicle> = new Map();
  private trips: Map<number, Trip> = new Map();

  private nextOwnerId = 1;
  private nextTechnicianId = 1;
  private nextInterventionId = 1;
  private nextCitizenId = 1;
  private nextConsultationId = 1;
  private nextTripId = 1;

  constructor() {
    this.seedSampleData();
  }

  private seedSampleData() {
    // Add some sample data for development
    const sampleSensor: Sensor = {
      uuid: uuidv4(),
      type: "Qualité de l'air",
      latitude: "35.825600",
      longitude: "10.637000",
      status: "Actif",
      installationDate: new Date("2024-01-01"),
      ownerId: 1,
    };
    this.sensors.set(sampleSensor.uuid, sampleSensor);

    const sampleVehicle: Vehicle = {
      plate: "TN-145263",
      vehicleType: "Navette Autonome",
      energy: "Électrique",
    };
    this.vehicles.set(sampleVehicle.plate, sampleVehicle);
  }

  // Owners
  async getOwners(): Promise<Owner[]> {
    return Array.from(this.owners.values());
  }

  async getOwner(id: number): Promise<Owner | undefined> {
    return this.owners.get(id);
  }

  async createOwner(insertOwner: InsertOwner): Promise<Owner> {
    const id = this.nextOwnerId++;
    const owner: Owner = { ...insertOwner, id };
    this.owners.set(id, owner);
    return owner;
  }

  // Sensors
  async getSensors(): Promise<Sensor[]> {
    return Array.from(this.sensors.values());
  }

  async getSensor(uuid: string): Promise<Sensor | undefined> {
    return this.sensors.get(uuid);
  }

  async createSensor(sensor: InsertSensor): Promise<Sensor> {
    const uuid = uuidv4();
    const newSensor = {
      ...sensor,
      uuid,
    } as unknown as Sensor;
    this.sensors.set(uuid, newSensor);
    return newSensor;
  }

  async updateSensor(uuid: string, updates: Partial<InsertSensor>): Promise<Sensor | undefined> {
    const sensor = this.sensors.get(uuid);
    if (!sensor) return undefined;
    const updated = { ...sensor, ...updates } as unknown as Sensor;
    this.sensors.set(uuid, updated);
    return updated;
  }

  async deleteSensor(uuid: string): Promise<boolean> {
    return this.sensors.delete(uuid);
  }

  // Sensor Measurements
  async getSensorMeasurements(sensorId: string, limit?: number): Promise<SensorMeasure[]> {
    const measurements = this.measurements.get(sensorId) || [];
    return limit ? measurements.slice(-limit) : measurements;
  }

  async createSensorMeasurement(measurement: InsertSensorMeasure): Promise<SensorMeasure> {
    const sensorId = String(measurement.sensorId);
    const existing = this.measurements.get(sensorId) || [];
    const newMeasure: SensorMeasure = {
      ...measurement,
      id: existing.length + 1,
      createdAt: new Date(),
    } as SensorMeasure;
    this.measurements.set(sensorId, [...existing, newMeasure]);
    return newMeasure;
  }

  // Technicians
  async getTechnicians(): Promise<Technician[]> {
    return Array.from(this.technicians.values());
  }

  async getTechnician(id: number): Promise<Technician | undefined> {
    return this.technicians.get(id);
  }

  async createTechnician(technician: InsertTechnician): Promise<Technician> {
    const id = this.nextTechnicianId++;
    const newTech = { ...technician, id } as Technician;
    this.technicians.set(id, newTech);
    return newTech;
  }

  // Interventions
  async getInterventions(): Promise<Intervention[]> {
    return Array.from(this.interventions.values());
  }

  async getIntervention(id: number): Promise<Intervention | undefined> {
    return this.interventions.get(id);
  }

  async createIntervention(intervention: InsertIntervention): Promise<Intervention> {
    const id = this.nextInterventionId++;
    const newIntervention = { ...intervention, id } as Intervention;
    this.interventions.set(id, newIntervention);
    return newIntervention;
  }

  // Intervention Technicians
  async getInterventionTechnicians(interventionId: number): Promise<InterventionTechnician[]> {
    return this.interventionTechs.get(interventionId) || [];
  }

  async createInterventionTechnician(interventionTechnician: InsertInterventionTechnician): Promise<InterventionTechnician> {
    const interventionId = interventionTechnician.interventionId;
    const existing = this.interventionTechs.get(interventionId) || [];
    const newRecord = { ...interventionTechnician, id: existing.length + 1 } as InterventionTechnician;
    this.interventionTechs.set(interventionId, [...existing, newRecord]);
    return newRecord;
  }

  // Citizens
  async getCitizens(): Promise<Citizen[]> {
    return Array.from(this.citizens.values());
  }

  async getCitizen(id: number): Promise<Citizen | undefined> {
    return this.citizens.get(id);
  }

  async createCitizen(citizen: InsertCitizen): Promise<Citizen> {
    const id = this.nextCitizenId++;
    const newCitizen = { ...citizen, id } as Citizen;
    this.citizens.set(id, newCitizen);
    return newCitizen;
  }

  async getTopCitizens(limit: number): Promise<Citizen[]> {
    return Array.from(this.citizens.values()).slice(0, limit);
  }

  // Consultations
  async getConsultations(): Promise<Consultation[]> {
    return Array.from(this.consultations.values());
  }

  async createConsultation(consultation: InsertConsultation): Promise<Consultation> {
    const id = this.nextConsultationId++;
    const newConsultation = { ...consultation, id } as Consultation;
    this.consultations.set(id, newConsultation);
    return newConsultation;
  }

  async getCitizenConsultations(citizenId: number): Promise<any[]> {
    return Array.from(this.consultations.values()).filter((c: any) => c.citizenId === citizenId);
  }

  // Vehicles
  async getVehicles(): Promise<Vehicle[]> {
    return Array.from(this.vehicles.values());
  }

  async getVehicle(plate: string): Promise<Vehicle | undefined> {
    return this.vehicles.get(plate);
  }

  async createVehicle(vehicle: InsertVehicle): Promise<Vehicle> {
    const newVehicle = { ...vehicle } as Vehicle;
    this.vehicles.set(vehicle.plate, newVehicle);
    return newVehicle;
  }

  // Trips
  async getTrips(): Promise<Trip[]> {
    return Array.from(this.trips.values());
  }

  async createTrip(trip: InsertTrip): Promise<Trip> {
    const id = this.nextTripId++;
    const newTrip = { ...trip, id } as Trip;
    this.trips.set(id, newTrip);
    return newTrip;
  }

  // Analytics
  async getMostPollutedZones(hours: number): Promise<Array<{ zone: string; avgValue: string }>> {
    // Return sample data
    return [
      { zone: "downtown", avgValue: "85" },
      { zone: "airport", avgValue: "72" },
    ];
  }

  async getSensorAvailabilityByZone(): Promise<Array<{ zone: string; activeCount: number; totalCount: number }>> {
    return [
      { zone: "downtown", activeCount: 8, totalCount: 10 },
      { zone: "airport", activeCount: 5, totalCount: 6 },
    ];
  }

  async getPredictiveInterventionsStats(month: Date): Promise<{ count: number; totalCo2Saving: string }> {
    return { count: 12, totalCo2Saving: "1250" };
  }

  async getTopCo2SavingTrips(limit: number): Promise<Trip[]> {
    return Array.from(this.trips.values()).slice(0, limit);
  }
}
