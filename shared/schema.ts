import { sql, relations } from "drizzle-orm";
import { mysqlTable, text, varchar, int, decimal, timestamp, date, json, primaryKey, mysqlEnum } from "drizzle-orm/mysql-core";
import { createInsertSchema } from "drizzle-zod";
import { z } from "zod";

// Owners -> Propriétaire
export const owners = mysqlTable("Propriétaire", {
  id: int("IDP").primaryKey().autoincrement(),
  name: varchar("Nom", { length: 100 }),
  address: varchar("Adresse", { length: 200 }),
  phone: varchar("Téléphone", { length: 30 }),
  email: varchar("Email", { length: 100 }),
  ownerType: mysqlEnum("Propriété", ["Municipalité", "Privé"]),
});

// Sensors -> Capteur
export const sensors = mysqlTable("Capteur", {
  uuid: varchar("UUID", { length: 36 }).primaryKey().notNull(),
  type: mysqlEnum("Type", ["Éclairage", "Déchets", "Trafic", "Énergie", "Qualité de l'air"]),
  latitude: decimal("Latitude", { precision: 9, scale: 6 }),
  longitude: decimal("Longitude", { precision: 9, scale: 6 }),
  status: mysqlEnum("Statut", ["Actif", "En Maintenance", "Hors Service", "Signalé"]),
  installationDate: date("Date Installation"),
  ownerId: int("IDP").references(() => owners.id),
});


export const capteurs = sensors;

// Sensor Measurements -> Mesures1
export const sensorMeasures = mysqlTable("Mesures1", {
  id: int("IDM").primaryKey().autoincrement(),
  sensorId: varchar("UUID", { length: 36 }).references(() => sensors.uuid),
  grandeur: varchar("NomGrandeur", { length: 100 }),
  value: decimal("Valeur", { precision: 20, scale: 6 }),
});

// Technicians -> Technicien
export const technicians = mysqlTable("Technicien", {
  id: int("IDT").primaryKey().autoincrement(),
  name: varchar("Nom", { length: 255 }),
  numero: varchar("Numero", { length: 20 }).notNull().default(""),
});

// Interventions -> Intervention
export const interventions = mysqlTable("Intervention", {
  id: int("IDIn").primaryKey().autoincrement(),
  sensorId: varchar("UUID", { length: 36 }).references(() => sensors.uuid),
  dateTime: timestamp("DateHeure"),
  type: mysqlEnum("Nature", ["Prédictive", "Corrective", "Curative"]),
  durationMinutes: int("Durée"),
  cost: decimal("Coût", { precision: 12, scale: 2 }),
  impactCo2: decimal("ImpactCO2", { precision: 12, scale: 3 }),
  status: mysqlEnum("statut", ["Demande", "Tech1_Assigné", "Tech2_Valide", "IA_Valide", "Terminée"]),
  technician1Id: int("technicien_1_id"),
  technician2Id: int("technicien_2_id"),
  reportTech1: text("rapport_tech1"),
  reportTech2: text("rapport_tech2"),
});

// Intervention Technicians -> Supervision
export const interventionTechnicians = mysqlTable("Supervision", {
  interventionId: int("IDIn").notNull().references(() => interventions.id),
  technicianId: int("IDT").notNull().references(() => technicians.id),
  role: mysqlEnum("Rôle", ["Intervenant", "Valideur"]),
}, (table) => ({
  pk: primaryKey({ columns: [table.interventionId, table.technicianId] }),
}));

// Citizens -> Citoyen
export const citizens = mysqlTable("Citoyen", {
  id: int("IDCI").primaryKey().autoincrement(),
  name: varchar("Nom", { length: 255 }),
  address: text("Adresse"),
  phone: varchar("Téléphone", { length: 50 }),
  email: varchar("Email", { length: 255 }),
  engagementScore: int("Score"),
  mobilityPrefs: text("Préférences"),
});

// Consultations -> Consultation
export const consultations = mysqlTable("Consultation", {
  id: int("IDCO").primaryKey().autoincrement(),
  citizenId: int("IDCI").notNull().references(() => citizens.id), 
  topic: varchar("Sujet", { length: 100 }),
  mode: varchar("Mode", { length: 50 }),
});

// Participations -> Participation
export const participations = mysqlTable("Participation", {
  id: int("IDPA").primaryKey().autoincrement(),
  citizenId: int("IDCI").notNull().references(() => citizens.id),
  consultationId: int("IDCO").notNull().references(() => consultations.id),
  date: date("Date"),
  heure: varchar("Heure", { length: 10 }),
});

// Vehicles -> Véhicule
export const vehicles = mysqlTable("véhicule", {
  plate: varchar("Plaque", { length: 20 }).primaryKey(),
  vehicleType: varchar("Type", { length: 100 }),
  energy: mysqlEnum("Énergie Utilisée", ["Électrique", "Hybride", "Hydrogène"]),
  status: mysqlEnum("Statut", ["Stationné", "En Route", "Arrivé", "En Panne"]),
  latitude: decimal("Latitude", { precision: 9, scale: 6 }),
  longitude: decimal("Longitude", { precision: 9, scale: 6 }),
});

// Trips -> Trajet
export const trips = mysqlTable("Trajet", {
  id: int("IDTR").primaryKey().autoincrement(),
  vehicleId: varchar("Plaque", { length: 20 }).references(() => vehicles.plate),
  origin: varchar("Origine", { length: 255 }),
  destination: varchar("Destination", { length: 255 }),
  startTime: timestamp("Date"),
  durationMinutes: int("Durée"),
  co2Saving: decimal("ÉconomieCO2", { precision: 12, scale: 3 }),
});



export const ownersRelations = relations(owners, ({ many }) => ({
  sensors: many(sensors),
}));

export const sensorsRelations = relations(sensors, ({ one, many }) => ({
  owner: one(owners, {
    fields: [sensors.ownerId],
    references: [owners.id],
  }),
  measurements: many(sensorMeasures),
  interventions: many(interventions),
}));

export const sensorMeasuresRelations = relations(sensorMeasures, ({ one }) => ({
  sensor: one(sensors, {
    fields: [sensorMeasures.sensorId],
    references: [sensors.uuid],
  }),
}));

export const techniciansRelations = relations(technicians, ({ many }) => ({
  interventionTechnicians: many(interventionTechnicians),
}));

export const interventionsRelations = relations(interventions, ({ one, many }) => ({
  sensor: one(sensors, {
    fields: [interventions.sensorId],
    references: [sensors.uuid],
  }),
  interventionTechnicians: many(interventionTechnicians),
}));

export const interventionTechniciansRelations = relations(interventionTechnicians, ({ one }) => ({
  intervention: one(interventions, {
    fields: [interventionTechnicians.interventionId],
    references: [interventions.id],
  }),
  technician: one(technicians, {
    fields: [interventionTechnicians.technicianId],
    references: [technicians.id],
  }),
}));

export const citizensRelations = relations(citizens, ({ many }) => ({
  consultations: many(consultations),
  participations: many(participations),
}));

export const consultationsRelations = relations(consultations, ({ one, many }) => ({
  citizen: one(citizens, {
    fields: [consultations.citizenId],
    references: [citizens.id],
  }),
  participations: many(participations),
}));

export const participationsRelations = relations(participations, ({ one }) => ({
  citizen: one(citizens, {
    fields: [participations.citizenId],
    references: [citizens.id],
  }),
  consultation: one(consultations, {
    fields: [participations.consultationId],
    references: [consultations.id],
  }),
}));;
export const insertSensorMeasureSchema = createInsertSchema(sensorMeasures).omit({ id: true });
export const insertOwnerSchema = createInsertSchema(owners).omit({ id: true });

// Custom sensor schema - completely manual to avoid Drizzle decimal type issues
export const insertSensorSchema = z.object({
  type: z.string().refine(val => ["Éclairage", "Déchets", "Trafic", "Énergie", "Qualité de l'air"].includes(val), {
    message: "Invalid sensor type"
  }).optional(),
  latitude: z.any().transform(val => {
    if (val === null || val === undefined || val === '') return undefined;
    const num = parseFloat(String(val));
    return isNaN(num) ? undefined : num;
  }).optional(),
  longitude: z.any().transform(val => {
    if (val === null || val === undefined || val === '') return undefined;
    const num = parseFloat(String(val));
    return isNaN(num) ? undefined : num;
  }).optional(),
  status: z.string().refine(val => ["Actif", "En Maintenance", "Hors Service", "Signalé"].includes(val), {
    message: "Invalid sensor status"
  }).optional(),
  installationDate: z.any().transform(val => {
    if (val === null || val === undefined || val === '') return undefined;
    if (val instanceof Date) return val;
    const date = new Date(String(val));
    return isNaN(date.getTime()) ? undefined : date;
  }).optional(),
  ownerId: z.any().transform(val => {
    if (val === null || val === undefined || val === '') return undefined;
    const num = parseInt(String(val), 10);
    return isNaN(num) ? undefined : num;
  }).optional(),
});
export const insertTechnicianSchema = createInsertSchema(technicians).omit({ id: true });
export const insertInterventionSchema = createInsertSchema(interventions)
  .omit({ id: true })
  .extend({
    dateTime: z.union([z.date(), z.string()]).pipe(z.coerce.date()),
  });
export const insertInterventionTechnicianSchema = createInsertSchema(interventionTechnicians);
export const insertCitizenSchema = createInsertSchema(citizens).omit({ id: true });
export const insertConsultationSchema = createInsertSchema(consultations)
  .omit({ id: true })
  .extend({
    date: z.union([z.date(), z.string()]).pipe(z.coerce.date()),
  });
export const insertParticipationSchema = createInsertSchema(participations);
export const insertVehicleSchema = createInsertSchema(vehicles);
export const insertTripSchema = createInsertSchema(trips)
  .omit({ id: true })
  .extend({
    startTime: z.union([z.date(), z.string()]).pipe(z.coerce.date()),
  });

// Types
export type Owner = typeof owners.$inferSelect;
export type InsertOwner = z.infer<typeof insertOwnerSchema>;
export type Sensor = typeof sensors.$inferSelect;
export type InsertSensor = z.infer<typeof insertSensorSchema>;
export type SensorMeasure = typeof sensorMeasures.$inferSelect;
export type InsertSensorMeasure = z.infer<typeof insertSensorMeasureSchema>;
export type Technician = typeof technicians.$inferSelect;
export type InsertTechnician = z.infer<typeof insertTechnicianSchema>;
export type Intervention = typeof interventions.$inferSelect;
export type InsertIntervention = z.infer<typeof insertInterventionSchema>;
export type InterventionTechnician = typeof interventionTechnicians.$inferSelect;
export type InsertInterventionTechnician = z.infer<typeof insertInterventionTechnicianSchema>;
export type Citizen = typeof citizens.$inferSelect;
export type InsertCitizen = z.infer<typeof insertCitizenSchema>;
export type Consultation = typeof consultations.$inferSelect;
export type InsertConsultation = z.infer<typeof insertConsultationSchema>;
export type Participation = typeof participations.$inferSelect;
export type InsertParticipation = z.infer<typeof insertParticipationSchema>;
export type Vehicle = typeof vehicles.$inferSelect;
export type InsertVehicle = z.infer<typeof insertVehicleSchema>;
export type Trip = typeof trips.$inferSelect;
export type InsertTrip = z.infer<typeof insertTripSchema>;
