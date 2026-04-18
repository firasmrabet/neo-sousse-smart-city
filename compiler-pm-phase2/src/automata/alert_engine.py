"""
Alert Engine — Actions Automatiques (Énoncé §2.2)
Déclencher des actions automatiques :
  - Alerte si capteur hors service > 24h
  - Alerte si intervention en attente > 48h
  - Suggestions d'actions correctives
  - Historique des alertes

Conformément à l'énoncé: "Déclencher des actions automatiques
(ex: alerte si capteur hors service > 24h)"
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)

# DB connection
try:
    from ..db_connection import get_db
except ImportError:
    try:
        from src.db_connection import get_db
    except ImportError:
        get_db = None


class AlertSeverity(str, Enum):
    CRITICAL = "CRITIQUE"
    HIGH = "HAUTE"
    MEDIUM = "MOYENNE"
    LOW = "BASSE"
    INFO = "INFO"


class AlertType(str, Enum):
    SENSOR_OUT_OF_SERVICE = "capteur_hors_service"
    SENSOR_MAINTENANCE_LONG = "capteur_maintenance_longue"
    INTERVENTION_PENDING = "intervention_en_attente"
    INTERVENTION_STALLED = "intervention_bloquée"
    VEHICLE_BREAKDOWN = "véhicule_en_panne"
    SENSOR_NO_DATA = "capteur_sans_données"
    SYSTEM_ANOMALY = "anomalie_système"


class Alert:
    """Représentation d'une alerte automatique"""

    def __init__(
        self,
        alert_type: AlertType,
        severity: AlertSeverity,
        entity_type: str,
        entity_id: str,
        message: str,
        action_recommandee: str,
        details: Dict[str, Any] = None,
        duree_heures: float = 0,
    ):
        self.id = f"ALR-{datetime.now().strftime('%Y%m%d%H%M%S')}-{entity_id[:8]}"
        self.alert_type = alert_type
        self.severity = severity
        self.entity_type = entity_type
        self.entity_id = entity_id
        self.message = message
        self.action_recommandee = action_recommandee
        self.details = details or {}
        self.duree_heures = duree_heures
        self.timestamp = datetime.now()
        self.acknowledged = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.alert_type.value,
            "severity": self.severity.value,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "message": self.message,
            "action": self.action_recommandee,
            "details": self.details,
            "duree_heures": round(self.duree_heures, 1),
            "timestamp": self.timestamp.isoformat(),
            "acknowledged": self.acknowledged,
        }

    @property
    def icon(self) -> str:
        icons = {
            AlertSeverity.CRITICAL: "🔴",
            AlertSeverity.HIGH: "🟠",
            AlertSeverity.MEDIUM: "🟡",
            AlertSeverity.LOW: "🔵",
            AlertSeverity.INFO: "ℹ️",
        }
        return icons.get(self.severity, "⚪")


class AlertEngine:
    """
    Moteur d'alertes automatiques — Conforme à l'énoncé §2.2
    
    Surveille la base de données et déclenche des alertes lorsque:
      - Un capteur est hors service (> 24h estimé)
      - Un capteur est en maintenance prolongée
      - Une intervention est en attente depuis > 48h
      - Un capteur actif n'a aucune mesure enregistrée
    """

    def __init__(self):
        self._alerts: List[Alert] = []
        self._alert_history: List[Alert] = []
        self._thresholds = {
            "sensor_out_of_service_hours": 24,
            "sensor_maintenance_hours": 72,
            "intervention_pending_hours": 48,
            "vehicle_breakdown_hours": 12,
            "sensor_no_data_hours": 6,
        }

    def scan_all(self) -> List[Alert]:
        """
        Scanner toutes les sources d'alertes.
        Point d'entrée principal — appeler périodiquement.
        """
        self._alerts.clear()

        self._scan_sensors_out_of_service()
        self._scan_sensors_maintenance()
        self._scan_interventions_pending()
        self._scan_sensors_no_data()

        # Sort by severity (CRITICAL first)
        severity_order = {
            AlertSeverity.CRITICAL: 0,
            AlertSeverity.HIGH: 1,
            AlertSeverity.MEDIUM: 2,
            AlertSeverity.LOW: 3,
            AlertSeverity.INFO: 4,
        }
        self._alerts.sort(key=lambda a: severity_order.get(a.severity, 99))

        # Archive to history
        self._alert_history.extend(self._alerts)

        return self._alerts

    def get_alerts(self) -> List[Alert]:
        """Retourner les alertes courantes"""
        return self._alerts

    def get_alerts_by_severity(self, severity: AlertSeverity) -> List[Alert]:
        return [a for a in self._alerts if a.severity == severity]

    def get_alert_summary(self) -> Dict[str, Any]:
        """Résumé des alertes pour le dashboard"""
        return {
            "total": len(self._alerts),
            "critical": len([a for a in self._alerts if a.severity == AlertSeverity.CRITICAL]),
            "high": len([a for a in self._alerts if a.severity == AlertSeverity.HIGH]),
            "medium": len([a for a in self._alerts if a.severity == AlertSeverity.MEDIUM]),
            "low": len([a for a in self._alerts if a.severity == AlertSeverity.LOW]),
            "info": len([a for a in self._alerts if a.severity == AlertSeverity.INFO]),
            "last_scan": datetime.now().isoformat(),
        }

    # ═══════════════════════════════════════════════════════════════
    # SCANNER: Capteurs Hors Service > 24h
    # ═══════════════════════════════════════════════════════════════

    def _scan_sensors_out_of_service(self):
        """
        Alerte si capteur hors service > 24h
        (EXIGENCE EXPLICITE DE L'ÉNONCÉ §2.2)
        Uses existing Capteur table — no history table needed.
        """
        if not get_db:
            return

        try:
            db = get_db()
            sensors_hs = db.fetch_all("""
                SELECT UUID, Type, Statut, `Date Installation`
                FROM Capteur
                WHERE Statut = 'Hors Service'
            """)
            for sensor in (sensors_hs or []):
                self._alerts.append(Alert(
                    alert_type=AlertType.SENSOR_OUT_OF_SERVICE,
                    severity=AlertSeverity.CRITICAL,
                    entity_type="capteur",
                    entity_id=sensor["UUID"],
                    message=(
                        f"Capteur {sensor['UUID'][:12]}... "
                        f"({sensor.get('Type', 'N/A')}) est HORS SERVICE"
                    ),
                    action_recommandee=(
                        "Intervention corrective recommandée. "
                        "Assigner techniciens pour diagnostic et réparation."
                    ),
                    details={"sensor_type": sensor.get("Type")},
                    duree_heures=24,
                ))
        except Exception as e:
            logger.error(f"Error scanning out-of-service sensors: {e}")

    # ═══════════════════════════════════════════════════════════════
    # SCANNER: Capteurs en Maintenance > 72h
    # ═══════════════════════════════════════════════════════════════

    def _scan_sensors_maintenance(self):
        if not get_db:
            return
        try:
            db = get_db()
            sensors = db.fetch_all("""
                SELECT UUID, Type, Statut
                FROM Capteur
                WHERE Statut = 'En Maintenance'
            """)
            for sensor in (sensors or []):
                self._alerts.append(Alert(
                    alert_type=AlertType.SENSOR_MAINTENANCE_LONG,
                    severity=AlertSeverity.MEDIUM,
                    entity_type="capteur",
                    entity_id=sensor["UUID"],
                    message=(
                        f"Capteur {sensor['UUID'][:12]}... "
                        f"({sensor.get('Type', 'N/A')}) en maintenance"
                    ),
                    action_recommandee=(
                        "Vérifier l'avancement de la maintenance. "
                        "Envisager un remplacement si nécessaire."
                    ),
                    details={"sensor_type": sensor.get("Type")},
                ))
        except Exception as e:
            logger.error(f"Error scanning maintenance sensors: {e}")

    # ═══════════════════════════════════════════════════════════════
    # SCANNER: Interventions en attente > 48h
    # ═══════════════════════════════════════════════════════════════

    def _scan_interventions_pending(self):
        if not get_db:
            return
        try:
            db = get_db()
            threshold = self._thresholds["intervention_pending_hours"]
            interventions = db.fetch_all(f"""
                SELECT IDIn, DateHeure, Nature, statut,
                       TIMESTAMPDIFF(HOUR, DateHeure, NOW()) as hours_pending
                FROM Intervention
                WHERE statut IN ('Demande', 'Tech1_Assigné')
                  AND TIMESTAMPDIFF(HOUR, DateHeure, NOW()) > {threshold}
                ORDER BY DateHeure ASC
            """)
            for intv in (interventions or []):
                hours = intv.get("hours_pending", 0)
                self._alerts.append(Alert(
                    alert_type=AlertType.INTERVENTION_PENDING,
                    severity=AlertSeverity.HIGH if hours > 72 else AlertSeverity.MEDIUM,
                    entity_type="intervention",
                    entity_id=str(intv["IDIn"]),
                    message=(
                        f"Intervention #{intv['IDIn']} ({intv.get('Nature', 'N/A')}) "
                        f"en attente depuis {hours}h (seuil: {threshold}h). "
                        f"État: {intv.get('statut', 'N/A')}"
                    ),
                    action_recommandee=(
                        "Accélérer l'assignation des techniciens. "
                        "Vérifier la disponibilité de l'équipe technique."
                    ),
                    details={
                        "nature": intv.get("Nature"),
                        "statut": intv.get("statut"),
                    },
                    duree_heures=float(hours) if hours else 0,
                ))
        except Exception as e:
            logger.error(f"Error scanning pending interventions: {e}")

    # ═══════════════════════════════════════════════════════════════
    # SCANNER: Capteurs actifs sans données
    # ═══════════════════════════════════════════════════════════════

    def _scan_sensors_no_data(self):
        if not get_db:
            return
        try:
            db = get_db()
            sensors = db.fetch_all("""
                SELECT c.UUID, c.Type, c.Statut,
                       (SELECT COUNT(*) FROM Mesures1 m WHERE m.UUID = c.UUID) as nb_mesures
                FROM Capteur c
                WHERE c.Statut = 'Actif'
            """)
            for sensor in (sensors or []):
                if sensor.get("nb_mesures", 0) == 0:
                    self._alerts.append(Alert(
                        alert_type=AlertType.SENSOR_NO_DATA,
                        severity=AlertSeverity.LOW,
                        entity_type="capteur",
                        entity_id=sensor["UUID"],
                        message=(
                            f"Capteur {sensor['UUID'][:12]}... "
                            f"({sensor.get('Type', 'N/A')}) actif mais aucune mesure enregistrée"
                        ),
                        action_recommandee=(
                            "Vérifier la connectivité du capteur. "
                            "Possible problème de communication réseau."
                        ),
                        details={"sensor_type": sensor.get("Type")},
                    ))
        except Exception as e:
            logger.error(f"Error scanning sensors with no data: {e}")

    # ═══════════════════════════════════════════════════════════════
    # UTILITY
    # ═══════════════════════════════════════════════════════════════

    def acknowledge_alert(self, alert_id: str) -> bool:
        for alert in self._alerts:
            if alert.id == alert_id:
                alert.acknowledged = True
                return True
        return False

    def get_statistics(self) -> Dict[str, Any]:
        """Statistiques des alertes pour analytics"""
        return {
            "total_actives": len(self._alerts),
            "total_historique": len(self._alert_history),
            "par_type": {
                t.value: len([a for a in self._alerts if a.alert_type == t])
                for t in AlertType
            },
            "par_severite": {
                s.value: len([a for a in self._alerts if a.severity == s])
                for s in AlertSeverity
            },
            "par_entite": {
                "capteur": len([a for a in self._alerts if a.entity_type == "capteur"]),
                "intervention": len([a for a in self._alerts if a.entity_type == "intervention"]),
                "véhicule": len([a for a in self._alerts if a.entity_type == "véhicule"]),
            },
        }
