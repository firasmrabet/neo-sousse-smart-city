"""
Automates Concrets — Capteur, Intervention, Véhicule
Conformes à l'énoncé PM-Compilation-25-26 §1.1

Chaque automate:
  - Définit ses états, transitions, états finaux
  - Persiste les transitions dans la BD Phase 1
  - Génère les diagrammes de transition (Graphviz)
"""

from enum import Enum
from typing import Dict, List, Optional
from .base import AutomataBase
import logging

logger = logging.getLogger(__name__)

# DB connection (Phase 1 MySQL)
try:
    from ..db_connection import get_db
except ImportError:
    try:
        from src.db_connection import get_db
    except ImportError:
        get_db = None


# ═══════════════════════════════════════════════════════════════════
# AUTOMATE 1: Cycle de Vie d'un Capteur
# Énoncé §1.1a:
#   États: INACTIF → ACTIF → SIGNALÉ → EN_MAINTENANCE → HORS_SERVICE
#   Événements: installation, détection_anomalie, réparation, panne
# ═══════════════════════════════════════════════════════════════════

class SensorState(Enum):
    INACTIF = "Inactif"
    ACTIF = "Actif"
    SIGNALE = "Signalé"
    EN_MAINTENANCE = "En Maintenance"
    HORS_SERVICE = "Hors Service"


class SensorAutomata(AutomataBase):
    """
    Automate DFA: Cycle de vie d'un Capteur IoT
    
    A = (Q, Σ, δ, q₀, F) où:
      Q = {Inactif, Actif, Signalé, En Maintenance, Hors Service}
      Σ = {installation, détection_anomalie, réparation, 
           réparation_complète, panne, remplacement, réactivation,
           fausse_alerte}
      q₀ = Inactif
      F = {Actif} (état opérationnel souhaité — le capteur fonctionne)
    """

    def __init__(self, entity_id: str):
        self.entity_id = entity_id
        super().__init__(entity_id)

    def get_automata_name(self) -> str:
        return "Cycle de Vie — Capteur IoT"

    def get_initial_state(self) -> SensorState:
        return SensorState.INACTIF

    def get_states(self) -> List[SensorState]:
        return list(SensorState)

    def get_final_states(self) -> List[SensorState]:
        return [SensorState.ACTIF]

    def get_transitions(self) -> Dict[SensorState, Dict[str, SensorState]]:
        S = SensorState
        return {
            S.INACTIF: {
                "installation": S.ACTIF,
            },
            S.ACTIF: {
                "détection_anomalie": S.SIGNALE,
                "panne": S.HORS_SERVICE,
            },
            S.SIGNALE: {
                "réparation": S.EN_MAINTENANCE,
                "panne": S.HORS_SERVICE,
                "fausse_alerte": S.ACTIF,
            },
            S.EN_MAINTENANCE: {
                "réparation_complète": S.ACTIF,
                "panne": S.HORS_SERVICE,
            },
            S.HORS_SERVICE: {
                "remplacement": S.INACTIF,
                "réactivation": S.ACTIF,
            },
        }

    def trigger(self, event: str, actor: str = "system") -> SensorState:
        old = self.current_state
        new = super().trigger(event, actor)
        self._persist(old, new, event, actor)
        return new

    def _persist(self, old: SensorState, new: SensorState, event: str, actor: str):
        if not get_db:
            return
        try:
            db = get_db()
            # capteurs_history
            db.execute_query(
                "INSERT INTO capteurs_history (sensor_uuid, old_statut, new_statut, event) "
                "VALUES (%s, %s, %s, %s)",
                (self.entity_id, old.value, new.value, event)
            )
            # logs_automata
            db.execute_query(
                "INSERT INTO logs_automata (automata_type, entity_id, entity_type, "
                "old_state, new_state, trigger_reason) "
                "VALUES (%s, %s, %s, %s, %s, %s)",
                ("sensor", self.entity_id, "capteur", old.value, new.value, event)
            )
        except Exception as e:
            logger.error(f"Persist sensor transition error: {e}")


# ═══════════════════════════════════════════════════════════════════
# AUTOMATE 2: Processus de Validation d'Intervention
# Énoncé §1.1b:
#   Implique 2 techniciens + validation IA
#   États: DEMANDE → TECH1_ASSIGNÉ → TECH2_VALIDE → IA_VALIDE → TERMINÉ
# ═══════════════════════════════════════════════════════════════════

class InterventionState(Enum):
    DEMANDE = "Demande"
    TECH1_ASSIGNE = "Tech1_Assigné"
    TECH2_VALIDE = "Tech2_Valide"
    IA_VALIDE = "IA_Valide"
    TERMINEE = "Terminée"
    REJETEE = "Rejetée"


class InterventionAutomata(AutomataBase):
    """
    Automate DFA: Processus de Validation d'Intervention
    
    A = (Q, Σ, δ, q₀, F) où:
      Q = {Demande, Tech1_Assigné, Tech2_Valide, IA_Valide, Terminée, Rejetée}
      Σ = {assigner_tech1, rapport_tech1, valider_ia, compléter, rejeter, réinitialiser}
      q₀ = Demande
      F = {Terminée}
    """

    def __init__(self, entity_id: str):
        self.entity_id = entity_id
        super().__init__(entity_id)

    def get_automata_name(self) -> str:
        return "Validation d'Intervention — Workflow"

    def get_initial_state(self) -> InterventionState:
        return InterventionState.DEMANDE

    def get_states(self) -> List[InterventionState]:
        return list(InterventionState)

    def get_final_states(self) -> List[InterventionState]:
        return [InterventionState.TERMINEE]

    def get_transitions(self) -> Dict[InterventionState, Dict[str, InterventionState]]:
        S = InterventionState
        return {
            S.DEMANDE: {
                "assigner_tech1": S.TECH1_ASSIGNE,
                "rejeter": S.REJETEE,
            },
            S.TECH1_ASSIGNE: {
                "rapport_tech1": S.TECH2_VALIDE,
                "rejeter": S.REJETEE,
            },
            S.TECH2_VALIDE: {
                "valider_ia": S.IA_VALIDE,
                "rejeter": S.REJETEE,
            },
            S.IA_VALIDE: {
                "compléter": S.TERMINEE,
                "rejeter": S.REJETEE,
            },
            S.TERMINEE: {},
            S.REJETEE: {
                "réinitialiser": S.DEMANDE,
            },
        }

    def trigger(self, event: str, actor: str = "system") -> InterventionState:
        old = self.current_state
        new = super().trigger(event, actor)
        self._persist(old, new, event, actor)
        return new

    def _persist(self, old: InterventionState, new: InterventionState, event: str, actor: str):
        if not get_db:
            return
        try:
            db = get_db()
            db.execute_query(
                "INSERT INTO interventions_history "
                "(intervention_id, old_statut, new_statut, actor_role) "
                "VALUES (%s, %s, %s, %s)",
                (int(self.entity_id), old.value, new.value, actor)
            )
            db.execute_query(
                "INSERT INTO logs_automata (automata_type, entity_id, entity_type, "
                "old_state, new_state, trigger_reason) "
                "VALUES (%s, %s, %s, %s, %s, %s)",
                ("intervention", self.entity_id, "intervention", old.value, new.value, event)
            )
        except Exception as e:
            logger.error(f"Persist intervention transition error: {e}")


# ═══════════════════════════════════════════════════════════════════
# AUTOMATE 3: Trajet d'un Véhicule Autonome
# Énoncé §1.1c:
#   États: STATIONNÉ → EN_ROUTE → EN_PANNE → ARRIVÉ
# ═══════════════════════════════════════════════════════════════════

class VehicleState(Enum):
    STATIONNE = "Stationné"
    EN_ROUTE = "En Route"
    EN_PANNE = "En Panne"
    ARRIVE = "Arrivé"


class VehicleAutomata(AutomataBase):
    """
    Automate DFA: Trajet d'un Véhicule Autonome
    
    A = (Q, Σ, δ, q₀, F) où:
      Q = {Stationné, En Route, En Panne, Arrivé}
      Σ = {démarrage, destination_atteinte, panne_détectée, 
           réparation_complète, remorquage, stationnement, redémarrage}
      q₀ = Stationné
      F = {Arrivé, Stationné} (destination atteinte ou retour au stationnement)
    """

    def __init__(self, entity_id: str, latitude: float = None, longitude: float = None):
        self.entity_id = entity_id
        self.latitude = latitude
        self.longitude = longitude
        super().__init__(entity_id)

    def get_automata_name(self) -> str:
        return "Trajet — Véhicule Autonome"

    def get_initial_state(self) -> VehicleState:
        return VehicleState.STATIONNE

    def get_states(self) -> List[VehicleState]:
        return list(VehicleState)

    def get_final_states(self) -> List[VehicleState]:
        return [VehicleState.ARRIVE, VehicleState.STATIONNE]

    def get_transitions(self) -> Dict[VehicleState, Dict[str, VehicleState]]:
        S = VehicleState
        return {
            S.STATIONNE: {
                "démarrage": S.EN_ROUTE,
            },
            S.EN_ROUTE: {
                "panne_détectée": S.EN_PANNE,
                "destination_atteinte": S.ARRIVE,
            },
            S.EN_PANNE: {
                "réparation_complète": S.EN_ROUTE,
                "remorquage": S.STATIONNE,
            },
            S.ARRIVE: {
                "stationnement": S.STATIONNE,
                "redémarrage": S.EN_ROUTE,
            },
        }

    def update_gps(self, lat: float, lon: float):
        self.latitude = lat
        self.longitude = lon

    def trigger(self, event: str, actor: str = "system") -> VehicleState:
        old = self.current_state
        new = super().trigger(event, actor)
        self._persist(old, new, event)
        return new

    def _persist(self, old: VehicleState, new: VehicleState, event: str):
        if not get_db:
            return
        try:
            db = get_db()
            db.execute_query(
                "INSERT INTO vehicles_history "
                "(vehicle_plaque, old_statut, new_statut, latitude, longitude) "
                "VALUES (%s, %s, %s, %s, %s)",
                (self.entity_id, old.value, new.value, self.latitude, self.longitude)
            )
            db.execute_query(
                "INSERT INTO logs_automata (automata_type, entity_id, entity_type, "
                "old_state, new_state, trigger_reason) "
                "VALUES (%s, %s, %s, %s, %s, %s)",
                ("vehicle", self.entity_id, "vehicle", old.value, new.value, event)
            )
        except Exception as e:
            logger.error(f"Persist vehicle transition error: {e}")


# ═══════════════════════════════════════════════════════════════════
# Factory
# ═══════════════════════════════════════════════════════════════════

AUTOMATA_REGISTRY = {
    "capteur": SensorAutomata,
    "intervention": InterventionAutomata,
    "véhicule": VehicleAutomata,
}


def create_automata(automata_type: str, entity_id: str, **kwargs) -> AutomataBase:
    """Factory pour créer un automate par type"""
    cls = AUTOMATA_REGISTRY.get(automata_type)
    if not cls:
        raise ValueError(f"Type d'automate inconnu: {automata_type}. "
                         f"Disponibles: {list(AUTOMATA_REGISTRY.keys())}")
    return cls(entity_id, **kwargs)
