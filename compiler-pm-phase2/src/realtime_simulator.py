"""
Real-Time IoT Simulator — Neo-Sousse Smart City
Generates sensor measurements and vehicle GPS data every 2 seconds.
Runs as a daemon background thread with its OWN dedicated DB connection.
"""

import threading
import time
import math
import random
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════
# SENSOR MEASUREMENT PROFILES per Type
# ═══════════════════════════════════════════════════════════════
SENSOR_PROFILES = {
    "Éclairage": [
        {"grandeur": "Luminosité", "unit": "lux", "base": 450, "amp": 120, "noise": 15},
        {"grandeur": "Consommation", "unit": "W", "base": 85, "amp": 20, "noise": 5},
    ],
    "Déchets": [
        {"grandeur": "Niveau Remplissage", "unit": "%", "base": 50, "amp": 25, "noise": 3},
        {"grandeur": "Poids Estimé", "unit": "kg", "base": 190, "amp": 40, "noise": 8},
    ],
    "Trafic": [
        {"grandeur": "Densité Trafic", "unit": "veh/h", "base": 55, "amp": 25, "noise": 8},
        {"grandeur": "Vitesse Moyenne", "unit": "km/h", "base": 35, "amp": 12, "noise": 5},
        {"grandeur": "Congestion", "unit": "%", "base": 42, "amp": 20, "noise": 6},
    ],
    "Énergie": [
        {"grandeur": "Consommation Énergie", "unit": "kWh", "base": 125, "amp": 30, "noise": 8},
        {"grandeur": "Tension", "unit": "V", "base": 230, "amp": 2, "noise": 0.5},
        {"grandeur": "Courant", "unit": "A", "base": 19, "amp": 4, "noise": 1},
    ],
    "Qualité de l'air": [
        {"grandeur": "PM2.5", "unit": "µg/m³", "base": 45, "amp": 12, "noise": 4},
        {"grandeur": "CO2", "unit": "ppm", "base": 420, "amp": 20, "noise": 5},
        {"grandeur": "Température", "unit": "°C", "base": 23.5, "amp": 2, "noise": 0.3},
    ],
}

# ═══════════════════════════════════════════════════════════════
# SOUSSE CITY ROUTES for vehicle simulation
# ═══════════════════════════════════════════════════════════════
SOUSSE_ROUTES = [
    # Route 1: Centre-ville → Port
    [(35.8256, 10.6369), (35.8270, 10.6380), (35.8285, 10.6395), (35.8300, 10.6410),
     (35.8315, 10.6425), (35.8330, 10.6440), (35.8345, 10.6455), (35.8360, 10.6470)],
    # Route 2: Médina → Zone industrielle
    [(35.8240, 10.6350), (35.8225, 10.6335), (35.8210, 10.6320), (35.8195, 10.6305),
     (35.8180, 10.6290), (35.8165, 10.6275), (35.8150, 10.6260), (35.8135, 10.6245)],
    # Route 3: Khezama → Sahloul
    [(35.8300, 10.5900), (35.8320, 10.5920), (35.8340, 10.5940), (35.8360, 10.5960),
     (35.8380, 10.5980), (35.8400, 10.6000), (35.8420, 10.6020), (35.8440, 10.6040)],
    # Route 4: Hammam Sousse → Akouda
    [(35.8600, 10.6100), (35.8620, 10.6120), (35.8640, 10.6140), (35.8660, 10.6160),
     (35.8680, 10.6180), (35.8700, 10.6200), (35.8720, 10.6220), (35.8740, 10.6240)],
    # Route 5: Sousse Nord circulaire
    [(35.8400, 10.6300), (35.8410, 10.6320), (35.8415, 10.6350), (35.8410, 10.6380),
     (35.8400, 10.6400), (35.8385, 10.6410), (35.8370, 10.6400), (35.8360, 10.6380)],
]


def _generate_sensor_value(profile: dict, t: float, is_active: bool) -> float:
    """Generate a realistic sensor value based on a sinusoidal + noise model."""
    if not is_active:
        return 0.0
    base = profile["base"]
    amp = profile["amp"]
    noise = profile["noise"]
    val = base + amp * math.sin(t * 0.15) + random.gauss(0, noise)
    return round(max(0, val), 2)


class RealtimeSimulator:
    """Background thread simulator with its OWN dedicated DB connection."""

    def __init__(self, db_getter):
        self._db_getter = db_getter
        self._running = False
        self._thread = None
        self._tick = 0
        self._vehicle_positions = {}
        # Dedicated connection for the simulator thread (NOT the shared singleton)
        self._sim_conn = None
        self._sim_cursor = None

    # ── Thread-safe dedicated DB connection ──────────────────
    def _ensure_connection(self):
        """Create or reconnect the simulator's own DB connection."""
        import mysql.connector
        try:
            if self._sim_conn and self._sim_conn.is_connected():
                return True
        except Exception:
            self._sim_conn = None
            self._sim_cursor = None

        try:
            self._sim_conn = mysql.connector.connect(
                host="127.0.0.1", port=3306, user="root", password="",
                database="sousse_smart_city_projet_module",
                charset='utf8mb4', use_pure=True, autocommit=True,
                connection_timeout=5
            )
            self._sim_cursor = self._sim_conn.cursor(dictionary=True, buffered=True)
            logger.info("✅ Simulator dedicated DB connection established")
            return True
        except Exception as e:
            logger.debug(f"Simulator DB connect error: {e}")
            return False

    def _sim_execute(self, query, params=None):
        """Execute a write query on the simulator's dedicated connection."""
        if not self._ensure_connection():
            return False
        try:
            self._sim_cursor.execute(query, params or ())
            self._sim_conn.commit()
            return True
        except Exception as e:
            logger.debug(f"Sim execute error: {e}")
            try: self._sim_conn.close()
            except Exception: pass
            self._sim_conn = None
            self._sim_cursor = None
            return False

    def _sim_fetch_all(self, query, params=None):
        """Fetch all rows on the simulator's dedicated connection."""
        if not self._ensure_connection():
            return []
        try:
            self._sim_cursor.execute(query, params or ())
            return self._sim_cursor.fetchall()
        except Exception as e:
            logger.debug(f"Sim fetch error: {e}")
            try: self._sim_conn.close()
            except Exception: pass
            self._sim_conn = None
            self._sim_cursor = None
            return []

    # ── Table initialization ─────────────────────────────────
    def _init_tables(self):
        """Create real-time data tables if they don't exist."""
        self._sim_execute("""
            CREATE TABLE IF NOT EXISTS sensor_realtime (
                id INT AUTO_INCREMENT PRIMARY KEY,
                uuid CHAR(36) NOT NULL,
                grandeur VARCHAR(100) NOT NULL,
                valeur DECIMAL(20,6) DEFAULT 0,
                unit VARCHAR(20) DEFAULT '',
                ts DATETIME DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_uuid_ts (uuid, ts),
                INDEX idx_ts (ts)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        self._sim_execute("""
            CREATE TABLE IF NOT EXISTS vehicle_realtime_gps (
                id INT AUTO_INCREMENT PRIMARY KEY,
                plaque VARCHAR(20) NOT NULL,
                latitude DECIMAL(9,6) NOT NULL,
                longitude DECIMAL(9,6) NOT NULL,
                ts DATETIME DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_plaque_ts (plaque, ts),
                INDEX idx_ts (ts)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)

    # ── Sensor data generation ───────────────────────────────
    def _generate_sensor_data(self):
        """Generate one tick of sensor measurements for all sensors."""
        sensors = self._sim_fetch_all("SELECT UUID, Type, Statut FROM capteur")
        if not sensors:
            return

        now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        t = self._tick

        for sensor in sensors:
            uuid = sensor.get('UUID', '')
            s_type = sensor.get('Type', '')
            statut = sensor.get('Statut', '')
            is_active = statut == 'Actif'

            profiles = SENSOR_PROFILES.get(s_type, [])
            if not profiles:
                continue

            profile = profiles[0]
            val = _generate_sensor_value(profile, t + hash(uuid) % 100, is_active)

            self._sim_execute(
                "INSERT INTO sensor_realtime (uuid, grandeur, valeur, unit, ts) "
                "VALUES (%s, %s, %s, %s, %s)",
                (uuid, profile["grandeur"], val, profile.get("unit", ""), now_str)
            )

    # ── Vehicle GPS generation ───────────────────────────────
    def _generate_vehicle_data(self):
        """Generate one tick of GPS data for all vehicles."""
        vehicles = self._sim_fetch_all(
            "SELECT Plaque, Statut, Latitude, Longitude FROM `véhicule`"
        )
        if not vehicles:
            return

        now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        for v in vehicles:
            plaque = v.get('Plaque', '')
            statut = v.get('Statut', '')
            cur_lat = float(v.get('Latitude') or 35.8256)
            cur_lon = float(v.get('Longitude') or 10.6369)

            if statut == 'En Route':
                if plaque not in self._vehicle_positions:
                    route_idx = hash(plaque) % len(SOUSSE_ROUTES)
                    self._vehicle_positions[plaque] = {
                        "route": route_idx, "step": 0, "direction": 1
                    }

                pos = self._vehicle_positions[plaque]
                route = SOUSSE_ROUTES[pos["route"]]
                step = pos["step"]

                target_lat, target_lon = route[step]
                lat = target_lat + random.gauss(0, 0.0003)
                lon = target_lon + random.gauss(0, 0.0003)

                pos["step"] += pos["direction"]
                if pos["step"] >= len(route):
                    pos["step"] = len(route) - 2
                    pos["direction"] = -1
                elif pos["step"] < 0:
                    pos["step"] = 1
                    pos["direction"] = 1

                self._sim_execute(
                    "UPDATE `véhicule` SET Latitude=%s, Longitude=%s WHERE Plaque=%s",
                    (round(lat, 6), round(lon, 6), plaque)
                )
            else:
                lat = cur_lat if cur_lat != 0 else 35.8256 + random.uniform(-0.01, 0.01)
                lon = cur_lon if cur_lon != 0 else 10.6369 + random.uniform(-0.01, 0.01)

                if cur_lat == 0 or v.get('Latitude') is None:
                    self._sim_execute(
                        "UPDATE `véhicule` SET Latitude=%s, Longitude=%s WHERE Plaque=%s",
                        (round(lat, 6), round(lon, 6), plaque)
                    )
                self._vehicle_positions.pop(plaque, None)

            self._sim_execute(
                "INSERT INTO vehicle_realtime_gps (plaque, latitude, longitude, ts) "
                "VALUES (%s, %s, %s, %s)",
                (plaque, round(lat, 6), round(lon, 6), now_str)
            )

    # ── Cleanup old data ─────────────────────────────────────
    def _cleanup_old_data(self):
        """Remove old real-time data to prevent DB bloat."""
        self._sim_execute(
            "DELETE FROM sensor_realtime WHERE ts < DATE_SUB(NOW(), INTERVAL 10 MINUTE)"
        )
        self._sim_execute(
            "DELETE FROM vehicle_realtime_gps WHERE ts < DATE_SUB(NOW(), INTERVAL 10 MINUTE)"
        )

    # ── Main loop ────────────────────────────────────────────
    def _loop(self):
        """Main simulator loop running every 2 seconds."""
        self._init_tables()
        logger.info("🔄 Real-time simulator started (dedicated connection)")
        cleanup_counter = 0
        while self._running:
            try:
                self._generate_sensor_data()
                self._generate_vehicle_data()
                self._tick += 1
                cleanup_counter += 1
                if cleanup_counter >= 30:
                    self._cleanup_old_data()
                    cleanup_counter = 0
            except Exception as e:
                logger.warning(f"Simulator tick error: {e}")
                # Force reconnect on next tick
                self._sim_conn = None
                self._sim_cursor = None
            time.sleep(2)

    def start(self):
        """Start the simulator in a daemon thread."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True, name="RealtimeSimulator")
        self._thread.start()
        logger.info("✅ Real-time simulator thread started")

    def stop(self):
        """Stop the simulator."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=3)
        if self._sim_conn:
            try: self._sim_conn.close()
            except Exception: pass
        logger.info("⏹ Real-time simulator stopped")

    @property
    def is_running(self):
        return self._running


# ═══════════════════════════════════════════════════════════════
# SINGLETON
# ═══════════════════════════════════════════════════════════════
_instance = None

def get_simulator(db_getter=None):
    """Get or create the singleton simulator."""
    global _instance
    if _instance is None and db_getter:
        _instance = RealtimeSimulator(db_getter)
    return _instance

def start_simulator(db_getter):
    """Start the global simulator."""
    sim = get_simulator(db_getter)
    if sim and not sim.is_running:
        sim.start()
    return sim
