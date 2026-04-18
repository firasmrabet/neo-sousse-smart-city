import os
import csv
from pathlib import Path
import pandas as pd


def get_automata_definitions():
    # Simple declarative automata definitions
    return {
        "Sensor Cycle": {
            "states": ["ACTIVE", "SIGNALED", "OUT_OF_SERVICE", "MAINTENANCE"],
            "transitions": {
                "anomaly_detected": ("ACTIVE", "SIGNALED"),
                "breakdown": ("ACTIVE", "OUT_OF_SERVICE"),
                "maintenance_start": ("OUT_OF_SERVICE", "MAINTENANCE"),
                "maintenance_complete": ("MAINTENANCE", "ACTIVE")
            }
        },
        "Intervention Validation": {
            "states": ["PENDING", "IN_PROGRESS", "COMPLETED", "REJECTED"],
            "transitions": {
                "assign": ("PENDING", "IN_PROGRESS"),
                "complete": ("IN_PROGRESS", "COMPLETED"),
                "reject": ("PENDING", "REJECTED")
            }
        }
    }


def render_graphviz_dot(defn, highlight_state=None):
    # Build a DOT string to display via Streamlit's graphviz_chart
    states = defn.get("states", [])
    transitions = defn.get("transitions", {})

    lines = ["digraph G {", "rankdir=LR;", "node [shape = circle, style=filled, fillcolor=gray20, fontcolor=white];"]

    for s in states:
        if s == highlight_state:
            lines.append(f'"{s}" [style=filled, fillcolor=darkorange, fontcolor=black];')
        else:
            lines.append(f'"{s}";')

    for evt, (src, dst) in transitions.items():
        lines.append(f'"{src}" -> "{dst}" [ label = "{evt}" ];')

    lines.append("}")
    return "\n".join(lines)


def simulate_step(defn, current_state, event):
    transitions = defn.get("transitions", {})
    if event in transitions:
        src, dst = transitions[event]
        if src == current_state:
            return dst, f"{current_state} --{event}--> {dst}"
        else:
            return current_state, f"Event '{event}' not valid from state {current_state} (expected {src})"
    else:
        return current_state, f"Unknown event '{event}'"


def ensure_data_dir():
    p = Path("data")
    p.mkdir(parents=True, exist_ok=True)
    return p


def append_history_row(row: dict, filename: str = "data/automata_history.csv"):
    ensure_data_dir()
    file_exists = os.path.exists(filename)
    keys = list(row.keys())
    with open(filename, "a", newline='', encoding='utf-8') as fh:
        writer = csv.DictWriter(fh, fieldnames=keys)
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)


def load_history(filename: str = "data/automata_history.csv"):
    if not os.path.exists(filename):
        return pd.DataFrame()
    return pd.read_csv(filename)


def run_scenario(defn, start_state, events_list):
    log = []
    state = start_state
    for ev in events_list:
        state, msg = simulate_step(defn, state, ev.strip())
        log.append({"event": ev.strip(), "state": state, "message": msg})
    return state, log
