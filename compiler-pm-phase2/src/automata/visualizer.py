"""
Automata Visualizer — Génération professionnelle de diagrammes
Export: PNG, SVG, PDF via Graphviz
Table de transition formatée pour affichage et rapport
"""

import os
import logging
from typing import Optional, List, Dict
from enum import Enum

logger = logging.getLogger(__name__)

try:
    import graphviz as gv
    HAS_GRAPHVIZ = True
except ImportError:
    HAS_GRAPHVIZ = False
    logger.warning("graphviz Python package not installed — export disabled")


class AutomataVisualizer:
    """
    Visualisation professionnelle des automates à états finis.
    
    Features:
      - Génération de diagrammes Graphviz (DOT)
      - Export PNG/SVG/PDF
      - État courant surligné en vert
      - Table de transition formatée (ASCII + HTML)
    """

    # Color scheme (dark theme)
    COLORS = {
        "active":    "#22c55e",   # green — current state
        "initial":   "#3b82f6",   # blue — initial state
        "final":     "#f59e0b",   # amber — final state
        "normal":    "#64748b",   # slate — normal state
        "bg":        "#0f172a",   # dark background
        "text":      "#f8fafc",   # white text
        "edge":      "#94a3b8",   # edge color
    }

    EVENT_COLORS = [
        "#60a5fa", "#f472b6", "#34d399", "#fbbf24",
        "#a78bfa", "#fb923c", "#38bdf8", "#e879f9",
    ]

    @staticmethod
    def render_dot(automata, highlight_state=None) -> str:
        """Generate Graphviz DOT code for an automata with professional styling"""
        return automata.to_graphviz_dot(highlight_state)

    @classmethod
    def export_diagram(
        cls,
        automata,
        output_path: str,
        fmt: str = "png",
        highlight_state=None,
    ) -> Optional[str]:
        """
        Export automata diagram to file.
        
        Args:
            automata: AutomataBase instance
            output_path: Base path (without extension)
            fmt: Format — 'png', 'svg', or 'pdf'
            highlight_state: State to highlight (default: current)
            
        Returns:
            Path to generated file, or None if Graphviz not available
        """
        if not HAS_GRAPHVIZ:
            logger.error("Cannot export: graphviz not installed")
            return None

        dot_source = automata.to_graphviz_dot(highlight_state)

        try:
            src = gv.Source(dot_source)
            # graphviz.Source.render returns path with extension
            rendered = src.render(
                filename=output_path,
                format=fmt,
                cleanup=True,  # remove .dot temp file
            )
            logger.info(f"✅ Diagram exported: {rendered}")
            return rendered
        except Exception as e:
            logger.error(f"Export error: {e}")
            return None

    @staticmethod
    def transition_table_ascii(automata) -> str:
        """
        Generate ASCII transition table (for terminal/report output).
        
        Format:
          ┌──────────────────┬───────────┬──────────┐
          │ État             │ event1    │ event2   │
          ├──────────────────┼───────────┼──────────┤
          │ → *Inactif       │ Actif     │ ∅        │
          └──────────────────┴───────────┴──────────┘
        """
        table = automata.get_transition_table()
        if not table:
            return "(table vide)"

        # Get all column keys
        headers = list(table[0].keys())
        
        # Calculate column widths
        widths = {}
        for h in headers:
            widths[h] = max(len(h), max(len(str(row.get(h, ""))) for row in table))
        
        # Build table
        lines = []
        
        # Top border
        top = "┌" + "┬".join("─" * (widths[h] + 2) for h in headers) + "┐"
        lines.append(top)
        
        # Header
        hdr = "│" + "│".join(f" {h:<{widths[h]}} " for h in headers) + "│"
        lines.append(hdr)
        
        # Separator
        sep = "├" + "┼".join("─" * (widths[h] + 2) for h in headers) + "┤"
        lines.append(sep)
        
        # Rows
        for row in table:
            r = "│" + "│".join(f" {str(row.get(h, '')):<{widths[h]}} " for h in headers) + "│"
            lines.append(r)
        
        # Bottom border
        bot = "└" + "┴".join("─" * (widths[h] + 2) for h in headers) + "┘"
        lines.append(bot)
        
        return "\n".join(lines)

    @staticmethod
    def transition_table_html(automata) -> str:
        """Generate HTML transition table for Streamlit dashboard"""
        table = automata.get_transition_table()
        if not table:
            return "<p>Table vide</p>"

        headers = list(table[0].keys())

        html = ['<table style="width:100%; border-collapse:collapse; font-family:Inter,sans-serif; font-size:0.9rem;">']
        
        # Header row
        html.append('<tr>')
        for h in headers:
            html.append(
                f'<th style="background:#1e293b; color:#f8fafc; padding:8px 12px; '
                f'border:1px solid #334155; text-align:left;">{h}</th>'
            )
        html.append('</tr>')
        
        # Data rows
        for i, row in enumerate(table):
            bg = "#0f172a" if i % 2 == 0 else "#1e293b"
            html.append('<tr>')
            for h in headers:
                val = str(row.get(h, ""))
                # Color ∅ cells differently
                color = "#ef4444" if val == "∅" else "#f8fafc"
                # Highlight initial/final markers
                if "→" in val:
                    val = val.replace("→", '<span style="color:#3b82f6;">→</span>')
                if "*" in val:
                    val = val.replace("*", '<span style="color:#f59e0b;">★</span>')
                
                html.append(
                    f'<td style="background:{bg}; color:{color}; padding:6px 12px; '
                    f'border:1px solid #334155;">{val}</td>'
                )
            html.append('</tr>')
        
        html.append('</table>')
        return "\n".join(html)

    @staticmethod
    def format_formal_definition(automata) -> str:
        """Format the formal definition A = (Q, Σ, δ, q₀, F) as a readable string"""
        fd = automata.get_formal_definition()
        lines = [
            f"Automate: {fd['name']}",
            f"",
            f"A = (Q, Σ, δ, q₀, F) où:",
            f"  Q  = {{{', '.join(fd['Q'])}}}",
            f"  Σ  = {{{', '.join(fd['Sigma'])}}}",
            f"  q₀ = {fd['q0']}",
            f"  F  = {{{', '.join(fd['F'])}}}",
            f"",
            f"  δ (fonction de transition):",
        ]
        for state, transitions in fd["delta"].items():
            for event, target in transitions.items():
                lines.append(f"    δ({state}, {event}) = {target}")

        return "\n".join(lines)
