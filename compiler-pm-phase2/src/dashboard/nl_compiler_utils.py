import os
import json
from pathlib import Path
import pandas as pd


def examples_list():
    return [
        "Show me the 5 most polluted zones",
        "Count sensors by type in each zone",
        "List recent interventions with assigned technicians",
        "Average measurement value for sensor X in last 7 days"
    ]


def validate_sql_is_safe(sql: str) -> (bool, str):
    # Very simple validator: only allow SELECT queries
    if not sql or not isinstance(sql, str):
        return False, "Empty SQL"
    s = sql.strip().lower()
    forbidden = ["insert ", "update ", "delete ", "drop ", "create ", "alter ", "truncate ", "grant "]
    for f in forbidden:
        if f in s:
            return False, f"Forbidden statement detected: {f.strip()}"
    if not s.startswith("select"):
        return False, "Only SELECT queries are allowed in sandbox"
    return True, "OK"


def ensure_data_dir():
    p = Path("data")
    p.mkdir(parents=True, exist_ok=True)
    return p


def save_query_history(nl_text: str, sql_text: str, filename: str = "data/nl_history.json"):
    ensure_data_dir()
    entry = {"nl": nl_text, "sql": sql_text}
    data = []
    if os.path.exists(filename):
        try:
            with open(filename, 'r', encoding='utf-8') as fh:
                data = json.load(fh)
        except Exception:
            data = []
    data.append(entry)
    with open(filename, 'w', encoding='utf-8') as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)


def load_query_history(filename: str = "data/nl_history.json"):
    if not os.path.exists(filename):
        return []
    try:
        with open(filename, 'r', encoding='utf-8') as fh:
            return json.load(fh)
    except Exception:
        return []
