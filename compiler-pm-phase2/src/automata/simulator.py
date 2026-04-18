"""
Automata Simulator — Simulation pas-à-pas interactive
Conforme à l'énoncé §1.1 — Scénario complet p.3

Features:
  - Simulation pas-à-pas avec historique complet
  - Scénarios prédéfinis (énoncé)
  - Détection automatique d'alertes
  - Vérification de validité de séquences
  - Replay et snapshot
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum

from .automata import (
    SensorAutomata, InterventionAutomata, VehicleAutomata,
    SensorState, InterventionState, VehicleState,
    create_automata,
)
from .base import AutomataBase


class SimulationStep:
    """Un pas de simulation"""
    def __init__(self, step_num: int, event: str, from_state: str,
                 to_state: str, success: bool, message: str):
        self.step_num = step_num
        self.event = event
        self.from_state = from_state
        self.to_state = to_state
        self.success = success
        self.message = message
        self.timestamp = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "step": self.step_num,
            "event": self.event,
            "from": self.from_state,
            "to": self.to_state,
            "ok": self.success,
            "message": self.message,
            "timestamp": self.timestamp,
        }


class SimulationResult:
    """Résultat complet d'une simulation"""
    def __init__(self):
        self.automata_type: str = ""
        self.entity_id: str = ""
        self.initial_state: str = ""
        self.final_state: str = ""
        self.steps: List[SimulationStep] = []
        self.success: bool = True
        self.accepted: bool = False
        self.duration_ms: float = 0

    @property
    def total_steps(self) -> int:
        return len(self.steps)

    @property
    def successful_steps(self) -> int:
        return sum(1 for s in self.steps if s.success)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "automata_type": self.automata_type,
            "entity_id": self.entity_id,
            "initial_state": self.initial_state,
            "final_state": self.final_state,
            "total_steps": self.total_steps,
            "successful_steps": self.successful_steps,
            "success": self.success,
            "accepted": self.accepted,
            "steps": [s.to_dict() for s in self.steps],
        }

    def summary(self) -> str:
        status = "✅ SUCCÈS" if self.success else "❌ ÉCHEC"
        accepted = " (état accepteur)" if self.accepted else " (non-accepteur)"
        return (
            f"{status} — {self.initial_state} → {self.final_state}{accepted}\n"
            f"  {self.successful_steps}/{self.total_steps} transitions réussies"
        )


class AutomataSimulator:
    """
    Simulateur interactif d'automates à états finis.
    
    Supporte:
      - Simulation complète d'une séquence d'événements
      - Simulation pas-à-pas (step-by-step)
      - Scénarios prédéfinis de l'énoncé
      - Détection d'alertes automatiques
    """

    def __init__(self):
        self._active_simulations: Dict[str, AutomataBase] = {}

    def simulate(
        self,
        automata_type: str,
        events: List[str],
        entity_id: str = "SIM-001",
        actor: str = "simulator",
    ) -> SimulationResult:
        """
        Exécuter une simulation complète.
        
        Args:
            automata_type: 'capteur', 'intervention', ou 'véhicule'
            events: Liste d'événements à appliquer
            entity_id: ID de l'entité simulée
            actor: Acteur de la simulation
            
        Returns:
            SimulationResult avec tous les détails
        """
        result = SimulationResult()
        result.automata_type = automata_type
        result.entity_id = entity_id

        start = datetime.now()

        # Create fresh automata
        automata = create_automata(automata_type, entity_id)
        result.initial_state = automata.get_state()

        for i, event in enumerate(events):
            from_state = automata.get_state()
            try:
                automata.trigger(event, actor=actor)
                step = SimulationStep(
                    step_num=i + 1,
                    event=event,
                    from_state=from_state,
                    to_state=automata.get_state(),
                    success=True,
                    message=f"δ({from_state}, {event}) = {automata.get_state()}"
                )
            except ValueError as e:
                step = SimulationStep(
                    step_num=i + 1,
                    event=event,
                    from_state=from_state,
                    to_state="∅",
                    success=False,
                    message=str(e)
                )
                result.success = False
                result.steps.append(step)
                break

            result.steps.append(step)

        result.final_state = automata.get_state()
        result.accepted = automata.current_state in automata.get_final_states()
        result.duration_ms = (datetime.now() - start).total_seconds() * 1000

        return result

    def verify_sequence(
        self,
        automata_type: str,
        events: List[str],
        entity_id: str = "VERIFY-001",
    ) -> Dict[str, Any]:
        """
        Vérifier si une séquence est valide SANS modifier d'état persistent.
        
        Returns:
            {valid, accepted, path, message}
        """
        automata = create_automata(automata_type, entity_id)
        return automata.verify_sequence(events)

    def detect_alerts(self, automata: AutomataBase) -> List[Dict[str, str]]:
        """
        Détecter les alertes basées sur l'état courant et l'historique.
        
        Alertes:
          - Capteur hors service (critique)
          - Capteur signalé (attention)
          - Intervention rejetée (warning)
          - Véhicule en panne (attention)
        """
        alerts = []
        state = automata.get_state()
        name = automata.get_automata_name()

        if isinstance(automata, SensorAutomata):
            if automata.current_state == SensorState.HORS_SERVICE:
                alerts.append({
                    "level": "critical",
                    "icon": "🔴",
                    "message": f"Capteur {automata.entity_id} est HORS SERVICE",
                    "action": "Intervention immédiate requise",
                })
            elif automata.current_state == SensorState.SIGNALE:
                alerts.append({
                    "level": "warning",
                    "icon": "⚠️",
                    "message": f"Capteur {automata.entity_id} est SIGNALÉ — anomalie détectée",
                    "action": "Planifier une vérification",
                })
            elif automata.current_state == SensorState.EN_MAINTENANCE:
                alerts.append({
                    "level": "info",
                    "icon": "🔧",
                    "message": f"Capteur {automata.entity_id} en maintenance",
                    "action": "Suivi en cours",
                })

        elif isinstance(automata, InterventionAutomata):
            if automata.current_state == InterventionState.REJETEE:
                alerts.append({
                    "level": "warning",
                    "icon": "❌",
                    "message": f"Intervention {automata.entity_id} REJETÉE",
                    "action": "Réinitialiser ou créer nouvelle demande",
                })

        elif isinstance(automata, VehicleAutomata):
            if automata.current_state == VehicleState.EN_PANNE:
                alerts.append({
                    "level": "critical",
                    "icon": "🚨",
                    "message": f"Véhicule {automata.entity_id} EN PANNE",
                    "action": "Envoyer équipe de dépannage",
                })

        return alerts

    # ── Predefined Scenarios ──────────────────────────────────────

    @staticmethod
    def get_scenarios() -> Dict[str, Dict[str, Any]]:
        """
        Scénarios prédéfinis conformes à l'énoncé PM-Compilation-25-26 p.3
        """
        return {
            # ── Capteur ──
            "Scénario Complet Énoncé (p.3)": {
                "description": (
                    "Scénario principal de l'énoncé:\n"
                    "1. Capteur installé et activé\n"
                    "2. Anomalie détectée → Capteur signalé\n"
                    "3. Réparation lancée → Maintenance\n"
                    "4. Réparation complète → Retour actif"
                ),
                "type": "capteur",
                "events": ["installation", "détection_anomalie", "réparation", "réparation_complète"],
                "expected_final": "Actif",
            },
            "Capteur — Panne Directe": {
                "description": "Un capteur actif tombe en panne sans passer par Signalé",
                "type": "capteur",
                "events": ["installation", "panne"],
                "expected_final": "Hors Service",
            },
            "Capteur — Fausse Alerte": {
                "description": "Anomalie détectée puis identifiée comme fausse alerte",
                "type": "capteur",
                "events": ["installation", "détection_anomalie", "fausse_alerte"],
                "expected_final": "Actif",
            },
            "Capteur — Remplacement": {
                "description": "Capteur hors service remplacé par un nouveau",
                "type": "capteur",
                "events": ["installation", "panne", "remplacement", "installation"],
                "expected_final": "Actif",
            },

            # ── Intervention ──
            "Intervention Complète": {
                "description": (
                    "Workflow complet d'intervention:\n"
                    "Demande → Tech1 assigné → Tech2 valide → IA valide → Terminée"
                ),
                "type": "intervention",
                "events": ["assigner_tech1", "rapport_tech1", "valider_ia", "compléter"],
                "expected_final": "Terminée",
            },
            "Intervention Rejetée et Réinitialisée": {
                "description": "Demande rejetée puis réinitialisée pour nouveau traitement",
                "type": "intervention",
                "events": ["rejeter", "réinitialiser", "assigner_tech1"],
                "expected_final": "Tech1_Assigné",
            },

            # ── Véhicule ──
            "Trajet Normal": {
                "description": "Départ → Destination atteinte → Stationnement",
                "type": "véhicule",
                "events": ["démarrage", "destination_atteinte", "stationnement"],
                "expected_final": "Stationné",
            },
            "Trajet avec Panne": {
                "description": "Panne en route, réparation, puis continuation du trajet",
                "type": "véhicule",
                "events": ["démarrage", "panne_détectée", "réparation_complète", "destination_atteinte"],
                "expected_final": "Arrivé",
            },
            "Véhicule Remorqué": {
                "description": "Panne en route → Remorquage → Retour au stationnement",
                "type": "véhicule",
                "events": ["démarrage", "panne_détectée", "remorquage"],
                "expected_final": "Stationné",
            },

            # ── Tests invalides ──
            "Séquence Invalide — Capteur": {
                "description": "Test: tenter 'panne' depuis état Inactif (doit échouer)",
                "type": "capteur",
                "events": ["panne"],
                "expected_final": None,  # Should fail
            },
            "Séquence Invalide — Véhicule": {
                "description": "Test: tenter 'destination_atteinte' depuis Stationné",
                "type": "véhicule",
                "events": ["destination_atteinte"],
                "expected_final": None,
            },
        }

    def run_all_scenarios(self) -> Dict[str, SimulationResult]:
        """Run all predefined scenarios and return results"""
        results = {}
        for name, scenario in self.get_scenarios().items():
            result = self.simulate(
                automata_type=scenario["type"],
                events=scenario["events"],
                entity_id=f"SC-{name[:8]}",
            )
            results[name] = result
        return results
