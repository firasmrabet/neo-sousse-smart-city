
import {
  owners, users, sensors, capteurs, sensorMeasures, technicians, interventions, interventionTechnicians,
  citizens, consultations, participations, vehicles, trips,
  type InsertUser,
  type Sensor, type DBSensor, type InsertSensor,
  type SensorMeasure, type InsertSensorMeasure,
  type Technician, type InsertTechnician,
  type Intervention, type InsertIntervention,
  type InterventionTechnician, type InsertInterventionTechnician,
  type Citizen, type InsertCitizen,
  type Consultation, type InsertConsultation,
  type Participation, type InsertParticipation,
  type Vehicle, type InsertVehicle,
  type Trip, type InsertTrip
} from "@shared/schema";
import { db, connectionError } from "./db";
import { eq, desc, sql, and, gte, lte, count } from "drizzle-orm";
// @ts-ignore
import { v4 as uuidv4 } from "uuid";

export interface IStorage {
  // Owners
  getOwners(): Promise<Owner[]>;
  getOwner(id: number): Promise<Owner | undefined>;
  createOwner(owner: InsertOwner): Promise<Owner>;

  // Sensors
  getSensors(): Promise<Sensor[]>;
  getSensor(uuid: string): Promise<Sensor | undefined>;
  createSensor(sensor: InsertSensor): Promise<Sensor>;
  updateSensor(uuid: string, sensor: Partial<InsertSensor>): Promise<Sensor | undefined>;
  deleteSensor(uuid: string): Promise<boolean>;

  // Sensor Measurements
  getSensorMeasurements(sensorId: string, limit?: number): Promise<SensorMeasure[]>;
  createSensorMeasurement(measurement: InsertSensorMeasure): Promise<SensorMeasure>;

  // Technicians
  getTechnicians(): Promise<Technician[]>;
  getTechnician(id: number): Promise<Technician | undefined>;
  createTechnician(technician: InsertTechnician): Promise<Technician>;

  // Interventions
  getInterventions(): Promise<Intervention[]>;
  getIntervention(id: number): Promise<Intervention | undefined>;
  createIntervention(intervention: InsertIntervention): Promise<Intervention>;

  // Intervention Technicians
  getInterventionTechnicians(interventionId: number): Promise<InterventionTechnician[]>;
  createInterventionTechnician(interventionTechnician: InsertInterventionTechnician): Promise<InterventionTechnician>;

  // Citizens
  getCitizens(): Promise<Citizen[]>;
  getCitizen(id: number): Promise<Citizen | undefined>;
  createCitizen(citizen: InsertCitizen): Promise<Citizen>;
  getTopCitizens(limit: number): Promise<Citizen[]>;

  // Consultations
  getConsultations(): Promise<Consultation[]>;
  createConsultation(consultation: InsertConsultation): Promise<Consultation>;
  getCitizenConsultations(citizenId: number): Promise<any[]>;

  // Vehicles
  getVehicles(): Promise<Vehicle[]>;
  getVehicle(plate: string): Promise<Vehicle | undefined>;
  createVehicle(vehicle: InsertVehicle): Promise<Vehicle>;

  // Trips
  getTrips(): Promise<Trip[]>;
  createTrip(trip: InsertTrip): Promise<Trip>;

  // Analytics
  getMostPollutedZones(hours: number): Promise<Array<{ zone: string; avgValue: string }>>;
  getSensorAvailabilityByZone(): Promise<Array<{ zone: string; activeCount: number; totalCount: number }>>;
  getPredictiveInterventionsStats(month: Date): Promise<{ count: number; totalCo2Saving: string }>;
  getTopCo2SavingTrips(limit: number): Promise<Trip[]>;
}

export class DatabaseStorage implements IStorage {
  // Owners
  async getOwners(): Promise<Owner[]> {
    return await db.select().from(owners);
  }

  async getOwner(id: number): Promise<Owner | undefined> {
    const [owner] = await db.select().from(owners).where(eq(owners.id, id));
    return owner || undefined;
  }

  async createOwner(insertOwner: InsertOwner): Promise<Owner> {
    await db.insert(owners).values(insertOwner);
    // Ensure email is not null/undefined before querying
    if (!insertOwner.email) {
      // Fallback: get the last inserted owner if email is missing (though it should be required)
      const [lastOwner] = await db.select().from(owners).orderBy(desc(owners.id)).limit(1);
      return lastOwner;
    }
    const result = await db.select().from(owners).where(eq(owners.email, insertOwner.email));
    return result[0];
  }

  // Sensors
  private mapToSensor(c: DBSensor, owner: Owner | undefined): Sensor {
    // Now using direct latitude/longitude columns
    const latitude = c.latitude ? parseFloat(c.latitude.toString()) : 0;
    const longitude = c.longitude ? parseFloat(c.longitude.toString()) : 0;

    return {
      uuid: c.uuid,
      type: c.type || "Qualité de l'air",
      latitude: isNaN(latitude) ? 0 : latitude,
      longitude: isNaN(longitude) ? 0 : longitude,
      status: c.status || "Actif",
      installationDate: c.installationDate ? new Date(c.installationDate) : null,
      ownerId: c.ownerId,
    };
  }

  private mapFromSensor(s: InsertSensor): any {
    return {
      uuid: uuidv4(), // will be overwritten if updating
      type: s.type || "Qualité de l'air",
      latitude: s.latitude,
      longitude: s.longitude,
      status: s.status || "Actif",
      installationDate: s.installationDate ? (s.installationDate instanceof Date ? s.installationDate : new Date(s.installationDate)) : new Date(),
      ownerId: s.ownerId || 1
    };
  }

  async getSensors(): Promise<Sensor[]> {
    // Use capteurs table instead of sensors
    const sensorsList = await db.select().from(capteurs);
    const ownersList = await db.select().from(owners);
    const ownersById = new Map<number, Owner>(ownersList.map((o) => [o.id, o]));

    return sensorsList.map((c) => this.mapToSensor(c, c.ownerId ? ownersById.get(c.ownerId) : undefined));
  }

  async getSensor(uuid: string): Promise<Sensor | undefined> {
    const [sensor] = await db.select().from(capteurs).where(eq(capteurs.uuid, uuid));
    if (!sensor) return undefined;
    const [owner] = await db.select().from(owners).where(eq(owners.id, sensor.ownerId));
    return this.mapToSensor(sensor, owner);
  }

  async createSensor(insertSensor: InsertSensor): Promise<Sensor> {
    console.log('[STORAGE-CREATE] Creating sensor in storage:', storage?.constructor?.name);
    console.log('[STORAGE-CREATE] db is:', db ? 'initialized' : 'NULL');
    
    const uuid = uuidv4();
    const dbSensor = { ...this.mapFromSensor(insertSensor), uuid };
    
    console.log('[STORAGE-CREATE] Inserting into capteurs:', dbSensor);
    await db.insert(capteurs).values(dbSensor);
    console.log('[STORAGE-CREATE] Insert completed');
    
    const result = await db.select().from(capteurs).where(eq(capteurs.uuid, uuid));
    console.log('[STORAGE-CREATE] Select result:', result?.length > 0 ? 'found' : 'NOT FOUND');

    // Fetch owner for return
    let owner: Owner | undefined;
    if (insertSensor.ownerId) {
      const [fetchedOwner] = await db.select().from(owners).where(eq(owners.id, insertSensor.ownerId));
      owner = fetchedOwner;
    }
    const returnedSensor = this.mapToSensor(result[0], owner);
    console.log('[STORAGE-CREATE] Returning sensor:', returnedSensor?.uuid);
    return returnedSensor;
  }

  async updateSensor(uuid: string, updateData: Partial<InsertSensor>): Promise<Sensor | undefined> {
    // We need to fetch current data to merge properly if partial update
    const [current] = await db.select().from(capteurs).where(eq(capteurs.uuid, uuid));
    if (!current) return undefined;

    const updates: any = {};
    if (updateData.type !== undefined) updates.type = updateData.type;
    if (updateData.status !== undefined) updates.status = updateData.status;
    if (updateData.installationDate !== undefined) updates.installationDate = new Date(updateData.installationDate);
    if (updateData.ownerId !== undefined) updates.ownerId = updateData.ownerId;

    // Handle coordinates update - now using separate columns
    if (updateData.latitude !== undefined) updates.latitude = updateData.latitude;
    if (updateData.longitude !== undefined) updates.longitude = updateData.longitude;

    await db.update(capteurs).set(updates).where(eq(capteurs.uuid, uuid));

    const result = await db.select().from(capteurs).where(eq(capteurs.uuid, uuid));
    let owner: Owner | undefined;
    if (result[0].ownerId) {
      const [fetchedOwner] = await db.select().from(owners).where(eq(owners.id, result[0].ownerId));
      owner = fetchedOwner;
    }
    return this.mapToSensor(result[0], owner);
  }

  async deleteSensor(uuid: string): Promise<boolean> {
    const result = await db.delete(capteurs).where(eq(capteurs.uuid, uuid));
    return (result as any).affectedRows > 0;
  }

  // Sensor Measurements
  async getSensorMeasurements(sensorId: string, limit: number = 100): Promise<SensorMeasure[]> {
    return await db.select()
      .from(sensorMeasures)
      .where(eq(sensorMeasures.sensorId, sensorId))
      .orderBy(desc(sensorMeasures.id))
      .limit(limit);
  }

  async createSensorMeasurement(insertMeasurement: InsertSensorMeasure): Promise<SensorMeasure> {
    await db.insert(sensorMeasures).values(insertMeasurement);
    const measurements = await db.select().from(sensorMeasures).orderBy(desc(sensorMeasures.id)).limit(1);
    return measurements[0];
  }

  // Technicians
  async getTechnicians(): Promise<Technician[]> {
    return await db.select().from(technicians);
  }

  async getTechnician(id: number): Promise<Technician | undefined> {
    const [technician] = await db.select().from(technicians).where(eq(technicians.id, id));
    return technician || undefined;
  }

  async createTechnician(insertTechnician: InsertTechnician): Promise<Technician> {
    try {
      await db.insert(technicians).values(insertTechnician);
      if (!insertTechnician.email) {
        const [last] = await db.select().from(technicians).orderBy(desc(technicians.id)).limit(1);
        return last;
      }
      const result = await db.select().from(technicians).where(eq(technicians.email, insertTechnician.email));
      return result[0];
    } catch (err: any) {
      console.error('[storage] createTechnician error:', err instanceof Error ? err.stack || err.message : err);
      // rethrow so caller (route) can respond appropriately
      throw err;
    }
  }

  // Interventions
  async getInterventions(): Promise<Intervention[]> {
    return await db.select().from(interventions).orderBy(desc(interventions.dateTime));
  }

  async getIntervention(id: number): Promise<Intervention | undefined> {
    const [intervention] = await db.select().from(interventions).where(eq(interventions.id, id));
    return intervention || undefined;
  }

  async createIntervention(insertIntervention: InsertIntervention): Promise<Intervention> {
    await db.insert(interventions).values(insertIntervention);
    const result = await db.select().from(interventions).orderBy(desc(interventions.id)).limit(1);
    return result[0];
  }

  // Intervention Technicians
  async getInterventionTechnicians(interventionId: number): Promise<InterventionTechnician[]> {
    return await db.select()
      .from(interventionTechnicians)
      .where(eq(interventionTechnicians.interventionId, interventionId));
  }

  async createInterventionTechnician(insertInterventionTechnician: InsertInterventionTechnician): Promise<InterventionTechnician> {
    await db.insert(interventionTechnicians).values(insertInterventionTechnician);
    const result = await db.select().from(interventionTechnicians).where(eq(interventionTechnicians.interventionId, insertInterventionTechnician.interventionId));
    return result[0];
  }

  // Citizens
  async getCitizens(): Promise<Citizen[]> {
    return await db.select().from(citizens);
  }

  async getCitizen(id: number): Promise<Citizen | undefined> {
    const [citizen] = await db.select().from(citizens).where(eq(citizens.id, id));
    return citizen || undefined;
  }

  async createCitizen(insertCitizen: InsertCitizen, consultationsData?: any[]): Promise<Citizen> {
    console.log(`[DEBUG] Creating citizen with ${consultationsData?.length || 0} consultations`);
    const [result] = await db.insert(citizens).values(insertCitizen);

    // ✅ FIX: ALWAYS get the last inserted citizen by ID, never by email
    // This ensures we get the correct citizen even if duplicate emails exist
    // Previous bug: querying by email would return the FIRST citizen with that email,
    // not the one we just inserted if multiple citizens share the same email
    const [citizen] = await db.select()
      .from(citizens)
      .orderBy(desc(citizens.id))
      .limit(1);

    if (!citizen) {
      throw new Error('Failed to create citizen');
    }

    console.log(`[DEBUG] Created citizen with ID: ${citizen.id}`);

    if (consultationsData && consultationsData.length > 0) {
      for (const c of consultationsData) {
        console.log("[DEBUG] Creating consultation: ", c);

        if (!citizen || !citizen.id) {
          console.error("[ERROR] Cannot create consultation without a valid citizen ID");
          continue;
        }

        // Create consultation WITH citizenId assigned to the current citizen
        const [consultationResult] = await db.insert(consultations).values({
          citizenId: citizen.id,  // ✅ CRITICAL: Assign consultation to the citizen
          topic: c.topic,
          mode: c.mode,
        });

        // ✅ FIX: Query for the SPECIFIC consultation we just created instead of relying on ORDER BY
        // This prevents race conditions when multiple citizens are created simultaneously
        const [createdConsultation] = await db.select()
          .from(consultations)
          .where(
            and(
              eq(consultations.citizenId, citizen.id),
              eq(consultations.topic, c.topic),
              eq(consultations.mode, c.mode)
            )
          )
          .orderBy(desc(consultations.id))  // Get the most recent match in case of duplicates
          .limit(1);

        console.log(`[DEBUG] Created consultation with ID: ${createdConsultation?.id} for citizen ${citizen.id}`);

        if (createdConsultation && citizen) {
          await db.insert(participations).values({
            citizenId: citizen.id,
            consultationId: createdConsultation.id,
            date: c.date ? new Date(c.date) : new Date(),
            heure: c.heure || new Date().toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' }),
          });
          console.log(`[DEBUG] Created participation for citizen ${citizen.id} and consultation ${createdConsultation.id} with heure: ${c.heure}`);
        }
      }
    }

    return citizen;
  }

  async getTopCitizens(limit: number): Promise<Citizen[]> {
    return await db.select()
      .from(citizens)
      .orderBy(desc(citizens.engagementScore))
      .limit(limit);
  }

  // Consultations
  async getConsultations(): Promise<any[]> {
    const results = await db
      .select({
        id: consultations.id,
        citizenId: consultations.citizenId,
        citizenName: citizens.name,
        topic: consultations.topic,
        mode: consultations.mode,
        participationDate: participations.date,
        participationMode: participations.heure,
      })
      .from(consultations)
      .leftJoin(citizens, eq(consultations.citizenId, citizens.id))
      .leftJoin(participations, eq(consultations.id, participations.consultationId))
      .orderBy(desc(consultations.id));

    return results;
  }

  async createConsultation(insertConsultation: InsertConsultation): Promise<Consultation> {
    // Insert the consultation
    await db.insert(consultations).values(insertConsultation);
    const result = await db.select().from(consultations).orderBy(desc(consultations.id)).limit(1);
    const consultation = result[0];

    // CRITICAL: Create participation record with the same citizenId
    if (consultation && insertConsultation.citizenId) {
      await db.insert(participations).values({
        citizenId: insertConsultation.citizenId,
        consultationId: consultation.id,
        date: new Date(),
        heure: new Date().toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' }),
      });
      console.log(`[DEBUG] Created participation for citizen ${insertConsultation.citizenId} and consultation ${consultation.id}`);
    }

    return consultation;
  }

  async getCitizenConsultations(citizenId: number): Promise<any[]> {
    const results = await db
      .select({
        id: consultations.id,
        topic: consultations.topic,
        mode: consultations.mode,
        citizenId: consultations.citizenId,
      })
      .from(consultations)
      .where(eq(consultations.citizenId, citizenId))
      .orderBy(desc(consultations.id));

    return results;
  }

  // Vehicles
  async getVehicles(): Promise<Vehicle[]> {
    return await db.select().from(vehicles);
  }

  async getVehicle(plate: string): Promise<Vehicle | undefined> {
    const [vehicle] = await db.select().from(vehicles).where(eq(vehicles.plate, plate));
    return vehicle || undefined;
  }

  async createVehicle(insertVehicle: InsertVehicle): Promise<Vehicle> {
    await db.insert(vehicles).values(insertVehicle);
    const result = await db.select().from(vehicles).where(eq(vehicles.plate, insertVehicle.plate));
    return result[0];
  }

  // Trips
  async getTrips(): Promise<Trip[]> {
    return await db.select().from(trips).orderBy(desc(trips.id));
  }

  async createTrip(insertTrip: InsertTrip): Promise<Trip> {
    await db.insert(trips).values(insertTrip);
    const result = await db.select().from(trips).orderBy(desc(trips.id)).limit(1);
    return result[0];
  }

  // Analytics
  async getMostPollutedZones(hours: number = 24): Promise<Array<{ zone: string; avgValue: string }>> {
    // 'zone' column removed from schema. Returning empty array for now.
    return [];
  }

  async getSensorAvailabilityByZone(): Promise<Array<{ zone: string; activeCount: number; totalCount: number }>> {
    try {
      // Get all sensors
      const allSensors = await db.select().from(sensors);

      // Define Sousse arrondissements based on coordinates
      // Sousse center: ~35.825°N, 10.636°E
      // Non-overlapping zones to ensure each sensor assigns to exactly one zone
      const zones = {
        'Centre': { minLat: 35.815, maxLat: 35.835, minLon: 10.620, maxLon: 10.650 },
        'Nord': { minLat: 35.835, maxLat: 36.100, minLon: 10.300, maxLon: 10.900 },
        'Sud': { minLat: 35.500, maxLat: 35.815, minLon: 10.300, maxLon: 10.900 },
        'Est': { minLat: 35.600, maxLat: 35.950, minLon: 10.650, maxLon: 11.200 },
        'Ouest': { minLat: 35.600, maxLat: 35.950, minLon: 10.300, maxLon: 10.620 },
      };

      // Categorize sensors by zone
      const zoneData: Record<string, { total: number; active: number }> = {};
      Object.keys(zones).forEach(zone => {
        zoneData[zone] = { total: 0, active: 0 };
      });

      for (const sensor of allSensors) {
        const lat = Number(sensor.latitude);
        const lon = Number(sensor.longitude);
        let assigned = false;

        // Try to assign sensor to exact zone match
        for (const [zoneName, bounds] of Object.entries(zones)) {
          if (lat >= bounds.minLat && lat <= bounds.maxLat &&
            lon >= bounds.minLon && lon <= bounds.maxLon) {
            zoneData[zoneName].total += 1;
            if (sensor.status === 'Actif') {
              zoneData[zoneName].active += 1;
            }
            assigned = true;
            break;
          }
        }

        // If not assigned to any zone, assign to closest zone
        if (!assigned) {
          let closestZone = 'Centre';
          let closestDistance = Infinity;

          for (const [zoneName, bounds] of Object.entries(zones)) {
            const zoneCenterLat = (bounds.minLat + bounds.maxLat) / 2;
            const zoneCenterLon = (bounds.minLon + bounds.maxLon) / 2;
            const distance = Math.sqrt(
              Math.pow(lat - zoneCenterLat, 2) +
              Math.pow(lon - zoneCenterLon, 2)
            );

            if (distance < closestDistance) {
              closestDistance = distance;
              closestZone = zoneName;
            }
          }

          zoneData[closestZone].total += 1;
          if (sensor.status === 'Actif') {
            zoneData[closestZone].active += 1;
          }
        }
      }

      // Convert to result format
      const result = Object.entries(zoneData)
        .filter(([_, data]) => data.total > 0) // Only include zones with sensors
        .map(([zone, data]) => ({
          zone,
          activeCount: data.active,
          totalCount: data.total,
        }))
        .sort((a, b) => a.zone.localeCompare(b.zone)); // Sort alphabetically

      return result;
    } catch (error) {
      console.error('[Storage] Error fetching sensor availability by zone:', error);
      return [];
    }
  }

  async getPredictiveInterventionsStats(month: Date): Promise<{ count: number; totalCo2Saving: string }> {
    const startOfMonth = new Date(month.getFullYear(), month.getMonth(), 1);
    const endOfMonth = new Date(month.getFullYear(), month.getMonth() + 1, 0, 23, 59, 59);

    const [result] = await db.select({
      count: count(),
      totalCo2Saving: sql<string>`COALESCE(CAST(SUM(${interventions.impactCo2}) AS CHAR), '0')`,
    })
      .from(interventions)
      .where(
        and(
          eq(interventions.type, 'Prédictive'), // Predictive interventions
          gte(interventions.dateTime, startOfMonth),
          lte(interventions.dateTime, endOfMonth)
        )
      );

    return {
      count: result?.count || 0,
      totalCo2Saving: result?.totalCo2Saving || "0"
    };
  }

  async getTopCo2SavingTrips(limit: number): Promise<Trip[]> {
    return await db.select().from(trips).orderBy(desc(trips.co2Saving)).limit(limit);
  }
}

// Determine which storage to use based on db connection
let storage: IStorage;

console.log('[STORAGE] Initializing storage...');
console.log('[STORAGE] connectionError:', connectionError?.message || 'null');
console.log('[STORAGE] db:', db ? 'initialized' : 'null');

if (connectionError || !db) {
  console.log('[STORAGE] ⚠️  Using in-memory storage (MySQL not available)');
  console.log('[STORAGE] Connection error details:', {
    hasError: !!connectionError,
    errorMessage: connectionError?.message,
    errorCode: (connectionError as any)?.code,
    dbIsNull: db === null
  });
  const { MemoryStorage } = await import("./storage-memory");
  storage = new MemoryStorage();
  console.log('[STORAGE] MemoryStorage initialized');
} else {
  console.log('[STORAGE] ✅ Using database storage (MySQL connected)');
  storage = new DatabaseStorage();
  console.log('[STORAGE] DatabaseStorage initialized');
}

console.log('[STORAGE] Storage initialization complete. Storage type:', storage?.constructor?.name || 'unknown');
export { storage };
