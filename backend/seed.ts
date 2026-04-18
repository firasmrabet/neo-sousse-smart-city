import { db } from "./db";
import { eq } from "drizzle-orm";
import {
  owners, sensors, sensorMeasures, technicians, interventions, interventionTechnicians,
  citizens, consultations, vehicles, trips,
} from "@shared/schema";

async function seed() {
  console.log("🌱 Seeding database with Smart City Sousse data...");

  try {
    
    console.log("Creating owners...");
    const ownersData = [
      {
        name: "Municipalite Sousse",
        address: "Rue principale, Sousse",
        phone: "+21612345678",
        email: "contact@municipalite-sousse.tn",
        ownerType: "municipalite",
      },
      {
        name: "Municipalité de Neo-Sousse",
        address: "Hotel de Ville, Neo-Sousse",
        phone: "+216 71 000 000",
        email: "contact@neo-sousse.tn",
        ownerType: "municipalite",
      },
      {
        name: "GreenTech Partners",
        address: "Zone Industrielle, Sousse",
        phone: "+216 73 111 222",
        email: "support@greentech.tn",
        ownerType: "prive",
      },
      {
        name: "firas mrabet",
        address: "monastir",
        phone: "26521249",
        email: "firasmrabet112@gmail.com",
        ownerType: "prive",
      },
      {
        name: "eniso",
        address: "sousse",
        phone: "26256478",
        email: "ecolee976@gmail.com",
        ownerType: "municipalite",
      },
      {
        name: "4c",
        address: "sousse",
        phone: "26256478",
        email: "firasmrabet115@gmail.com",
        ownerType: "prive",
      },
    ];

    for (const ownerData of ownersData) {
      try {
        await db.insert(owners).values(ownerData);
      } catch (err: any) {
        if (err && err.code === 'ER_DUP_ENTRY') {
          // already exists, ignore
        } else {
          throw err;
        }
      }
    }

    const allOwners = await db.select().from(owners);
    const municipality = allOwners.find(o => o.email === 'contact@municipalite-sousse.tn') || allOwners[0];
    const greentech = allOwners.find(o => o.email === 'support@greentech.tn') || allOwners[2];;

    // Create sensors from SQL data
    console.log("Creating sensors...");
    const sensorsData = [
      { uuid: "092c6c1f-3f83-4081-9bdd-9a3ca01aea7f", type: "air", latitude: "35.828000", longitude: "10.635000", status: "actif", installationDate: "2025-01-15", ownerId: allOwners[1]?.id || 1 },
      { uuid: "1a88684b-77b4-48e9-b665-f7aa231de1d7", type: "eclairage", latitude: "66.222222", longitude: "2.666667", status: "maintenance", installationDate: "2025-10-25", ownerId: allOwners[0]?.id || 1 },
      { uuid: "208694dd-8b2b-44af-b4ad-a615230ed353", type: "air", latitude: "35.825600", longitude: "10.640700", status: "actif", installationDate: "2025-11-28", ownerId: allOwners[0]?.id || 1 },
      { uuid: "3b8c7fc0-cbdd-4db4-ba8b-ba7428288a39", type: "eclairage", latitude: "35.838000", longitude: "10.630000", status: "hors_service", installationDate: "2024-12-15", ownerId: allOwners[1]?.id || 1 },
      { uuid: "3ebde8b6-56e5-487b-b335-010ff94f67e4", type: "dechets", latitude: "35.830000", longitude: "10.625000", status: "actif", installationDate: "2025-01-20", ownerId: allOwners[2]?.id || 1 },
      { uuid: "4125fb07-d0c7-4fe5-879b-edc78c9706d7", type: "air", latitude: "35.828000", longitude: "10.635000", status: "actif", installationDate: "2025-01-15", ownerId: allOwners[1]?.id || 1 },
      { uuid: "440de941-d50c-4fa3-a636-a1082ccf8c61", type: "energie", latitude: "35.835000", longitude: "10.615000", status: "actif", installationDate: "2025-02-10", ownerId: allOwners[1]?.id || 1 },
      { uuid: "4f0fd45a-82c9-4d82-814a-75ac3ef939d1", type: "energie", latitude: "35.835000", longitude: "10.615000", status: "actif", installationDate: "2025-02-10", ownerId: allOwners[1]?.id || 1 },
      { uuid: "6ab147a0-07c0-4279-8072-9000dc6dd028", type: "energie", latitude: "35.835000", longitude: "10.615000", status: "actif", installationDate: "2025-02-10", ownerId: allOwners[1]?.id || 1 },
      { uuid: "6b1e756e-4ed4-453c-9ed6-46faee2af2d1", type: "air", latitude: "35.825600", longitude: "10.640600", status: "actif", installationDate: "2025-01-10", ownerId: allOwners[1]?.id || 1 },
      { uuid: "6badbb62-1f30-458b-859b-a20d8259cd22", type: "air", latitude: "35.825600", longitude: "10.640600", status: "actif", installationDate: "2025-01-10", ownerId: allOwners[1]?.id || 1 },
      { uuid: "6c51665c-e399-45de-9c04-ef3286324fe5", type: "air", latitude: "35.825600", longitude: "10.640600", status: "actif", installationDate: "2025-11-27", ownerId: allOwners[0]?.id || 1 },
      { uuid: "52b9323f-edf0-4129-b9f1-755cacc73845", type: "trafic", latitude: "35.840000", longitude: "10.620000", status: "maintenance", installationDate: "2025-02-01", ownerId: allOwners[2]?.id || 1 },
      { uuid: "65b693cd-6200-4d0f-87de-cc2d66d251d5", type: "air", latitude: "35.825600", longitude: "10.640600", status: "actif", installationDate: "2025-11-27", ownerId: allOwners[0]?.id || 1 },
    ];

    for (const sensorData of sensorsData) {
      try {
        await db.insert(sensors).values(sensorData);
      } catch (err: any) {
        if (err && err.code === 'ER_DUP_ENTRY') {
          // already exists, ignore
        } else if (err) {
          console.error(`Error inserting sensor ${sensorData.uuid}:`, err.message);
        }
      }
    }

    const sensorsList = await db.select().from(sensors);

    // Create sensor measurements from SQL data
    console.log("Creating sensor measurements...");
    
    // Sample measurements data extracted from SQL (showing the pattern)
    const measurementsData = [
      // Sensor 092c6c1f (Air - Centre)
      { sensorId: "092c6c1f-3f83-4081-9bdd-9a3ca01aea7f", ts: new Date("2025-11-28 17:13:18"), metric: "PM2.5", value: 29.1614, unit: "µg/m3", zone: "Centre" },
      { sensorId: "092c6c1f-3f83-4081-9bdd-9a3ca01aea7f", ts: new Date("2025-11-28 17:13:18"), metric: "PM10", value: 54.5160, unit: "µg/m3", zone: "Centre" },
      { sensorId: "092c6c1f-3f83-4081-9bdd-9a3ca01aea7f", ts: new Date("2025-11-28 17:13:18"), metric: "NO2", value: 16.6199, unit: "µg/m3", zone: "Centre" },
      // Sensor 1a88684b (Lighting - Nord)
      { sensorId: "1a88684b-77b4-48e9-b665-f7aa231de1d7", ts: new Date("2025-11-28 17:13:18"), metric: "voltage", value: 231.6645, unit: "V", zone: "Nord" },
      { sensorId: "1a88684b-77b4-48e9-b665-f7aa231de1d7", ts: new Date("2025-11-28 17:13:18"), metric: "power", value: 45.9557, unit: "W", zone: "Nord" },
      // Sensor 3ebde8b6 (Waste - Centre)
      { sensorId: "3ebde8b6-56e5-487b-b335-010ff94f67e4", ts: new Date("2025-11-28 17:13:18"), metric: "fill_level", value: 15.6749, unit: "%", zone: "Centre" },
      // Sensor 4125fb07 (Air - Centre)
      { sensorId: "4125fb07-d0c7-4fe5-879b-edc78c9706d7", ts: new Date("2025-11-28 17:13:18"), metric: "PM2.5", value: 37.8231, unit: "µg/m3", zone: "Centre" },
      // Sensor 440de941 (Energy - Nord)
      { sensorId: "440de941-d50c-4fa3-a636-a1082ccf8c61", ts: new Date("2025-11-28 17:13:18"), metric: "voltage", value: 227.1384, unit: "V", zone: "Nord" },
      { sensorId: "440de941-d50c-4fa3-a636-a1082ccf8c61", ts: new Date("2025-11-28 17:13:18"), metric: "power", value: 3.3713, unit: "kW", zone: "Nord" },
      // Sensor 52b9323f (Traffic - Nord)
      { sensorId: "52b9323f-edf0-4129-b9f1-755cacc73845", ts: new Date("2025-11-28 17:13:18"), metric: "vehicle_count", value: 162, unit: "vehicles", zone: "Nord" },
      { sensorId: "52b9323f-edf0-4129-b9f1-755cacc73845", ts: new Date("2025-11-28 17:13:18"), metric: "avg_speed", value: 62.2673, unit: "km/h", zone: "Nord" },
      // Sensor 65b693cd (Air - Centre)
      { sensorId: "65b693cd-6200-4d0f-87de-cc2d66d251d5", ts: new Date("2025-11-28 17:13:18"), metric: "PM2.5", value: 23.2899, unit: "µg/m3", zone: "Centre" },
      { sensorId: "65b693cd-6200-4d0f-87de-cc2d66d251d5", ts: new Date("2025-11-28 17:13:18"), metric: "PM10", value: 94.8752, unit: "µg/m3", zone: "Centre" },
    ];

    // Insert measurements
    for (const measurement of measurementsData) {
      try {
        await db.insert(sensorMeasures).values(measurement);
      } catch (err: any) {
        if (err && err.code !== 'ER_DUP_ENTRY') {
          console.error(`Error inserting measurement:`, err.message);
        }
      }
    }

    // Create technicians
    console.log("Creating technicians...");
    const techniciansData = [
      { name: "Amine Bennaceur", phone: "+216 21 333 444", email: "amine@tech.tn", status: "actif" },
      { name: "Sarra Khelifi", phone: "+216 22 555 666", email: "sarra@tech.tn", status: "actif" },
      { name: "Mohamed Trabelsi", phone: "+216 23 777 888", email: "mohamed@tech.tn", status: "actif" },
      { name: "Leila Mansour", phone: "+216 24 999 000", email: "leila@tech.tn", status: "inactif" },
    ];
    for (const tech of techniciansData) {
      try {
        await db.insert(technicians).values(tech);
      } catch (err: any) {
        if (err && err.code === 'ER_DUP_ENTRY') {
          // already exists, ignore
        } else {
          throw err;
        }
      }
    }
    const techniciansList = await db.select().from(technicians);

    // Create interventions from SQL data
    console.log("Creating interventions...");
    const interventionsData = [
      { sensorId: "65b693cd-6200-4d0f-87de-cc2d66d251d5", dateTime: new Date("2025-11-27 19:54:21"), type: "predictive", durationMinutes: 45, cost: "150.00", impactCo2: "3.5000" },
      { sensorId: "ffa098af-d029-4667-b612-0b656e4937e2", dateTime: new Date("2025-11-28 14:30:00"), type: "predictive", durationMinutes: 35, cost: "120.00", impactCo2: "2.8000" },
      { sensorId: "ffa098af-d029-4667-b612-0b656e4937e2", dateTime: new Date("2025-11-27 19:09:00"), type: "predictive", durationMinutes: 29, cost: "100.00", impactCo2: "2.6000" },
      { sensorId: "6c51665c-e399-45de-9c04-ef3286324fe5", dateTime: new Date("2025-11-27 19:17:00"), type: "predictive", durationMinutes: 30, cost: "100.00", impactCo2: "2.5000" },
      { sensorId: "6b1e756e-4ed4-453c-9ed6-46faee2af2d1", dateTime: new Date("2025-11-28 11:45:00"), type: "predictive", durationMinutes: 40, cost: "130.00", impactCo2: "3.0000" },
      { sensorId: "714cb584-44ac-4298-8dba-1bca30a581e4", dateTime: new Date("2025-11-27 19:17:00"), type: "predictive", durationMinutes: 30, cost: "100.00", impactCo2: "2.5000" },
      { sensorId: "4125fb07-d0c7-4fe5-879b-edc78c9706d7", dateTime: new Date("2025-11-28 16:20:00"), type: "predictive", durationMinutes: 25, cost: "90.00", impactCo2: "2.2000" },
      { sensorId: "52b9323f-edf0-4129-b9f1-755cacc73845", dateTime: new Date("2025-11-28 10:30:00"), type: "predictive", durationMinutes: 50, cost: "160.00", impactCo2: "4.0000" },
    ];
    
    for (const data of interventionsData) {
      try {
        await db.insert(interventions).values(data);
      } catch (err: any) {
        if (err && err.code === 'ER_DUP_ENTRY') {
          // already exists, ignore
        } else {
          throw err;
        }
      }
    }
    const interventionsList = await db.select().from(interventions);

    // Assign technicians to interventions (min 2, exactly 1 validator)
    console.log("Assigning technicians to interventions...");
    const interventionTechData = [
      {
        interventionId: interventionsList[0].id,
        technicianId: techniciansList[0].id,
        role: "intervenant",
      },
      {
        interventionId: interventionsList[0].id,
        technicianId: techniciansList[1].id,
        role: "valideur",
      },
      {
        interventionId: interventionsList[1].id,
        technicianId: techniciansList[1].id,
        role: "intervenant",
      },
      {
        interventionId: interventionsList[1].id,
        technicianId: techniciansList[2].id,
        role: "valideur",
      },
      {
        interventionId: interventionsList[2].id,
        technicianId: techniciansList[0].id,
        role: "valideur",
      },
      {
        interventionId: interventionsList[2].id,
        technicianId: techniciansList[2].id,
        role: "intervenant",
      },
      {
        interventionId: interventionsList[3].id,
        technicianId: techniciansList[1].id,
        role: "intervenant",
      },
      {
        interventionId: interventionsList[3].id,
        technicianId: techniciansList[3].id,
        role: "valideur",
      },
      {
        interventionId: interventionsList[4].id,
        technicianId: techniciansList[0].id,
        role: "intervenant",
      },
      {
        interventionId: interventionsList[4].id,
        technicianId: techniciansList[1].id,
        role: "valideur",
      },
      {
        interventionId: interventionsList[5].id,
        technicianId: techniciansList[2].id,
        role: "intervenant",
      },
      {
        interventionId: interventionsList[5].id,
        technicianId: techniciansList[0].id,
        role: "valideur",
      },
      {
        interventionId: interventionsList[6].id,
        technicianId: techniciansList[3].id,
        role: "intervenant",
      },
      {
        interventionId: interventionsList[6].id,
        technicianId: techniciansList[1].id,
        role: "valideur",
      },
      {
        interventionId: interventionsList[7].id,
        technicianId: techniciansList[2].id,
        role: "intervenant",
      },
      {
        interventionId: interventionsList[7].id,
        technicianId: techniciansList[3].id,
        role: "valideur",
      },
    ];
    for (const data of interventionTechData) {
      try {
        await db.insert(interventionTechnicians).values(data);
      } catch (err: any) {
        if (err && err.code === 'ER_DUP_ENTRY') {
          // already exists, ignore
        } else {
          throw err;
        }
      }
    }

    // Create citizens from SQL data
    console.log("Creating citizens...");
    const citizensData = [
      { name: "firas mrabet mrabet", address: "sousse", phone: "+21626521249", email: "firassmrabett111@gmail.com", engagementScore: 90, mobilityPrefs: ["marche"] },
      { name: "mrabet", address: "monastir", phone: "+21626521249", email: "firas.mrabet@eniso.u-sousse.tn", engagementScore: 99, mobilityPrefs: ["velo"] },
      { name: "Hichem Zarrouk", address: "Sahloul, Sousse", phone: "+216 29 111 222", email: "hichem@neo.tn", engagementScore: 82, mobilityPrefs: ["bike", "bus"] },
      { name: "Noura Mansouri", address: "Akouda, Sousse", phone: "+216 23 444 555", email: "noura@neo.tn", engagementScore: 68, mobilityPrefs: ["car", "tram"] },
      { name: "Karim Bouazizi", address: "Centre Ville, Sousse", phone: "+216 25 666 777", email: "karim@neo.tn", engagementScore: 91, mobilityPrefs: ["bike", "tram"] },
    ];
    for (const data of citizensData) {
      try {
        await db.insert(citizens).values(data);
      } catch (err: any) {
        if (err && err.code === 'ER_DUP_ENTRY') {
          // already exists, ignore
        } else {
          throw err;
        }
      }
    }
    const citizensList = await db.select().from(citizens);

    // Create consultations from SQL data
    console.log("Creating consultations...");
    const consultationsData = [
      { citizenId: 17, date: "2025-11-27", topic: "hh", participationMode: "en_ligne" },
      { citizenId: 18, date: "2025-11-28", topic: "*", participationMode: "presentiel" },
    ];
    for (const data of consultationsData) {
      try {
        await db.insert(consultations).values(data);
      } catch (err: any) {
        if (err && err.code === 'ER_DUP_ENTRY') {
          // already exists, ignore
        } else {
          throw err;
        }
      }
    }

    // Create vehicles from SQL data
    console.log("Creating vehicles...");
    const vehiclesData: any[] = [];
    for (const data of vehiclesData) {
      try {
        await db.insert(vehicles).values(data);
      } catch (err: any) {
        if (err && err.code === 'ER_DUP_ENTRY') {
          // already exists, ignore
        } else {
          throw err;
        }
      }
    }
    const vehiclesList = await db.select().from(vehicles);

    // Create trips from SQL data
    console.log("Creating trips...");
    const tripsData = [
      { vehicleId: "TN-1234-NEO", origin: "Centre", destination: "Sahloul", startTime: new Date(Date.now() - 6 * 60 * 60 * 1000), durationMinutes: 20, co2Saving: "1.80" },
      { vehicleId: "TN-5678-NEO", origin: "Dépot", destination: "Zone Nord", startTime: new Date(Date.now() - 5 * 60 * 60 * 1000), durationMinutes: 35, co2Saving: "3.20" },
      { vehicleId: "TN-9012-NEO", origin: "Centre", destination: "Akouda", startTime: new Date(Date.now() - 4 * 60 * 60 * 1000), durationMinutes: 45, co2Saving: "5.60" },
      { vehicleId: "TN-1234-NEO", origin: "Sahloul", destination: "Centre", startTime: new Date(Date.now() - 3 * 60 * 60 * 1000), durationMinutes: 18, co2Saving: "1.50" },
      { vehicleId: "TN-3456-NEO", origin: "Centre", destination: "Khezama", startTime: new Date(Date.now() - 2 * 60 * 60 * 1000), durationMinutes: 40, co2Saving: "4.20" },
      { vehicleId: "TN-9012-NEO", origin: "Akouda", destination: "Msaken", startTime: new Date(Date.now() - 1 * 60 * 60 * 1000), durationMinutes: 30, co2Saving: "3.80" },
    ];
    for (const data of tripsData) {
      try {
        await db.insert(trips).values(data);
      } catch (err: any) {
        if (err && err.code === 'ER_DUP_ENTRY') {
          // already exists, ignore
        } else {
          throw err;
        }
      }
    }

    // Count measurements inserted (approx)
    const measurementsList = await db.select().from(sensorMeasures);
    const measurementsCount = measurementsList.length;

    console.log("✅ Database seeded successfully!");
    console.log(`Created:
  - ${2} owners
  - ${sensorsList.length} sensors
  - ${measurementsCount} sensor measurements
  - ${techniciansList.length} technicians
  - ${interventionsList.length} interventions
  - ${citizensList.length} citizens
  - ${5} consultations
  - ${vehiclesList.length} vehicles
  - ${6} trips
    `);
  } catch (error) {
    console.error("Error seeding database:", error);
    throw error;
  }
}

seed()
  .then(() => {
    console.log("Seed completed");
    process.exit(0);
  })
  .catch((error) => {
    console.error("Seed failed:", error);
    process.exit(1);
  });
