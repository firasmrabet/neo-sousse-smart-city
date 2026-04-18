"""
Automata Engine — Point d'entrée haut niveau
Gère la création, simulation et scénarios des automates.
"""

from typing import Dict, List, Optional, Any
from .automata import (
    SensorAutomata, InterventionAutomata, VehicleAutomata,
    SensorState, InterventionState, VehicleState,
    create_automata, AUTOMATA_REGISTRY,
)
from .base import AutomataBase


class AutomataEngine:
    """Moteur centralisé pour gérer tous les automates"""

    def __init__(self):
        self._instances: Dict[str, AutomataBase] = {}

    def create(self, automata_type: str, entity_id: str, **kw) -> AutomataBase:
        key = f"{automata_type}:{entity_id}"
        a = create_automata(automata_type, entity_id, **kw)
        self._instances[key] = a
        return a

    def get(self, automata_type: str, entity_id: str) -> Optional[AutomataBase]:
        return self._instances.get(f"{automata_type}:{entity_id}")

    def get_or_create(self, automata_type: str, entity_id: str, **kw) -> AutomataBase:
        existing = self.get(automata_type, entity_id)
        if existing:
            return existing
        return self.create(automata_type, entity_id, **kw)

    def run_scenario(
        self,
        automata: AutomataBase,
        events: List[str],
        actor: str = "scenario",
    ) -> Dict[str, Any]:
        """
        Exécuter un scénario (séquence d'événements) sur un automate.
        
        Conformément à la théorie DFA:
          - 'success' = toutes les transitions sont valides (δ définie)
          - 'accepted' = l'état final ∈ F (états accepteurs)
          
        Un mot w est accepté par A ssi δ*(q₀, w) ∈ F
        
        Returns:
            {start, final, steps, success, accepted, is_final_state, total_steps}
        """
        start = automata.get_state()
        steps = []

        for event in events:
            from_state = automata.get_state()
            try:
                automata.trigger(event, actor=actor)
                steps.append({
                    "event": event,
                    "from": from_state,
                    "to": automata.get_state(),
                    "ok": True,
                    "message": f"✓ δ({from_state}, {event}) = {automata.get_state()}"
                })
            except ValueError as e:
                steps.append({
                    "event": event,
                    "from": from_state,
                    "to": None,
                    "ok": False,
                    "message": f"✗ {str(e)}"
                })
                break

        # Check if final state is an accepting state (∈ F)
        final_state_enum = automata.get_state_enum()
        final_states = set(automata.get_final_states())
        is_final = final_state_enum in final_states
        all_valid = all(s["ok"] for s in steps)

        return {
            "start": start,
            "final": automata.get_state(),
            "steps": steps,
            "success": all_valid,
            "accepted": all_valid and is_final,  # DFA acceptance: δ*(q₀, w) ∈ F
            "is_final_state": is_final,
            "final_states": [s.value for s in final_states],
            "total_steps": len(steps),
        }

    # ── Predefined Scenarios (from assignment p.3) ────────────────

    @staticmethod
    def get_predefined_scenarios() -> Dict[str, Dict]:
        """Scénarios prédéfinis conformes à l'énoncé"""
        return {
            # ── CAPTEUR ──────────────────────────────────────────
            "Scénario Complet — Énoncé p.3": {
                "description": (
                    "Cycle de vie COMPLET traversant les 5 états:\n"
                    "1. Installation du capteur (Inactif → Actif)\n"
                    "2. Détection d'anomalie (Actif → Signalé)\n"
                    "3. Envoi en maintenance (Signalé → En Maintenance)\n"
                    "4. Réparation terminée (En Maintenance → Actif)\n"
                    "5. Panne critique (Actif → Hors Service)\n"
                    "6. Remplacement du capteur (Hors Service → Inactif)"
                ),
                "automata_type": "capteur",
                "events": [
                    "installation",          # Inactif → Actif
                    "détection_anomalie",    # Actif → Signalé
                    "réparation",            # Signalé → En Maintenance
                    "réparation_complète",   # En Maintenance → Actif
                    "panne",                 # Actif → Hors Service
                    "remplacement",          # Hors Service → Inactif
                ],
            },
            "Cycle Maintenance Capteur": {
                "description": (
                    "Cycle simple de maintenance:\n"
                    "Installation → Anomalie → Maintenance → Retour actif"
                ),
                "automata_type": "capteur",
                "events": [
                    "installation",          # Inactif → Actif
                    "détection_anomalie",    # Actif → Signalé
                    "réparation",            # Signalé → En Maintenance
                    "réparation_complète",   # En Maintenance → Actif
                ],
            },
            "Capteur — Fausse Alerte": {
                "description": (
                    "Le capteur est signalé mais l'alerte s'avère fausse:\n"
                    "Installation → Anomalie → Fausse alerte → Retour actif"
                ),
                "automata_type": "capteur",
                "events": [
                    "installation",          # Inactif → Actif
                    "détection_anomalie",    # Actif → Signalé
                    "fausse_alerte",         # Signalé → Actif
                ],
            },
            "Capteur — Panne Directe": {
                "description": "Capteur actif tombe directement en panne sans passer par la maintenance",
                "automata_type": "capteur",
                "events": [
                    "installation",          # Inactif → Actif
                    "panne",                 # Actif → Hors Service
                ],
            },
            "Capteur — Réactivation Hors Service": {
                "description": (
                    "Capteur réactivé directement depuis l'état Hors Service:\n"
                    "Installation → Panne → Réactivation directe"
                ),
                "automata_type": "capteur",
                "events": [
                    "installation",          # Inactif → Actif
                    "panne",                 # Actif → Hors Service
                    "réactivation",          # Hors Service → Actif
                ],
            },
            "⚠️ Séquence Invalide — Test": {
                "description": (
                    "🧪 TEST VOLONTAIRE: Vérifie que l'automate REJETTE "
                    "correctement une transition invalide.\n"
                    "L'événement 'panne' n'est pas valide depuis l'état 'Inactif'.\n"
                    "Résultat attendu: ÉCHEC (ce comportement est correct)"
                ),
                "automata_type": "capteur",
                "events": ["panne"],  # Invalid from INACTIF — expected to fail
            },
            # ── INTERVENTION ─────────────────────────────────────
            "Intervention Complète": {
                "description": (
                    "Workflow complet de validation:\n"
                    "Demande → Tech1 assigné → Tech2 valide → IA valide → Terminée"
                ),
                "automata_type": "intervention",
                "events": [
                    "assigner_tech1",
                    "rapport_tech1",
                    "valider_ia",
                    "compléter",
                ],
            },
            "Intervention Rejetée puis Relancée": {
                "description": (
                    "Demande rejetée puis réinitialisée pour un nouveau traitement"
                ),
                "automata_type": "intervention",
                "events": ["rejeter", "réinitialiser"],
            },
            # ── VÉHICULE ─────────────────────────────────────────
            "Trajet Normal": {
                "description": (
                    "Trajet simple sans incident:\n"
                    "Départ → Arrivée → Stationnement"
                ),
                "automata_type": "véhicule",
                "events": [
                    "démarrage",
                    "destination_atteinte",
                    "stationnement",
                ],
            },
            "Trajet avec Panne": {
                "description": (
                    "Trajet interrompu par une panne puis reprise:\n"
                    "Départ → Panne → Réparation → Arrivée"
                ),
                "automata_type": "véhicule",
                "events": [
                    "démarrage",
                    "panne_détectée",
                    "réparation_complète",
                    "destination_atteinte",
                ],
            },
        }

    def list_instances(self) -> List[Dict]:
        return [
            {"key": k, "type": type(v).__name__, "state": v.get_state()}
            for k, v in self._instances.items()
        ]
