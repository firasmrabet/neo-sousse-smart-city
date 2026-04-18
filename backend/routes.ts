import type { Express } from "express"; // Force restart
import { createServer, type Server } from "http";
import { storage } from "./storage";
import { spawn } from "child_process";
import {
  insertOwnerSchema, insertSensorSchema, insertSensorMeasureSchema,
  insertTechnicianSchema, insertInterventionSchema, insertInterventionTechnicianSchema,
  insertCitizenSchema, insertConsultationSchema,
  insertVehicleSchema, insertTripSchema,
} from "@shared/schema";
import { db } from "./db";
import { participations } from "@shared/schema";

export async function registerRoutes(
  httpServer: Server,
  app: Express
): Promise<Server> {
  console.log('[ROUTES] Storage object:', storage);
  console.log('[ROUTES] Storage has getOwners?', typeof storage?.getOwners);

  // Owners
  app.get("/api/owners", async (_req, res) => {
    try {
      const owners = await storage.getOwners();
      res.json(owners);
    } catch (error: any) {
      console.error('[ROUTES] Error in /api/owners:', error);
      res.status(500).json({ error: error.message });
    }
  });

  app.get("/api/owners/:id", async (req, res) => {
    try {
      const id = parseInt(req.params.id);
      const owner = await storage.getOwner(id);
      if (!owner) {
        return res.status(404).json({ error: "Owner not found" });
      }
      res.json(owner);
    } catch (error: any) {
      res.status(500).json({ error: error.message });
    }
  });

  app.post("/api/owners", async (req, res) => {
    try {
      const data = insertOwnerSchema.parse(req.body);
      const owner = await storage.createOwner(data);
      res.status(201).json(owner);
    } catch (error: any) {
      res.status(400).json({ error: error.message });
    }
  });

  // Sensors
  app.get("/api/sensors", async (_req, res) => {
    try {
      const sensors = await storage.getSensors();
      res.json(sensors);
    } catch (error: any) {
      res.status(500).json({ error: error.message });
    }
  });

  app.get("/api/sensors/:uuid", async (req, res) => {
    try {
      const sensor = await storage.getSensor(req.params.uuid);
      if (!sensor) {
        return res.status(404).json({ error: "Sensor not found" });
      }
      res.json(sensor);
    } catch (error: any) {
      res.status(500).json({ error: error.message });
    }
  });

  app.post("/api/sensors", async (req, res) => {
    try {
      console.log("POST /api/sensors - Received body:", JSON.stringify(req.body, null, 2));
      const data = insertSensorSchema.parse(req.body);
      console.log("Parsed data:", JSON.stringify(data, null, 2));
      const sensor = await storage.createSensor(data);
      res.status(201).json(sensor);
    } catch (error: any) {
      console.error("POST /api/sensors - Error:", error);
      res.status(400).json({ error: error.message, details: error.errors });
    }
  });

  app.put("/api/sensors/:uuid", async (req, res) => {
    try {
      const data = insertSensorSchema.partial().parse(req.body);
      const sensor = await storage.updateSensor(req.params.uuid, data);
      if (!sensor) {
        return res.status(404).json({ error: "Sensor not found" });
      }
      res.json(sensor);
    } catch (error: any) {
      res.status(400).json({ error: error.message });
    }
  });

  app.delete("/api/sensors/:uuid", async (req, res) => {
    try {
      const deleted = await storage.deleteSensor(req.params.uuid);
      if (!deleted) {
        return res.status(404).json({ error: "Sensor not found" });
      }
      res.status(204).send();
    } catch (error: any) {
      res.status(500).json({ error: error.message });
    }
  });

  // Sensor Measurements
  app.get("/api/sensors/:sensorId/measurements", async (req, res) => {
    try {
      const limit = req.query.limit ? parseInt(req.query.limit as string) : 100;
      const measurements = await storage.getSensorMeasurements(req.params.sensorId, limit);
      res.json(measurements);
    } catch (error: any) {
      res.status(500).json({ error: error.message });
    }
  });

  app.post("/api/measurements", async (req, res) => {
    try {
      const data = insertSensorMeasureSchema.parse(req.body);
      const measurement = await storage.createSensorMeasurement(data);
      res.status(201).json(measurement);
    } catch (error: any) {
      res.status(400).json({ error: error.message });
    }
  });

  // Technicians
  app.get("/api/technicians", async (_req, res) => {
    try {
      const technicians = await storage.getTechnicians();
      res.json(technicians);
    } catch (error: any) {
      res.status(500).json({ error: error.message });
    }
  });

  app.post("/api/technicians", async (req, res) => {
    try {
      console.log("[POST /api/technicians] Received body:", JSON.stringify(req.body));
      const data = insertTechnicianSchema.parse(req.body);
      console.log("[POST /api/technicians] Validation passed, data:", JSON.stringify(data));
      const technician = await storage.createTechnician(data);
      console.log("[POST /api/technicians] Created technician:", JSON.stringify(technician));
      res.status(201).json(technician);
    } catch (error: any) {
      console.error("[POST /api/technicians] Error:", error.message || error);
      res.status(400).json({ error: error.message || String(error) });
    }
  });

  // Interventions
  app.get("/api/interventions", async (_req, res) => {
    try {
      const interventions = await storage.getInterventions();
      res.json(interventions);
    } catch (error: any) {
      res.status(500).json({ error: error.message });
    }
  });

  app.post("/api/interventions", async (req, res) => {
    try {
      console.log("[POST /api/interventions] Raw body:", JSON.stringify(req.body, null, 2));
      const { intervention, technicians } = req.body;

      console.log("[POST /api/interventions] Intervention data:", JSON.stringify(intervention, null, 2));
      console.log("[POST /api/interventions] Technicians data:", JSON.stringify(technicians, null, 2));

      // Validate intervention data
      const interventionData = insertInterventionSchema.parse(intervention);

      // Validate technicians array
      if (!Array.isArray(technicians) || technicians.length < 2) {
        return res.status(400).json({ error: "Au moins 2 techniciens sont requis" });
      }

      // Require at least 1 intervenant and at least 1 valideur
      const intervenants = technicians.filter((t: any) => t.role === 'Intervenant');
      const validators = technicians.filter((t: any) => t.role === 'Validateur');

      if (intervenants.length === 0) {
        return res.status(400).json({ error: "Au moins 1 technicien intervenant est requis" });
      }
      if (validators.length === 0) {
        return res.status(400).json({ error: "Au moins 1 valideur est requis" });
      }

      // Create intervention
      const createdIntervention = await storage.createIntervention(interventionData);

      // Add technicians
      for (const tech of technicians) {
        await storage.createInterventionTechnician({
          interventionId: createdIntervention.id,
          technicianId: tech.technicianId,
          role: tech.role,
        });
      }

      res.status(201).json(createdIntervention);
    } catch (error: any) {
      console.error("[POST /api/interventions] Error:", error);
      console.error("[POST /api/interventions] Error message:", error.message);
      console.error("[POST /api/interventions] Error stack:", error.stack);
      res.status(400).json({ error: error.message });
    }
  });

  app.get("/api/interventions/:id/technicians", async (req, res) => {
    try {
      const id = parseInt(req.params.id);
      const technicians = await storage.getInterventionTechnicians(id);
      res.json(technicians);
    } catch (error: any) {
      res.status(500).json({ error: error.message });
    }
  });

  // Citizens
  app.get("/api/citizens", async (_req, res) => {
    try {
      const citizens = await storage.getCitizens();
      res.json(citizens);
    } catch (error: any) {
      res.status(500).json({ error: error.message });
    }
  });

  app.get("/api/citizens/top", async (req, res) => {
    try {
      const limit = req.query.limit ? parseInt(req.query.limit as string) : 20;
      const citizens = await storage.getTopCitizens(limit);
      res.json(citizens);
    } catch (error: any) {
      res.status(500).json({ error: error.message });
    }
  });

  app.post("/api/citizens", async (req, res) => {
    try {
      const data = insertCitizenSchema.parse(req.body);
      // Extract consultations if provided (frontend may send this)
      const consultationsData = req.body.consultations || [];
      const citizen = await storage.createCitizen(data, consultationsData);
      res.status(201).json(citizen);
    } catch (error: any) {
      res.status(400).json({ error: error.message });
    }
  });

  // Consultations
  app.get("/api/consultations", async (_req, res) => {
    try {
      const consultations = await storage.getConsultations();
      res.json(consultations);
    } catch (error: any) {
      res.status(500).json({ error: error.message });
    }
  });

  app.post("/api/consultations", async (req, res) => {
    try {
      // CRITICAL: Ensure citizenId is provided and assigned correctly
      if (!req.body.citizenId) {
        return res.status(400).json({ error: "citizenId is required for creating a consultation" });
      }

      const data = insertConsultationSchema.parse(req.body);

      // Validate that citizenId is actually set in the data object
      if (!data.citizenId) {
        return res.status(400).json({ error: "citizenId must be provided in the request body" });
      }

      const consultation = await storage.createConsultation(data);
      res.status(201).json(consultation);
    } catch (error: any) {
      res.status(400).json({ error: error.message });
    }
  });

  app.get("/api/citizens/:id/consultations", async (req, res) => {
    try {
      const id = parseInt(req.params.id);
      console.log(`[DEBUG] Fetching consultations for citizen ID: ${id}`);
      const consultations = await storage.getCitizenConsultations(id);
      console.log(`[DEBUG] Found ${consultations.length} consultations:`, consultations);
      res.json(consultations);
    } catch (error: any) {
      console.error(`[ERROR] Failed to fetch consultations:`, error);
      res.status(500).json({ error: error.message });
    }
  });

  // DEBUG endpoint to check all participations
  app.get("/api/debug/participations", async (_req, res) => {
    try {
      const results = await db.select().from(participations);
      console.log(`[DEBUG] All participations:`, results);
      res.json(results);
    } catch (error: any) {
      res.status(500).json({ error: error.message });
    }
  });

  // Vehicles
  app.get("/api/vehicles", async (_req, res) => {
    try {
      const vehicles = await storage.getVehicles();
      res.json(vehicles);
    } catch (error: any) {
      res.status(500).json({ error: error.message });
    }
  });

  app.post("/api/vehicles", async (req, res) => {
    try {
      console.log("[POST /api/vehicles] Raw body:", JSON.stringify(req.body, null, 2));
      const data = insertVehicleSchema.parse(req.body);
      const vehicle = await storage.createVehicle(data);
      res.status(201).json(vehicle);
    } catch (error: any) {
      console.error("[POST /api/vehicles] Error:", error);
      console.error("[POST /api/vehicles] Error message:", error.message);
      res.status(400).json({ error: error.message });
    }
  });

  // Trips
  app.get("/api/trips", async (_req, res) => {
    try {
      const trips = await storage.getTrips();
      res.json(trips);
    } catch (error: any) {
      res.status(500).json({ error: error.message });
    }
  });

  app.post("/api/trips", async (req, res) => {
    try {
      const data = insertTripSchema.parse(req.body);
      const trip = await storage.createTrip(data);
      res.status(201).json(trip);
    } catch (error: any) {
      console.error("Trip creation error:", JSON.stringify(error, null, 2));
      res.status(400).json({ error: error.message });
    }
  });

  // Analytics
  app.get("/api/analytics/polluted-zones", async (req, res) => {
    try {
      const hours = req.query.hours ? parseInt(req.query.hours as string) : 24;
      const zones = await storage.getMostPollutedZones(hours);
      res.json(zones);
    } catch (error: any) {
      res.status(500).json({ error: error.message });
    }
  });

  app.get("/api/analytics/sensor-availability", async (_req, res) => {
    try {
      const availability = await storage.getSensorAvailabilityByZone();
      res.json(availability);
    } catch (error: any) {
      res.status(500).json({ error: error.message });
    }
  });

  app.get("/api/analytics/predictive-interventions", async (req, res) => {
    try {
      const month = req.query.month ? new Date(req.query.month as string) : new Date();
      const stats = await storage.getPredictiveInterventionsStats(month);
      res.json(stats);
    } catch (error: any) {
      res.status(500).json({ error: error.message });
    }
  });

  app.get("/api/analytics/top-co2-trips", async (req, res) => {
    try {
      const limit = req.query.limit ? parseInt(req.query.limit as string) : 10;
      const trips = await storage.getTopCo2SavingTrips(limit);
      res.json(trips);
    } catch (error: any) {
      res.status(500).json({ error: error.message });
    }
  });

  // Sensor Measurements (for real-time chart display)
  app.get("/api/sensor-measurements/:sensorId", async (req, res) => {
    try {
      const { sensorId } = req.params;
      const limit = req.query.limit ? parseInt(req.query.limit as string) : 100;

      const measurements = await storage.getSensorMeasurements(sensorId, limit);

      if (!measurements || measurements.length === 0) {
        return res.status(404).json({ error: "No measurements found for this sensor" });
      }

      res.json(measurements);
    } catch (error: any) {
      console.error('[ROUTES] Error in /api/sensor-measurements:', error);
      res.status(500).json({ error: error.message });
    }
  });

  // Dashboard stats
  app.get("/api/dashboard/stats", async (_req, res) => {
    try {
      const sensors = await storage.getSensors();
      const interventions = await storage.getInterventions();
      const citizens = await storage.getCitizens();
      const trips = await storage.getTrips();

      const activeSensors = sensors.filter(s => s.status === 'Actif').length;

      const today = new Date();
      today.setHours(0, 0, 0, 0);
      const interventionsToday = interventions.filter(i =>
        new Date(i.dateTime) >= today
      );

      const avgEngagement = citizens.length > 0
        ? Math.round(citizens.reduce((sum, c) => sum + c.engagementScore, 0) / citizens.length)
        : 0;

      const currentMonth = new Date();
      currentMonth.setDate(1);
      currentMonth.setHours(0, 0, 0, 0);
      const nextMonth = new Date(currentMonth);
      nextMonth.setMonth(nextMonth.getMonth() + 1);

      const monthTrips = trips.filter(t => {
        const tripDate = new Date(t.startTime);
        return tripDate >= currentMonth && tripDate < nextMonth;
      });
      const co2Saved = monthTrips.reduce((sum, t) => sum + parseFloat(t.co2Saving.toString()), 0);

      res.json({
        activeSensors,
        totalSensors: sensors.length,
        interventionsToday: interventionsToday.length,
        predictiveToday: interventionsToday.filter(i => i.type === 'predictive').length,
        avgEngagement,
        totalCitizens: citizens.length,
        co2Saved: co2Saved.toFixed(2),
      });
    } catch (error: any) {
      res.status(500).json({ error: error.message });
    }
  });

  // Launch Streamlit instance
  app.post("/api/streamlit/launch", async (req, res) => {
    try {
      const { app: appName = "professional", port = 8510 } = req.body;
      
      const projectPath = "c:\\Users\\Mrabet\\Desktop\\devops\\outils\\ps-main\\projet DB\\SensorLinker\\SensorLinker\\compiler-pm-phase2";
      const streamlitApp = "src/dashboard/app_v3.py";

      // Spawn Streamlit as a detached background process
      const proc = spawn("python", [
        "-m", "streamlit", "run", streamlitApp,
        `--server.port=${port}`,
        "--server.headless=true"
      ], {
        cwd: projectPath,
        detached: true,
        stdio: "ignore"
      });

      // Unref to allow parent process to exit
      proc.unref();

      // Wait a moment for Streamlit to start
      await new Promise(resolve => setTimeout(resolve, 2000));

      res.json({
        success: true,
        app: appName,
        port,
        url: `http://localhost:${port}`,
        message: `Streamlit ${appName} launched on port ${port}`
      });
    } catch (error: any) {
      console.error("[STREAMLIT] Error launching Streamlit:", error);
      res.status(500).json({ 
        error: error.message,
        details: "Failed to launch Streamlit process"
      });
    }
  });

  return httpServer;
}
