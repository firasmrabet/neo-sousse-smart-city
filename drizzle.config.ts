import { defineConfig } from "drizzle-kit";

if (!process.env.MYSQL_DATABASE && !process.env.DATABASE_URL) {
  throw new Error("No database configuration found. Set MYSQL_DATABASE or DATABASE_URL");
}

export default defineConfig({
  out: "./migrations",
  schema: "./shared/schema.ts",
  dialect: "mysql",
  dbCredentials: {
    host: process.env.MYSQL_HOST || "127.0.0.1",
    port: parseInt(process.env.MYSQL_PORT || "3306", 10),
    user: process.env.MYSQL_USER || "root",
    password: process.env.MYSQL_PASSWORD || "",
    database: process.env.MYSQL_DATABASE || "sousse_smart_city_projet_module",
  },
});
