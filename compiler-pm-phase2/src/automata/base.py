"""
Automates à États Finis — Classe de Base
Définition formelle DFA: A = (Q, Σ, δ, q₀, F)
Conforme au cours: 3_AutomatesAEtatsFinis TL

Implémente:
  - Représentation formelle (quintuplet)
  - Table de transition
  - Diagramme de transition (Graphviz DOT)
  - Vérification de séquences
  - Historique des transitions
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import List, Dict, Tuple, Callable, Optional, Set, Any
from datetime import datetime
import json


class AutomataBase(ABC):
    """
    Classe de base pour Automates à États Finis Déterministes (DFA).
    
    Formalisme: A = (Q, Σ, δ, q₀, F)
      - Q : ensemble fini d'états
      - Σ : alphabet (ensemble d'événements)
      - δ : fonction de transition  δ: Q × Σ → Q
      - q₀: état initial
      - F : ensemble d'états finaux (accepteurs)
    """

    def __init__(self, entity_id: str):
        self.entity_id = entity_id
        self.current_state = self.get_initial_state()
        self.history: List[Dict[str, Any]] = []
        self.actions: Dict[str, Callable] = {}
        self.created_at = datetime.now()

    # ── Abstract methods ──────────────────────────────────────────

    @abstractmethod
    def get_initial_state(self) -> Enum:
        """q₀ — état initial"""
        ...

    @abstractmethod
    def get_states(self) -> List[Enum]:
        """Q — ensemble fini d'états"""
        ...

    @abstractmethod
    def get_final_states(self) -> List[Enum]:
        """F — ensemble d'états finaux (accepteurs)"""
        ...

    @abstractmethod
    def get_transitions(self) -> Dict[Enum, Dict[str, Enum]]:
        """δ — fonction de transition (table)"""
        ...

    @abstractmethod
    def get_automata_name(self) -> str:
        """Nom humain de l'automate"""
        ...

    # ── Formal definition ─────────────────────────────────────────

    def get_alphabet(self) -> Set[str]:
        """Σ — alphabet (ensemble de tous les événements possibles)"""
        events = set()
        for state_transitions in self.get_transitions().values():
            events.update(state_transitions.keys())
        return events

    def get_formal_definition(self) -> Dict[str, Any]:
        """Retourner la définition formelle A = (Q, Σ, δ, q₀, F)"""
        return {
            "name": self.get_automata_name(),
            "Q": [s.value for s in self.get_states()],
            "Sigma": sorted(self.get_alphabet()),
            "delta": {
                state.value: {
                    event: target.value
                    for event, target in transitions.items()
                }
                for state, transitions in self.get_transitions().items()
            },
            "q0": self.get_initial_state().value,
            "F": [s.value for s in self.get_final_states()],
        }

    # ── Transition table (course format) ──────────────────────────

    def get_transition_table(self) -> List[Dict[str, str]]:
        """
        Générer la table de transition au format du cours.
        Lignes = états, Colonnes = événements.
        '→' marque l'état initial, '*' marque les états finaux.
        """
        states = self.get_states()
        alphabet = sorted(self.get_alphabet())
        transitions = self.get_transitions()
        initial = self.get_initial_state()
        finals = set(self.get_final_states())

        rows = []
        for state in states:
            prefix = ""
            if state == initial:
                prefix += "→ "
            if state in finals:
                prefix += "* "
            row = {"État": f"{prefix}{state.value}"}
            for event in alphabet:
                target = transitions.get(state, {}).get(event)
                row[event] = target.value if target else "∅"
            rows.append(row)
        return rows

    # ── Transition execution ──────────────────────────────────────

    def is_valid_event(self, event: str) -> bool:
        """Vérifier si un événement est valide depuis l'état courant"""
        return event in self.get_transitions().get(self.current_state, {})

    def get_valid_events(self) -> List[str]:
        """Retourner la liste des événements valides depuis l'état courant"""
        return list(self.get_transitions().get(self.current_state, {}).keys())

    def trigger(self, event: str, actor: str = "system") -> Enum:
        """
        Déclencher une transition.
        
        Args:
            event: Événement à déclencher
            actor: Qui cause la transition
            
        Returns:
            Nouvel état après transition
            
        Raises:
            ValueError: Si la transition est invalide
        """
        transitions = self.get_transitions()
        state_trans = transitions.get(self.current_state, {})

        if event not in state_trans:
            valid = list(state_trans.keys())
            raise ValueError(
                f"Transition invalide: δ({self.current_state.value}, {event}) = ∅. "
                f"Événements valides depuis '{self.current_state.value}': {valid}"
            )

        old_state = self.current_state
        new_state = state_trans[event]
        self.current_state = new_state

        # Record history
        record = {
            "timestamp": datetime.now().isoformat(),
            "from_state": old_state.value,
            "event": event,
            "to_state": new_state.value,
            "actor": actor,
        }
        self.history.append(record)

        # Execute registered action callback
        if event in self.actions:
            self.actions[event](old_state, new_state)

        return new_state

    # ── Sequence verification ─────────────────────────────────────

    def verify_sequence(self, events: List[str], from_state: Optional[Enum] = None) -> Dict[str, Any]:
        """
        Vérifier si une séquence d'événements est valide.
        Ne modifie PAS l'état courant de l'automate.
        
        Returns:
            {valid: bool, path: [...], error_at: index|None, final_state: str}
        """
        state = from_state or self.current_state
        transitions = self.get_transitions()
        path = [{"state": state.value, "event": None}]

        for i, event in enumerate(events):
            state_trans = transitions.get(state, {})
            if event not in state_trans:
                return {
                    "valid": False,
                    "path": path,
                    "error_at": i,
                    "error_event": event,
                    "error_state": state.value,
                    "message": f"δ({state.value}, {event}) = ∅ — transition invalide à l'étape {i+1}",
                }
            state = state_trans[event]
            path.append({"state": state.value, "event": event})

        finals = set(self.get_final_states())
        accepted = state in finals

        return {
            "valid": True,
            "accepted": accepted,
            "path": path,
            "final_state": state.value,
            "message": f"Séquence valide. État final: {state.value}"
                       + (" (état accepteur ✓)" if accepted else " (non-accepteur)"),
        }

    # ── Graphviz DOT generation ───────────────────────────────────

    def to_graphviz_dot(self, highlight_state: Optional[Enum] = None) -> str:
        """
        Générer le code DOT pour Graphviz.
        Conforme aux diagrammes de transition du cours.
        """
        highlight = highlight_state or self.current_state
        states = self.get_states()
        transitions = self.get_transitions()
        initial = self.get_initial_state()
        finals = set(self.get_final_states())

        # Color scheme — light bg for clear black doublecircle visibility
        colors = {
            "active": "#22c55e",     # green
            "initial": "#3b82f6",    # blue
            "final": "#f59e0b",      # amber
            "normal": "#cbd5e1",     # light slate
            "bg": "#f0f4f8",         # light bg
            "text": "#1e293b",       # dark text
            "edge": "#475569",       # edge color
        }

        lines = [
            'digraph {',
            '  rankdir=LR;',
            f'  bgcolor="{colors["bg"]}";',
            '  pad=0.5;',
            f'  node [fontname="Segoe UI" fontsize=11 style=filled fontcolor="{colors["text"]}"];',
            f'  edge [fontname="Segoe UI" fontsize=9 color="{colors["edge"]}" fontcolor="{colors["text"]}"];',
            '',
            '  // Initial arrow',
            '  __start__ [shape=point width=0 height=0 label=""];',
            f'  __start__ -> "{initial.value}" [color="{colors["initial"]}" penwidth=2];',
            '',
        ]

        # Nodes
        for state in states:
            is_final = state in finals
            is_active = (state == highlight)
            
            if is_active:
                # LED glow: bright neon green fill (like illuminated LED)
                fill = "#00ff55"
            elif state == initial:
                fill = colors["initial"]
            elif is_final:
                fill = colors["final"]
            else:
                fill = colors["normal"]

            # Active state: bright LED glow inside, normal border
            if is_active:
                if is_final:
                    lines.append(
                        f'  "{state.value}" [shape=doublecircle fillcolor="{fill}" '
                        f'fontcolor="#000000" color="#000000" penwidth=1.0 '
                        f'width=1.6 height=1.6];'
                    )
                else:
                    lines.append(
                        f'  "{state.value}" [shape=circle fillcolor="{fill}" '
                        f'fontcolor="#000000" color="#334155" penwidth=1.0];'
                    )
            elif is_final:
                # Final states: two thin BLACK concentric circles (textbook style)
                lines.append(
                    f'  "{state.value}" [shape=doublecircle fillcolor="{fill}" '
                    f'fontcolor="white" color="#000000" penwidth=1.0 width=1.6 height=1.6];'
                )
            else:
                lines.append(
                    f'  "{state.value}" [shape=circle fillcolor="{fill}" '
                    f'color="#334155" penwidth=1];'
                )

        lines.append("")

        # Edges — merge parallel edges between same nodes
        edge_labels: Dict[Tuple[str, str], List[str]] = {}
        for src, trans in transitions.items():
            for event, dst in trans.items():
                key = (src.value, dst.value)
                edge_labels.setdefault(key, []).append(event)

        event_colors = [
            "#60a5fa", "#f472b6", "#34d399", "#fbbf24",
            "#a78bfa", "#fb923c", "#38bdf8", "#e879f9",
        ]

        for idx, ((src, dst), events) in enumerate(edge_labels.items()):
            label = "\\n".join(events)
            c = event_colors[idx % len(event_colors)]
            lines.append(
                f'  "{src}" -> "{dst}" [label="{label}" color="{c}" fontcolor="{c}" penwidth=1.5];'
            )

        lines.append("}")
        return "\n".join(lines)

    # ── Utility ───────────────────────────────────────────────────

    def get_state(self) -> str:
        return self.current_state.value

    def get_state_enum(self) -> Enum:
        return self.current_state

    def get_history(self) -> List[Dict[str, Any]]:
        return list(self.history)

    def reset(self) -> None:
        self.current_state = self.get_initial_state()
        self.history.clear()

    def set_state_by_value(self, state_value: str) -> None:
        """Set automata to a specific state by its string value (from DB)."""
        for s in self.get_states():
            if s.value == state_value:
                self.current_state = s
                return
        raise ValueError(f"État inconnu: {state_value}")

    def register_action(self, event: str, callback: Callable) -> None:
        self.actions[event] = callback

    def __repr__(self) -> str:
        return (
            f"<{self.__class__.__name__} "
            f"entity={self.entity_id} "
            f"state={self.current_state.value}>"
        )
