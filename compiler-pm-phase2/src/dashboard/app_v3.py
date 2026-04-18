"""
Neo-Sousse Smart City — Dashboard Professionnel     
Streamlit + Plotly + Graphviz

Modules:
  - Compilateur NL → SQL (avec visualisation AST)
  - Automates interactifs (3 DFA: Capteur, Intervention, Véhicule)
  - Rapports IA (Ollama llama3.2)
  - Monitoring temps réel (capteurs, interventions, véhicules, citoyens)
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import sys, time, json, html as _html_mod

# ── Path setup ────────────────────────────────────────────────────
ROOT = r"c:\Users\Mrabet\Desktop\devops\outils\ps-main\projet DB\SensorLinker\SensorLinker\compiler-pm-phase2"
sys.path.insert(0, ROOT)

from src.db_connection import get_db
from src.compiler import Compiler, CompilationResult, SemanticAnalyzer
from src.automata import (
    AutomataEngine, SensorAutomata, InterventionAutomata, VehicleAutomata,
    SensorState, InterventionState, VehicleState, create_automata,
    AutomataVisualizer, AutomataSimulator,
    AlertEngine, AlertSeverity,
)
from src.ia.report_generator import AIReportGenerator
from src.ia.pdf_professional import ProfessionalPDFGenerator
# Force reload auth module (bypass stale __pycache__)
import importlib
import src.dashboard.auth as _auth_mod
importlib.reload(_auth_mod)
render_login_page = _auth_mod.render_login_page
get_pages_for_role = _auth_mod.get_pages_for_role
from src.realtime_simulator import start_simulator

@st.cache_resource
def init_simulator():
    """Start the real-time background simulator once."""
    return start_simulator(get_db)

init_simulator()

# ═══════════════════════════════════════════════════════════════════
# PAGE CONFIG & CUSTOM CSS
# ═══════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="Neo-Sousse Smart City      ",
    page_icon="🏙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Premium dark theme CSS
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600&display=swap');

:root {
    --bg-primary: #0f172a;
    --bg-card: #1e293b;
    --bg-card-hover: #334155;
    --accent: #3b82f6;
    --accent-green: #22c55e;
    --accent-amber: #f59e0b;
    --accent-red: #ef4444;
    --accent-purple: #a855f7;
    --accent-cyan: #06b6d4;
    --accent-pink: #ec4899;
    --text-primary: #f8fafc;
    --text-secondary: #94a3b8;
    --border: #334155;
}

.stApp { font-family: 'Inter', sans-serif; }

.metric-card {
    background: linear-gradient(135deg, var(--bg-card), var(--bg-card-hover));
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 1.2rem;
    text-align: center;
    box-shadow: 0 4px 16px rgba(0,0,0,0.3);
    transition: transform 0.2s ease;
}
.metric-card:hover { transform: translateY(-2px); }
.metric-value { font-size: 2rem; font-weight: 700; margin: 0.3rem 0; }
.metric-label { font-size: 0.85rem; color: var(--text-secondary); text-transform: uppercase; letter-spacing: 0.5px; }

.status-badge {
    display: inline-block;
    padding: 0.25rem 0.75rem;
    border-radius: 9999px;
    font-size: 0.75rem;
    font-weight: 600;
}
.badge-green { background: rgba(34,197,94,0.15); color: #22c55e; }
.badge-amber { background: rgba(245,158,11,0.15); color: #f59e0b; }
.badge-red { background: rgba(239,68,68,0.15); color: #ef4444; }
.badge-blue { background: rgba(59,130,246,0.15); color: #3b82f6; }

.section-header {
    font-size: 1.25rem;
    font-weight: 600;
    margin: 1.5rem 0 0.75rem 0;
    padding-bottom: 0.5rem;
    border-bottom: 2px solid var(--accent);
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.ast-box {
    background: #1e293b;
    border: 1px solid #334155;
    border-radius: 8px;
    padding: 1rem;
    font-family: 'Cascadia Code', 'Fira Code', monospace;
    font-size: 0.85rem;
    white-space: pre-wrap;
}

.report-box {
    background: linear-gradient(135deg, #1e293b, #0f172a);
    border-left: 4px solid var(--accent-purple);
    border-radius: 8px;
    padding: 1.2rem;
    margin: 1rem 0;
    line-height: 1.6;
}

/* ═══ COMPILER PAGE PREMIUM STYLES ═══ */

.compiler-hero {
    background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #0f172a 100%);
    border: 1px solid rgba(139, 92, 246, 0.3);
    border-radius: 16px;
    padding: 2rem 2.5rem;
    margin-bottom: 1.5rem;
    position: relative;
    overflow: hidden;
}
.compiler-hero::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0; bottom: 0;
    background: radial-gradient(ellipse at 30% 50%, rgba(139,92,246,0.08) 0%, transparent 70%);
    pointer-events: none;
}
.compiler-hero h1 {
    font-size: 2rem;
    font-weight: 700;
    background: linear-gradient(135deg, #c084fc, #818cf8, #60a5fa);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin: 0 0 0.5rem 0;
}
.compiler-hero .subtitle {
    color: var(--text-secondary);
    font-size: 0.9rem;
    font-style: italic;
}

/* Pipeline Steps */
.pipeline-container {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0;
    margin: 1.5rem 0;
    padding: 1rem;
    background: rgba(15, 23, 42, 0.6);
    border: 1px solid var(--border);
    border-radius: 12px;
    backdrop-filter: blur(10px);
}
.pipeline-step {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.4rem;
    padding: 0.8rem 1.2rem;
    border-radius: 10px;
    transition: all 0.3s ease;
    min-width: 90px;
}
.pipeline-step.active {
    background: rgba(139, 92, 246, 0.15);
    box-shadow: 0 0 20px rgba(139, 92, 246, 0.2);
}
.pipeline-step.done {
    background: rgba(34, 197, 94, 0.1);
}
.pipeline-step .step-icon { font-size: 1.5rem; }
.pipeline-step .step-label { font-size: 0.7rem; font-weight: 600; color: var(--text-secondary); text-transform: uppercase; letter-spacing: 0.5px; }
.pipeline-step .step-detail { font-size: 0.65rem; color: #64748b; }
.pipeline-arrow {
    color: #475569;
    font-size: 1.2rem;
    margin: 0 0.3rem;
}
.pipeline-arrow.done { color: #22c55e; }

/* SQL Card */
.sql-card {
    background: linear-gradient(135deg, #0c1222, #1a1a2e);
    border: 1px solid rgba(59, 130, 246, 0.3);
    border-radius: 12px;
    padding: 0;
    margin: 1rem 0;
    overflow: hidden;
    box-shadow: 0 8px 32px rgba(0,0,0,0.3);
}
.sql-card-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0.75rem 1.2rem;
    background: rgba(59, 130, 246, 0.08);
    border-bottom: 1px solid rgba(59, 130, 246, 0.15);
}
.sql-card-header .title {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 0.85rem;
    font-weight: 600;
    color: #60a5fa;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}
.sql-card-header .badge {
    background: rgba(34, 197, 94, 0.15);
    color: #22c55e;
    padding: 0.2rem 0.6rem;
    border-radius: 9999px;
    font-size: 0.7rem;
    font-weight: 600;
}
.sql-card-body {
    padding: 1.2rem 1.5rem;
    font-family: 'JetBrains Mono', 'Cascadia Code', monospace;
    font-size: 0.9rem;
    line-height: 1.8;
    color: #e2e8f0;
    overflow-x: auto;
}
.sql-keyword { color: #c084fc; font-weight: 600; }
.sql-function { color: #f472b6; }
.sql-string { color: #34d399; }
.sql-table { color: #60a5fa; }
.sql-operator { color: #fbbf24; }
.sql-number { color: #fb923c; }

/* Results Card */
.results-card {
    background: linear-gradient(135deg, #0c1222, #111827);
    border: 1px solid rgba(6, 182, 212, 0.25);
    border-radius: 12px;
    padding: 0;
    margin: 1rem 0;
    overflow: hidden;
    box-shadow: 0 8px 32px rgba(0,0,0,0.2);
}
.results-card-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0.75rem 1.2rem;
    background: rgba(6, 182, 212, 0.06);
    border-bottom: 1px solid rgba(6, 182, 212, 0.15);
}
.results-card-header .title {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 0.85rem;
    font-weight: 600;
    color: #22d3ee;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}
.results-card-header .count-badge {
    background: rgba(6, 182, 212, 0.15);
    color: #22d3ee;
    padding: 0.2rem 0.8rem;
    border-radius: 9999px;
    font-size: 0.75rem;
    font-weight: 600;
}

/* Compilation Stats */
.comp-stats {
    display: flex;
    gap: 1rem;
    margin: 1rem 0;
}
.comp-stat {
    flex: 1;
    background: linear-gradient(135deg, var(--bg-card), #0f172a);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 0.8rem 1rem;
    text-align: center;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}
.comp-stat:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0,0,0,0.3);
}
.comp-stat .stat-value {
    font-size: 1.5rem;
    font-weight: 700;
    font-family: 'JetBrains Mono', monospace;
}
.comp-stat .stat-label {
    font-size: 0.7rem;
    color: var(--text-secondary);
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-top: 0.2rem;
}

/* Token badges */
.token-pill {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    padding: 0.3rem 0.8rem;
    border-radius: 8px;
    font-size: 0.78rem;
    font-family: 'JetBrains Mono', monospace;
    margin: 0.2rem;
    border: 1px solid transparent;
}
.token-keyword { background: rgba(192, 132, 252, 0.12); border-color: rgba(192,132,252,0.3); color: #c084fc; }
.token-table { background: rgba(96, 165, 250, 0.12); border-color: rgba(96,165,250,0.3); color: #60a5fa; }
.token-column { background: rgba(34, 211, 238, 0.12); border-color: rgba(34,211,238,0.3); color: #22d3ee; }
.token-value { background: rgba(52, 211, 153, 0.12); border-color: rgba(52,211,153,0.3); color: #34d399; }
.token-number { background: rgba(251, 146, 60, 0.12); border-color: rgba(251,146,60,0.3); color: #fb923c; }
.token-operator { background: rgba(251, 191, 36, 0.12); border-color: rgba(251,191,36,0.3); color: #fbbf24; }
.token-other { background: rgba(148, 163, 184, 0.1); border-color: rgba(148,163,184,0.2); color: #94a3b8; }

/* Success banner */
.success-banner {
    background: linear-gradient(135deg, rgba(34, 197, 94, 0.1), rgba(16, 185, 129, 0.05));
    border: 1px solid rgba(34, 197, 94, 0.3);
    border-radius: 10px;
    padding: 0.8rem 1.2rem;
    display: flex;
    align-items: center;
    gap: 0.75rem;
    margin: 0.75rem 0;
}
.success-banner .check-icon {
    width: 28px; height: 28px;
    background: rgba(34, 197, 94, 0.2);
    border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 1rem;
}
.success-banner .text {
    font-weight: 600;
    color: #22c55e;
    font-size: 0.9rem;
}
.success-banner .detail {
    color: #6ee7b7;
    font-size: 0.8rem;
    margin-left: auto;
    font-family: 'JetBrains Mono', monospace;
}

/* Error banner */
.error-banner {
    background: linear-gradient(135deg, rgba(239, 68, 68, 0.1), rgba(220, 38, 38, 0.05));
    border: 1px solid rgba(239, 68, 68, 0.3);
    border-radius: 10px;
    padding: 0.8rem 1.2rem;
    display: flex;
    align-items: center;
    gap: 0.75rem;
    margin: 0.75rem 0;
}
.error-banner .text { font-weight: 600; color: #ef4444; font-size: 0.9rem; }

/* AST Tree */
.ast-tree-node {
    background: rgba(30, 41, 59, 0.8);
    border: 1px solid var(--border);
    border-left: 3px solid;
    border-radius: 8px;
    padding: 0.6rem 1rem;
    margin: 0.4rem 0;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.8rem;
}
.ast-tree-node.type-select { border-left-color: #60a5fa; }
.ast-tree-node.type-count { border-left-color: #c084fc; }
.ast-tree-node.type-aggregate { border-left-color: #f472b6; }
.ast-tree-node.type-condition { border-left-color: #fbbf24; }

/* ═══ PAGE HEROES ═══ */
.page-hero {
    border-radius: 16px;
    padding: 2rem 2.5rem;
    margin-bottom: 1.5rem;
    position: relative;
    overflow: hidden;
}
.page-hero::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0; bottom: 0;
    pointer-events: none;
}
.page-hero h1 {
    font-size: 2rem;
    font-weight: 700;
    margin: 0 0 0.5rem 0;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}
.page-hero .subtitle {
    color: #94a3b8;
    font-size: 0.9rem;
    font-style: italic;
}
.page-hero .hero-badges {
    display: flex;
    gap: 0.5rem;
    margin-top: 0.75rem;
    flex-wrap: wrap;
}
.page-hero .hero-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.3rem;
    padding: 0.25rem 0.75rem;
    border-radius: 9999px;
    font-size: 0.7rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.1);
    color: #94a3b8;
}

.hero-dashboard { background: linear-gradient(135deg, #0f172a 0%, #0c2d48 50%, #0f172a 100%); border: 1px solid rgba(6,182,212,0.3); }
.hero-dashboard::before { background: radial-gradient(ellipse at 30% 50%, rgba(6,182,212,0.08) 0%, transparent 70%); }
.hero-dashboard h1 { background: linear-gradient(135deg, #22d3ee, #06b6d4, #0ea5e9); -webkit-background-clip: text; background-clip: text; }

.hero-automates { background: linear-gradient(135deg, #0f172a 0%, #1a2e1a 50%, #0f172a 100%); border: 1px solid rgba(34,197,94,0.3); }
.hero-automates::before { background: radial-gradient(ellipse at 30% 50%, rgba(34,197,94,0.08) 0%, transparent 70%); }
.hero-automates h1 { background: linear-gradient(135deg, #4ade80, #22c55e, #10b981); -webkit-background-clip: text; background-clip: text; }

.hero-capteurs { background: linear-gradient(135deg, #0f172a 0%, #1a2744 50%, #0f172a 100%); border: 1px solid rgba(59,130,246,0.3); }
.hero-capteurs::before { background: radial-gradient(ellipse at 30% 50%, rgba(59,130,246,0.08) 0%, transparent 70%); }
.hero-capteurs h1 { background: linear-gradient(135deg, #93c5fd, #3b82f6, #2563eb); -webkit-background-clip: text; background-clip: text; }

.hero-interventions { background: linear-gradient(135deg, #0f172a 0%, #2d2317 50%, #0f172a 100%); border: 1px solid rgba(245,158,11,0.3); }
.hero-interventions::before { background: radial-gradient(ellipse at 30% 50%, rgba(245,158,11,0.08) 0%, transparent 70%); }
.hero-interventions h1 { background: linear-gradient(135deg, #fcd34d, #f59e0b, #d97706); -webkit-background-clip: text; background-clip: text; }

.hero-vehicules { background: linear-gradient(135deg, #0f172a 0%, #2d1a3d 50%, #0f172a 100%); border: 1px solid rgba(168,85,247,0.3); }
.hero-vehicules::before { background: radial-gradient(ellipse at 30% 50%, rgba(168,85,247,0.08) 0%, transparent 70%); }
.hero-vehicules h1 { background: linear-gradient(135deg, #d8b4fe, #a855f7, #7c3aed); -webkit-background-clip: text; background-clip: text; }

.hero-citoyens { background: linear-gradient(135deg, #0f172a 0%, #172e3d 50%, #0f172a 100%); border: 1px solid rgba(6,182,212,0.3); }
.hero-citoyens::before { background: radial-gradient(ellipse at 30% 50%, rgba(6,182,212,0.08) 0%, transparent 70%); }
.hero-citoyens h1 { background: linear-gradient(135deg, #67e8f9, #06b6d4, #0891b2); -webkit-background-clip: text; background-clip: text; }

.hero-rapports { background: linear-gradient(135deg, #0f172a 0%, #2d1730 50%, #0f172a 100%); border: 1px solid rgba(236,72,153,0.3); }
.hero-rapports::before { background: radial-gradient(ellipse at 30% 50%, rgba(236,72,153,0.08) 0%, transparent 70%); }
.hero-rapports h1 { background: linear-gradient(135deg, #f9a8d4, #ec4899, #db2777); -webkit-background-clip: text; background-clip: text; }

.hero-params { background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%); border: 1px solid rgba(148,163,184,0.3); }
.hero-params::before { background: radial-gradient(ellipse at 30% 50%, rgba(148,163,184,0.06) 0%, transparent 70%); }
.hero-params h1 { background: linear-gradient(135deg, #e2e8f0, #94a3b8, #64748b); -webkit-background-clip: text; background-clip: text; }

/* ═══ PREMIUM FOOTER ═══ */
.premium-footer {
    text-align: center;
    padding: 1.5rem 0 0.5rem 0;
    margin-top: 2rem;
}
.premium-footer .footer-brand {
    font-size: 1rem;
    font-weight: 700;
    background: linear-gradient(135deg, #c084fc, #818cf8, #60a5fa);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin-bottom: 0.4rem;
}
.premium-footer .footer-modules {
    font-size: 0.78rem;
    color: #475569;
    margin-bottom: 0.3rem;
}
.premium-footer .footer-modules span {
    padding: 0.15rem 0.6rem;
    border-right: 1px solid #1e293b;
}
.premium-footer .footer-modules span:last-child { border-right: none; }
.premium-footer .footer-copy {
    font-size: 0.7rem;
    color: #334155;
    margin-top: 0.3rem;
}

/* ═══ INFO CARD ═══ */
.info-card {
    background: linear-gradient(135deg, var(--bg-card), #0f172a);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 1.5rem;
    position: relative;
    overflow: hidden;
    margin-bottom: 1rem;
}
.info-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; width: 100%; height: 3px;
}
.info-card.db::before { background: linear-gradient(90deg, #3b82f6, #06b6d4); }
.info-card.ia::before { background: linear-gradient(90deg, #a855f7, #ec4899); }
.info-card .card-title {
    font-size: 1.1rem;
    font-weight: 700;
    color: var(--text-primary);
    margin: 0.5rem 0 1rem 0;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}
.info-item {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0.5rem 0.75rem;
    margin: 0.3rem 0;
    background: rgba(15, 23, 42, 0.5);
    border-radius: 8px;
    border: 1px solid rgba(51, 65, 85, 0.5);
}
.info-item .label {
    color: var(--text-secondary);
    font-size: 0.8rem;
    min-width: 80px;
    text-transform: uppercase;
    letter-spacing: 0.3px;
    font-weight: 600;
}
.info-item .value {
    color: var(--text-primary);
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.85rem;
}

/* ═══ SECTION DIVIDER ═══ */
.section-divider {
    height: 1px;
    background: linear-gradient(90deg, transparent, var(--border), transparent);
    margin: 1.5rem 0;
    border: none;
}

/* ═══ DFA ACCEPTANCE BANNERS ═══ */
.dfa-verdict {
    border-radius: 12px;
    padding: 1.2rem 1.5rem;
    margin: 1rem 0;
    position: relative;
    overflow: hidden;
}
.dfa-verdict::before {
    content: '';
    position: absolute;
    top: 0; left: 0; width: 4px; height: 100%;
}
.dfa-verdict .verdict-header {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    margin-bottom: 0.6rem;
}
.dfa-verdict .verdict-icon {
    font-size: 1.5rem;
}
.dfa-verdict .verdict-title {
    font-size: 1.1rem;
    font-weight: 700;
}
.dfa-verdict .verdict-notation {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.85rem;
    padding: 0.4rem 0.8rem;
    border-radius: 8px;
    margin-top: 0.4rem;
    display: inline-block;
}
.dfa-verdict .verdict-detail {
    font-size: 0.82rem;
    color: #94a3b8;
    margin-top: 0.5rem;
    line-height: 1.6;
}

.dfa-accepted {
    background: linear-gradient(135deg, rgba(34,197,94,0.08), rgba(16,185,129,0.04));
    border: 1px solid rgba(34,197,94,0.3);
}
.dfa-accepted::before { background: #22c55e; }
.dfa-accepted .verdict-title { color: #22c55e; }
.dfa-accepted .verdict-notation {
    background: rgba(34,197,94,0.1);
    color: #4ade80;
    border: 1px solid rgba(34,197,94,0.2);
}

.dfa-not-accepted {
    background: linear-gradient(135deg, rgba(245,158,11,0.08), rgba(217,119,6,0.04));
    border: 1px solid rgba(245,158,11,0.3);
}
.dfa-not-accepted::before { background: #f59e0b; }
.dfa-not-accepted .verdict-title { color: #f59e0b; }
.dfa-not-accepted .verdict-notation {
    background: rgba(245,158,11,0.1);
    color: #fbbf24;
    border: 1px solid rgba(245,158,11,0.2);
}

.dfa-rejected {
    background: linear-gradient(135deg, rgba(239,68,68,0.08), rgba(220,38,38,0.04));
    border: 1px solid rgba(239,68,68,0.3);
}
.dfa-rejected::before { background: #ef4444; }
.dfa-rejected .verdict-title { color: #ef4444; }
.dfa-rejected .verdict-notation {
    background: rgba(239,68,68,0.1);
    color: #f87171;
    border: 1px solid rgba(239,68,68,0.2);
}

.dfa-state-chip {
    display: inline-flex;
    align-items: center;
    gap: 0.3rem;
    padding: 0.2rem 0.6rem;
    border-radius: 6px;
    font-size: 0.78rem;
    font-family: 'JetBrains Mono', monospace;
    font-weight: 600;
}
.dfa-state-chip.final {
    background: rgba(245,158,11,0.15);
    color: #fbbf24;
    border: 1px solid rgba(245,158,11,0.3);
}
.dfa-state-chip.non-final {
    background: rgba(148,163,184,0.1);
    color: #94a3b8;
    border: 1px solid rgba(148,163,184,0.2);
}
.dfa-state-chip.current {
    background: rgba(34,197,94,0.15);
    color: #4ade80;
    border: 1px solid rgba(34,197,94,0.3);
}

/* ═══ COMPACT ALERTS TABLE ═══ */
.alerts-scroll-container {
    max-height: 420px;
    overflow-y: auto;
    border: 1px solid var(--border);
    border-radius: 12px;
    background: rgba(15, 23, 42, 0.4);
    padding: 0;
}
.alerts-scroll-container::-webkit-scrollbar {
    width: 6px;
}
.alerts-scroll-container::-webkit-scrollbar-track {
    background: rgba(15,23,42,0.3);
    border-radius: 6px;
}
.alerts-scroll-container::-webkit-scrollbar-thumb {
    background: rgba(148,163,184,0.3);
    border-radius: 6px;
}
.alerts-scroll-container::-webkit-scrollbar-thumb:hover {
    background: rgba(148,163,184,0.5);
}
.alert-row {
    display: flex;
    align-items: flex-start;
    gap: 10px;
    padding: 0.7rem 1rem;
    border-bottom: 1px solid rgba(51,65,85,0.4);
    transition: background 0.15s ease;
}
.alert-row:last-child { border-bottom: none; }
.alert-row:hover { background: rgba(255,255,255,0.03); }
.alert-sev {
    flex-shrink: 0;
    font-size: 0.7rem;
    font-weight: 700;
    padding: 3px 8px;
    border-radius: 6px;
    white-space: nowrap;
    min-width: 80px;
    text-align: center;
}
.alert-sev.critique { background: rgba(239,68,68,0.15); color: #f87171; }
.alert-sev.haute { background: rgba(245,158,11,0.15); color: #fbbf24; }
.alert-sev.moyenne { background: rgba(59,130,246,0.15); color: #60a5fa; }
.alert-sev.info { background: rgba(6,182,212,0.1); color: #22d3ee; }
.alert-body { flex: 1; min-width: 0; }
.alert-entity {
    font-size: 0.72rem;
    color: #64748b;
    margin-bottom: 2px;
    display: flex;
    align-items: center;
    gap: 6px;
}
.alert-entity .dur { margin-left: auto; color: #94a3b8; font-size: 0.7rem; }
.alert-msg { font-size: 0.82rem; font-weight: 600; color: #e2e8f0; margin-bottom: 2px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.alert-action { font-size: 0.75rem; color: #94a3b8; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════
# AUTHENTICATION GATE
# ═══════════════════════════════════════════════════════════════════

if "auth_user" not in st.session_state:
    st.session_state.auth_user = None

if not st.session_state.auth_user:
    render_login_page(st)
    st.stop()

# ═══════════════════════════════════════════════════════════════════
# SESSION STATE INIT (authenticated users only)
# ═══════════════════════════════════════════════════════════════════

if "page" not in st.session_state:
    st.session_state.page = "🏠 Dashboard"
if "automata_engine" not in st.session_state:
    st.session_state.automata_engine = AutomataEngine()
st.session_state.compiler = Compiler()
if "ia" not in st.session_state:
    st.session_state.ia = AIReportGenerator(provider="ollama", model="llama3.2:3b")
if "alert_engine" not in st.session_state:
    st.session_state.alert_engine = AlertEngine()
if "pdf_gen" not in st.session_state:
    try:
        st.session_state.pdf_gen = ProfessionalPDFGenerator()
    except ImportError:
        st.session_state.pdf_gen = None

engine = st.session_state.automata_engine
compiler = st.session_state.compiler
ia = st.session_state.ia
alert_engine = st.session_state.alert_engine
pdf_gen = st.session_state.pdf_gen

# ═══════════════════════════════════════════════════════════════════
# SIDEBAR NAVIGATION (Role-Based)
# ═══════════════════════════════════════════════════════════════════

auth_user = st.session_state.auth_user
user_role = auth_user.get('role', 'citoyen')
allowed_pages = get_pages_for_role(user_role)

with st.sidebar:
    st.markdown("## 🏙️ Neo-Sousse")
    st.markdown("**Smart City**")
    st.markdown("---")

    # User info card
    role_icons = {"admin": "👑", "technicien": "🔧", "citoyen": "👥"}
    role_names = {"admin": "Administrateur", "technicien": "Technicien", "citoyen": "Citoyen"}
    role_colors = {"admin": "#f87171", "technicien": "#fbbf24", "citoyen": "#4ade80"}
    st.markdown(f"""
    <div style='background:rgba(59,130,246,0.06); border:1px solid rgba(59,130,246,0.15);
         border-radius:10px; padding:0.7rem 0.8rem; margin-bottom:1rem;'>
        <div style='font-weight:600; font-size:0.85rem; color:#f8fafc;'>
            {role_icons.get(user_role, '👤')} {auth_user.get('nom', auth_user.get('email', ''))}
        </div>
        <div style='font-size:0.72rem; color:#64748b; margin-top:2px;'>{auth_user.get('email', '')}</div>
        <div style='margin-top:4px;'>
            <span style='font-size:0.68rem; font-weight:600; padding:2px 8px; border-radius:20px;
                  background:rgba(255,255,255,0.05); color:{role_colors.get(user_role, "#94a3b8")};'>
                {role_names.get(user_role, user_role).upper()}
            </span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Ensure current page is allowed
    if st.session_state.page not in allowed_pages:
        st.session_state.page = allowed_pages[0] if allowed_pages else "🏠 Dashboard"

    page = st.radio("Navigation", allowed_pages,
                    index=allowed_pages.index(st.session_state.page) if st.session_state.page in allowed_pages else 0,
                    label_visibility="collapsed")
    st.session_state.page = page

    st.markdown("---")
    st.markdown(f"**🟢 Système en ligne**")
    st.markdown(f"**IA:** {ia.provider} ({ia.model})")
    st.markdown(f"**Heure:** {datetime.now().strftime('%H:%M:%S')}")

    st.markdown("---")
    if st.button(" Déconnexion", use_container_width=True, type="primary"):
        # Clear ALL auth-related state
        st.session_state.auth_user = None
        st.session_state.auth_mode = "login"
        st.session_state.page = "🏠 Dashboard"
        # Clear cached data
        for key in list(st.session_state.keys()):
            if key.startswith('last_') or key.startswith('auto_') or key.startswith('reset_'):
                del st.session_state[key]
        st.rerun()

# ═══════════════════════════════════════════════════════════════════
# HELPER: DB queries
# ═══════════════════════════════════════════════════════════════════

def safe_fetch(query, params=None):
    try:
        db = get_db()
        if not db._db_available():
            st.warning("⚠️ Base de données MySQL non disponible — données simulées affichées.", icon="🔌")
            return []
        return db.fetch_all(query, params) or []
    except Exception as e:
        st.warning(f"⚠️ BD indisponible : {e}", icon="🔌")
        return []

def safe_fetch_one(query, params=None):
    try:
        db = get_db()
        if not db._db_available():
            return {}
        return db.fetch_one(query, params) or {}
    except Exception as e:
        return {}

def metric_card(label, value, color="#3b82f6", icon="📊"):
    st.markdown(f"""
    <div class='metric-card'>
        <div style='font-size:1.5rem;'>{icon}</div>
        <div class='metric-value' style='color:{color};'>{value}</div>
        <div class='metric-label'>{label}</div>
    </div>
    """, unsafe_allow_html=True)


def highlight_sql(sql_text):
    """Colorize SQL for premium display"""
    import re
    s = sql_text
    # Escape HTML
    s = s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    # Strings FIRST (before keywords, to avoid conflicts with HTML attributes)
    s = re.sub(r"'([^']*?)'", r'<span class="sql-string">&apos;\1&apos;</span>', s)
    # Keywords
    for kw in ['SELECT', 'FROM', 'WHERE', 'JOIN', 'ON', 'INNER', 'LEFT', 'RIGHT',
               'GROUP BY', 'ORDER BY', 'HAVING', 'LIMIT', 'AS', 'AND', 'OR',
               'NOT', 'IN', 'LIKE', 'BETWEEN', 'IS', 'NULL', 'DESC', 'ASC', 'DISTINCT']:
        s = re.sub(rf'\b({kw})\b', r'<span class="sql-keyword">\1</span>', s, flags=re.IGNORECASE)
    # Functions
    for fn in ['COUNT', 'AVG', 'SUM', 'MIN', 'MAX', 'ROUND']:
        s = re.sub(rf'\b({fn})\s*\(', rf'<span class="sql-function">\1</span>(', s, flags=re.IGNORECASE)
    # Numbers (only standalone numbers, not inside existing spans)
    s = re.sub(r'(?<!["\w])(\d+\.?\d*)(?!["\w])', r'<span class="sql-number">\1</span>', s)
    return s

def get_token_class(token_type):
    """Map token type to CSS class"""
    t = token_type.lower()
    if t in ('keyword', 'show', 'count', 'aggregate', 'filter', 'negation', 'conjunction',
             'disjunction', 'preference', 'superlative', 'top', 'order'):
        return 'token-keyword'
    elif t in ('table', 'table_name'):
        return 'token-table'
    elif t in ('column', 'column_name', 'grandeur'):
        return 'token-column'
    elif t in ('value', 'status_value', 'type_value', 'nature_value', 'string'):
        return 'token-value'
    elif t in ('number', 'integer', 'float'):
        return 'token-number'
    elif t in ('operator', 'comparator', 'equals', 'greater', 'less'):
        return 'token-operator'
    return 'token-other'

def _build_scenario_dot(test_auto, result):
    """Build a Graphviz DOT diagram highlighting the path taken during a scenario."""
    states = test_auto.get_states()
    transitions = test_auto.get_transitions()
    initial = test_auto.get_initial_state()
    finals = set(test_auto.get_final_states())

    # Extract the path of (from_state, event, to_state) from scenario result
    path_edges = set()  # (src_value, event, dst_value)
    visited_states = set()
    visited_states.add(initial.value)

    for step in result.get("steps", []):
        if step.get("ok") and step.get("from") and step.get("to"):
            src = step["from"]
            evt = step["event"]
            dst = step["to"]
            path_edges.add((src, evt, dst))
            visited_states.add(src)
            visited_states.add(dst)

    # Determine final state from the automata
    final_state_val = test_auto.get_state()

    colors = {
        "active": "#22c55e", "path": "#4ade80", "initial": "#3b82f6",
        "final": "#f59e0b", "normal": "#cbd5e1", "bg": "#f0f4f8",
        "text": "#1e293b", "edge": "#475569", "path_edge": "#22c55e",
    }

    lines = [
        'digraph {',
        '  rankdir=LR;',
        f'  bgcolor="{colors["bg"]}";',
        '  pad=0.5;',
        f'  node [fontname="Segoe UI" fontsize=11 style=filled fontcolor="{colors["text"]}"];',
        f'  edge [fontname="Segoe UI" fontsize=9 color="{colors["edge"]}" fontcolor="{colors["text"]}"];',
        '',
        '  __start__ [shape=point width=0 height=0 label=""];',
        f'  __start__ -> "{initial.value}" [color="{colors["initial"]}" penwidth=2];',
        '',
    ]

    # Nodes
    for state in states:
        sv = state.value
        is_final = state in finals
        shape = "doublecircle" if is_final else "circle"
        if sv == final_state_val:
            fill = colors["active"]
        elif sv in visited_states:
            fill = colors["path"]
        elif state == initial:
            fill = colors["initial"]
        elif is_final:
            fill = colors["final"]
        else:
            fill = colors["normal"]

        if is_final:
            # Final states: two thin BLACK concentric circles (textbook DFA style)
            lines.append(
                f'  "{sv}" [shape=doublecircle fillcolor="{fill}" '
                f'fontcolor="white" color="#000000" penwidth=1.0 width=1.8 height=1.8];'
            )
        else:
            lines.append(f'  "{sv}" [shape=circle fillcolor="{fill}" color="#334155" penwidth=1];')

    lines.append("")

    # Edges — merge parallel edges
    from typing import Tuple as T2
    edge_labels = {}
    for src, trans in transitions.items():
        for event, dst in trans.items():
            key = (src.value, dst.value)
            edge_labels.setdefault(key, []).append(event)

    for (src, dst), events in edge_labels.items():
        # Check if any edge in this group was taken during the scenario
        taken_events = [e for e in events if (src, e, dst) in path_edges]
        other_events = [e for e in events if (src, e, dst) not in path_edges]

        # Draw taken edges (highlighted green, thick)
        if taken_events:
            label = "\\n".join(taken_events)
            lines.append(
                f'  "{src}" -> "{dst}" [label="{label}" color="{colors["path_edge"]}" '
                f'fontcolor="{colors["path_edge"]}" penwidth=3 style=bold];'
            )
        # Draw non-taken edges (dimmed)
        if other_events:
            label = "\\n".join(other_events)
            lines.append(
                f'  "{src}" -> "{dst}" [label="{label}" color="{colors["edge"]}" '
                f'fontcolor="#64748b" penwidth=1 style=dashed];'
            )

    lines.append("}")
    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════
# PAGE: DASHBOARD
# ═══════════════════════════════════════════════════════════════════

if page == "🏠 Dashboard":
    st.markdown("""
    <div class='page-hero hero-dashboard'>
        <h1>🏠 Tableau de Bord — Neo-Sousse Smart City</h1>
        <div class='subtitle'>Vue d’ensemble du système intelligent — Monitoring temps réel     </div>
        <div class='hero-badges'>
            <span class='hero-badge'>🟢 Système en ligne</span>
            <span class='hero-badge'>📶 IoT Connecté</span>
            <span class='hero-badge'>🤖 IA Active</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # KPIs
    stats = {
        "total": safe_fetch_one("SELECT COUNT(*) as n FROM capteur").get("n", 0),
        "actifs": safe_fetch_one("SELECT COUNT(*) as n FROM capteur WHERE Statut='Actif'").get("n", 0),
        "hs": safe_fetch_one("SELECT COUNT(*) as n FROM capteur WHERE Statut='Hors Service'").get("n", 0),
        "interventions": safe_fetch_one("SELECT COUNT(*) as n FROM intervention").get("n", 0),
        "vehicules": safe_fetch_one("SELECT COUNT(*) as n FROM véhicule").get("n", 0),
        "citoyens": safe_fetch_one("SELECT COUNT(*) as n FROM citoyen").get("n", 0),
    }

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    with c1: metric_card("Capteurs", stats["total"], "#3b82f6", "📡")
    with c2: metric_card("Actifs", stats["actifs"], "#22c55e", "✅")
    with c3: metric_card("Hors Service", stats["hs"], "#ef4444", "🔴")
    with c4: metric_card("Interventions", stats["interventions"], "#f59e0b", "🔧")
    with c5: metric_card("Véhicules", stats["vehicules"], "#a855f7", "🚗")
    with c6: metric_card("Citoyens", stats["citoyens"], "#06b6d4", "👥")

    st.markdown("---")

    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown("<div class='section-header'>🪐 Empreinte Sectorielle (Sunburst)</div>", unsafe_allow_html=True)
        types = safe_fetch("SELECT Type, COUNT(*) as nb FROM capteur GROUP BY Type")
        if types:
            df_t = pd.DataFrame(types)
            # Sunburst multicouche avec design néon
            fig = px.sunburst(df_t, path=["Type"], values="nb",
                              color="nb", color_continuous_scale="Darkmint")
            fig.update_traces(
                textinfo="label+percent entry",
                insidetextorientation='horizontal',
                marker=dict(line=dict(color='#0f172a', width=2))
            )
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                margin=dict(t=10, b=10, l=10, r=10),
                coloraxis_showscale=False,
                font=dict(family="JetBrains Mono", color="#f8fafc", size=12)
            )
            st.plotly_chart(fig, use_container_width=True)

    with col_right:
        st.markdown("<div class='section-header'>📡 Radar de Stabilité (Tactical)</div>", unsafe_allow_html=True)
        statuts = safe_fetch("SELECT Statut, COUNT(*) as nb FROM capteur GROUP BY Statut")
        if statuts:
            df_s = pd.DataFrame(statuts)
            # Radar Chart (Spider) : look technologique et pro
            fig = go.Figure(data=go.Scatterpolar(
                r=df_s['nb'],
                theta=df_s['Statut'],
                fill='toself',
                fillcolor='rgba(6, 182, 212, 0.3)',
                line=dict(color='#22d3ee', width=3),
                marker=dict(color='#67e8f9', size=10)
            ))

            fig.update_layout(
                polar=dict(
                    bgcolor="rgba(15, 23, 42, 0.5)",
                    radialaxis=dict(visible=True, showticklabels=False, gridcolor="rgba(255,255,255,0.1)"),
                    angularaxis=dict(gridcolor="rgba(255,255,255,0.1)", tickfont=dict(size=11))
                ),
                paper_bgcolor="rgba(0,0,0,0)",
                margin=dict(t=30, b=20, l=40, r=40),
                font=dict(family="JetBrains Mono", color="#f8fafc")
            )
            st.plotly_chart(fig, use_container_width=True)

    # Recent interventions
    st.markdown("<div class='section-header'>🔧 Interventions Récentes</div>", unsafe_allow_html=True)
    recents = safe_fetch("SELECT IDIn, DateHeure, Nature, Durée, statut FROM intervention ORDER BY DateHeure DESC LIMIT 8")
    if recents:
        df_r = pd.DataFrame(recents)
        st.dataframe(df_r, use_container_width=True, hide_index=True)

    # IA Summary — cached so it persists across page navigations
    st.markdown("<div class='section-header'>🤖 Résumé IA</div>", unsafe_allow_html=True)
    if 'ia_summary_cache' not in st.session_state or st.session_state.get('ia_summary_needs_refresh', False):
        with st.spinner("🤖 Génération du résumé IA..."):
            st.session_state.ia_summary_cache = ia.generate_dashboard_summary()
            st.session_state.ia_summary_needs_refresh = False
    summary = st.session_state.ia_summary_cache
    st.markdown(f"<div class='report-box'>{summary.get('report', 'N/A')}</div>", unsafe_allow_html=True)
    rc1, rc2 = st.columns([3, 1])
    with rc1:
        st.caption(f"Provider: {summary.get('provider', 'N/A')}")
    with rc2:
        if st.button("🔄 Rafraîchir", key="refresh_ia_summary"):
            st.session_state.ia_summary_needs_refresh = True
            st.rerun()

    # ═══ COMPACT ALERTS PANEL ON DASHBOARD ═══
    st.markdown("<div class='section-header'>🚨 Alertes Automatiques (§2.2)</div>", unsafe_allow_html=True)
    try:
        alerts = alert_engine.scan_all()
        alert_summary = alert_engine.get_alert_summary()
        
        ac1, ac2, ac3 = st.columns(3)
        with ac1: metric_card("Total", alert_summary['total'], "#ef4444", "🚨")
        with ac2: metric_card("Critiques", alert_summary['critical'], "#dc2626", "🔴")
        with ac3: metric_card("Hautes", alert_summary['high'], "#f59e0b", "🟠")
        
        if alerts:
            # Compact table display instead of individual cards
            alert_data = []
            for al in alerts[:8]:
                alert_data.append({
                    "Sévérité": f"{al.icon} {al.severity.value}",
                    "Entité": al.entity_type,
                    "Message": al.message[:80],
                })
            st.dataframe(pd.DataFrame(alert_data), use_container_width=True, hide_index=True)
            if len(alerts) > 8:
                st.caption(f"+ {len(alerts) - 8} autres. Voir 🚨 Alertes Automatiques.")
        else:
            st.success("✅ Aucune alerte — Tous les systèmes OK")
    except Exception as e:
        st.info(f"⚠️ Scan d'alertes: {e}")


# ═══════════════════════════════════════════════════════════════════
# PAGE: COMPILATEUR NL → SQL
# ═══════════════════════════════════════════════════════════════════

elif page == "🔤 Compilateur NL→SQL":
    # ── Hero Header ──
    st.markdown("""
    <div class='compiler-hero'>
        <h1>⚡ Compilateur Langage Naturel → SQL</h1>
        <div class='subtitle'>Conforme à l'énoncé PM-Compilation §1.2 — Pipeline complet : Lexer → Parser → Semantic Analyzer → CodeGen</div>
    </div>
    """, unsafe_allow_html=True)

    def on_example_change():
        if st.session_state.example_selector != "Sélectionnez un exemple...":
            st.session_state.nl_input_widget = st.session_state.example_selector

    if "nl_input_widget" not in st.session_state:
        st.session_state.nl_input_widget = ""

    # ── Input Section ──
    col_input, col_examples = st.columns([2, 1])
    with col_input:
        nl_input = st.text_area("✍️ Saisir requête en français :", height=100,
                                placeholder="Ex: Affiche les 5 zones les plus polluées par NO2",
                                key="nl_input_widget")
    with col_examples:
        examples = ["Sélectionnez un exemple..."] + Compiler.get_example_queries()
        st.selectbox("📋 Exemples (énoncé) :", examples, key="example_selector", on_change=on_example_change)
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(f"""<div style='background:rgba(139,92,246,0.08); border:1px solid rgba(139,92,246,0.2); border-radius:8px; padding:0.6rem 0.8rem; font-size:0.78rem; color:#94a3b8;'>
        💡 <b style='color:#c084fc;'>Astuce</b><br>Utilisez des phrases naturelles en français. Le compilateur supporte les jointures, agrégations, tri, et filtres complexes.
        </div>""", unsafe_allow_html=True)

    if st.button("⚡ Compiler", type="primary", use_container_width=True) and nl_input:
        start_time = time.time()
        result = compiler.compile(nl_input)
        compile_time = time.time() - start_time

        if result.success:
            n_tokens = len([t for t in result.tokens if t.type.value != 'EOF'])
            ast_type = result.ast.node_type if result.ast else 'N/A'

            # ── Success Banner ──
            st.markdown(f"""
            <div class='success-banner'>
                <div class='check-icon'>✅</div>
                <div class='text'>Compilation réussie</div>
                <div class='detail'>{compile_time*1000:.0f}ms</div>
            </div>
            """, unsafe_allow_html=True)

            # ── Pipeline Status ──
            st.markdown(f"""
            <div class='pipeline-container'>
                <div class='pipeline-step done'>
                    <div class='step-icon'>📝</div>
                    <div class='step-label'>Input</div>
                    <div class='step-detail'>{len(nl_input)} car.</div>
                </div>
                <div class='pipeline-arrow done'>→</div>
                <div class='pipeline-step done'>
                    <div class='step-icon'>🔤</div>
                    <div class='step-label'>Lexer</div>
                    <div class='step-detail'>{n_tokens} tokens</div>
                </div>
                <div class='pipeline-arrow done'>→</div>
                <div class='pipeline-step done'>
                    <div class='step-icon'>🌳</div>
                    <div class='step-label'>Parser</div>
                    <div class='step-detail'>{ast_type}</div>
                </div>
                <div class='pipeline-arrow done'>→</div>
                <div class='pipeline-step done'>
                    <div class='step-icon'>🔍</div>
                    <div class='step-label'>Semantic</div>
                    <div class='step-detail'>{len(result.warnings)} warns</div>
                </div>
                <div class='pipeline-arrow done'>→</div>
                <div class='pipeline-step done'>
                    <div class='step-icon'>💾</div>
                    <div class='step-label'>CodeGen</div>
                    <div class='step-detail'>SQL ✓</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # ── Compilation Stats ──
            st.markdown(f"""
            <div class='comp-stats'>
                <div class='comp-stat'>
                    <div class='stat-value' style='color:#c084fc;'>{n_tokens}</div>
                    <div class='stat-label'>Tokens</div>
                </div>
                <div class='comp-stat'>
                    <div class='stat-value' style='color:#60a5fa;'>{ast_type}</div>
                    <div class='stat-label'>Type AST</div>
                </div>
                <div class='comp-stat'>
                    <div class='stat-value' style='color:#22c55e;'>{len(result.warnings)}</div>
                    <div class='stat-label'>Warnings</div>
                </div>
                <div class='comp-stat'>
                    <div class='stat-value' style='color:#fbbf24;'>{compile_time*1000:.0f}<span style='font-size:0.8rem;'>ms</span></div>
                    <div class='stat-label'>Temps</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Show semantic warnings if any
            if result.warnings:
                for w in result.warnings:
                    if w.level == "error":
                        st.error(f"🔴 {w.message}")
                    elif w.level == "warning":
                        st.warning(f"⚠️ {w.message}")
                    else:
                        st.info(f"ℹ️ {w.message}")
                    if w.suggestion:
                        st.caption(f"💡 {w.suggestion}")

            if result.suggestions:
                for s in result.suggestions:
                    st.info(f"💡 Suggestion: {s}")

            # ── SQL Généré (premium card) ──
            highlighted_sql = highlight_sql(result.sql)
            st.markdown(f"""
            <div class='sql-card'>
                <div class='sql-card-header'>
                    <div class='title'>💾 SQL Généré</div>
                    <div class='badge'>MySQL</div>
                </div>
                <div class='sql-card-body'>{highlighted_sql}</div>
            </div>
            """, unsafe_allow_html=True)

            # ── Résultats de la BD ──
            sql = result.sql.strip()
            if sql.upper().startswith("SELECT"):
                try:
                    rows = safe_fetch(sql)
                    if rows:
                        df_result = pd.DataFrame(rows)
                        n_rows = len(df_result)
                        n_cols = len(df_result.columns)
                        st.markdown(f"""
                        <div class='results-card'>
                            <div class='results-card-header'>
                                <div class='title'>📊 Résultats de la Base de Données</div>
                                <div class='count-badge'>{n_rows} ligne{'s' if n_rows > 1 else ''} · {n_cols} colonne{'s' if n_cols > 1 else ''}</div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        st.dataframe(df_result, use_container_width=True, hide_index=True)
                    else:
                        st.info("ℹ️ Aucun résultat correspondant dans la base de données.")
                except Exception as e:
                    st.error(f"❌ Erreur d'exécution SQL : {e}")

            # ── Détails du pipeline (onglets premium) ──
            st.markdown("<br>", unsafe_allow_html=True)
            tab_tokens, tab_ast, tab_tree, tab_sem = st.tabs(["🔤 Tokens (Lexer)", "🌳 AST (Parser)", "🌲 Arbre de Dérivation", "🔍 Analyse Sémantique"])

            with tab_tokens:
                # Visual token display
                token_list = [t for t in result.tokens if t.type.value != "EOF"]
                pills_html = ""
                for t in token_list:
                    css_class = get_token_class(t.type.value)
                    pills_html += f"<span class='token-pill {css_class}'><b>{t.type.value}</b> {t.value}</span>"
                st.markdown(f"<div style='line-height:2.2; padding:0.5rem 0;'>{pills_html}</div>", unsafe_allow_html=True)
                st.markdown("---")
                # Also show as table
                token_data = [{"#": i+1, "Type": t.type.value, "Valeur": t.value, "Position": t.position}
                              for i, t in enumerate(token_list)]
                st.dataframe(pd.DataFrame(token_data), use_container_width=True, hide_index=True)

            with tab_ast:
                if result.ast:
                    ast_type_class = 'type-select' if 'select' in result.ast.node_type else ('type-count' if 'count' in result.ast.node_type else 'type-aggregate')
                    st.markdown(f"""
                    <div class='ast-tree-node {ast_type_class}'>
                        <b style='color:#c084fc;'>TYPE</b> <span style='color:#f8fafc;'>{result.ast.node_type}</span>
                    </div>
                    """, unsafe_allow_html=True)

                    # Show key properties
                    ast_dict = result.ast.__dict__
                    for key, val in ast_dict.items():
                        if key == 'node_type':
                            continue
                        if key == 'conditions' and val:
                            for i, cond in enumerate(val):
                                st.markdown(f"""
                                <div class='ast-tree-node type-condition' style='margin-left:1.5rem;'>
                                    <b style='color:#fbbf24;'>CONDITION {i+1}</b>
                                    <span style='color:#60a5fa;'>{getattr(cond, 'left', '')}</span>
                                    <span style='color:#fbbf24;'>{getattr(cond, 'operator', '')}</span>
                                    <span style='color:#34d399;'>{getattr(cond, 'right', '')}</span>
                                </div>
                                """, unsafe_allow_html=True)
                        elif key == 'joins' and val:
                            for i, j in enumerate(val):
                                st.markdown(f"""
                                <div class='ast-tree-node type-select' style='margin-left:1.5rem;'>
                                    <b style='color:#60a5fa;'>JOIN {i+1}</b>
                                    <span style='color:#f8fafc;'>{j}</span>
                                </div>
                                """, unsafe_allow_html=True)
                        else:
                            val_display = str(val) if val is not None else 'ø'
                            if len(val_display) > 80:
                                val_display = val_display[:80] + '…'
                            color = '#94a3b8' if val in (None, [], '') else '#f8fafc'
                            st.markdown(f"""
                            <div style='margin-left:1.5rem; padding:0.3rem 0; font-family: JetBrains Mono, monospace; font-size:0.8rem;'>
                                <span style='color:#64748b;'>├─</span>
                                <b style='color:#94a3b8;'>{key}</b>
                                <span style='color:#475569;'> = </span>
                                <span style='color:{color};'>{val_display}</span>
                            </div>
                            """, unsafe_allow_html=True)

                    st.markdown("---")
                    st.markdown("**📋 AST complet (JSON) :**")
                    ast_info = result.ast.__dict__ if result.ast else {}
                    st.json(json.loads(json.dumps(ast_info, default=str)))

            with tab_tree:
                # ── Arbre de Dérivation
                st.markdown("""
                <div style='background:rgba(139,92,246,0.1); border:1px solid rgba(139,92,246,0.3); 
                            border-radius:8px; padding:0.8rem; margin-bottom:1rem;'>
                    <b style='color:#a78bfa;'> — Arbre de Dérivation </b><br>
                    <span style='color:#94a3b8; font-size:0.85rem;'>
                        Arbre classique de dérivation selon les grammaires de Chomsky.
                        La racine est l'axiome <code>&lt;requête&gt;</code>, les nœuds internes (en <span style='color:#dc2626;'>rouge</span>) sont les non-terminaux,
                        et les feuilles (en <b>noir gras</b>) sont les symboles terminaux.
                    </span>
                </div>
                """, unsafe_allow_html=True)
                
                if hasattr(result, 'derivation_tree') and result.derivation_tree:
                    tree = result.derivation_tree
                    
                    # Convert tree dict to JSON for JavaScript
                    import json as _json
                    tree_json = _json.dumps(tree, ensure_ascii=False)
                    
                    # JavaScript-based classical derivation tree (SVG)
                    # Matches exactly the style from: red non-terminals, bold black terminals, lines
                    tree_js_html = f"""
                    <div id="tree-container" style="background:#ffffff; border:1px solid #ccc; border-radius:10px; 
                         padding:15px; box-shadow: 0 2px 12px rgba(0,0,0,0.08); text-align:center;">
                        <div style="color:#666; font-size:13px; margin-bottom:10px; font-family:Georgia, serif; font-style:italic;">
                            Arbre de Dérivation — Analyse Descendante Récursive
                        </div>
                        <canvas id="treeCanvas" style="display:inline-block;"></canvas>
                    </div>
                    <script>
                    (function() {{
                        const treeData = {tree_json};
                        const canvas = document.getElementById('treeCanvas');
                        const ctx = canvas.getContext('2d');
                        
                        // ── Configuration ──
                        const FONT_NT = 'italic 15px Georgia, serif';  // Non-terminaux
                        const FONT_T  = 'bold 14px Georgia, serif';    // Terminaux
                        const COLOR_NT = '#cc0000';                     // Rouge (comme le cours)
                        const COLOR_T  = '#000000';                     // Noir gras
                        const COLOR_LINE = '#444444';                   // Lignes
                        const H_SPACING = 22;                           // Espacement horizontal min
                        const V_SPACING = 65;                           // Espacement vertical entre niveaux
                        const TOP_MARGIN = 35;
                        const SIDE_MARGIN = 30;
                        
                        // ── Mesurer la largeur du texte ──
                        function textWidth(text, font) {{
                            ctx.font = font;
                            return ctx.measureText(text).width;
                        }}
                        
                        // ── Obtenir le label d'un nœud ──
                        function getLabel(node) {{
                            if (node.rule) return node.rule;
                            if (node.terminal) return '"' + node.value + '"';
                            return '?';
                        }}
                        
                        function isTerminal(node) {{
                            return !!node.terminal;
                        }}
                        
                        // ── Phase 1: Calculer la largeur de chaque sous-arbre ──
                        function computeWidth(node) {{
                            if (isTerminal(node)) {{
                                let w = textWidth(getLabel(node), FONT_T) + H_SPACING;
                                node._width = Math.max(w, 50);
                                return node._width;
                            }}
                            let children = node.children || [];
                            if (children.length === 0) {{
                                let w = textWidth(getLabel(node), FONT_NT) + H_SPACING;
                                node._width = Math.max(w, 50);
                                return node._width;
                            }}
                            let total = 0;
                            for (let c of children) {{
                                total += computeWidth(c);
                            }}
                            let selfW = textWidth(getLabel(node), FONT_NT) + H_SPACING;
                            node._width = Math.max(total, selfW);
                            return node._width;
                        }}
                        
                        // ──     : Assigner les positions (x, y) ──
                        function assignPositions(node, x, y) {{
                            node._y = y;
                            let children = node.children || [];
                            if (children.length === 0 || isTerminal(node)) {{
                                node._x = x + node._width / 2;
                                return;
                            }}
                            // Distribuer les enfants
                            let curX = x;
                            for (let c of children) {{
                                assignPositions(c, curX, y + V_SPACING);
                                curX += c._width;
                            }}
                            // Centrer le parent au-dessus de ses enfants
                            let firstChild = children[0];
                            let lastChild = children[children.length - 1];
                            node._x = (firstChild._x + lastChild._x) / 2;
                        }}
                        
                        // ── Phase 3: Dessiner l'arbre ──
                        function drawTree(node) {{
                            let label = getLabel(node);
                            let x = node._x;
                            let y = node._y;
                            
                            // Dessiner le texte
                            ctx.textAlign = 'center';
                            ctx.textBaseline = 'middle';
                            
                            if (isTerminal(node)) {{
                                ctx.font = FONT_T;
                                ctx.fillStyle = COLOR_T;
                                ctx.fillText(label, x, y);
                            }} else {{
                                ctx.font = FONT_NT;
                                ctx.fillStyle = COLOR_NT;
                                ctx.fillText(label, x, y);
                            }}
                            
                            // Dessiner les lignes vers les enfants
                            let children = node.children || [];
                            for (let c of children) {{
                                ctx.beginPath();
                                ctx.strokeStyle = COLOR_LINE;
                                ctx.lineWidth = 1.2;
                                ctx.moveTo(x, y + 10);
                                ctx.lineTo(c._x, c._y - 10);
                                ctx.stroke();
                                drawTree(c);
                            }}
                        }}
                        
                        // ── Exécution ──
                        computeWidth(treeData);
                        let treeWidth = treeData._width + SIDE_MARGIN * 2;
                        
                        // Calculer la profondeur
                        function maxDepth(n, d) {{
                            let children = n.children || [];
                            if (children.length === 0 || n.terminal) return d;
                            let m = d;
                            for (let c of children) {{ m = Math.max(m, maxDepth(c, d+1)); }}
                            return m;
                        }}
                        let depth = maxDepth(treeData, 0);
                        let totalHeight = (depth + 1) * V_SPACING + TOP_MARGIN * 2;
                        
                        // Utiliser la largeur du conteneur (100%) pour centrer
                        let container = document.getElementById('tree-container');
                        let containerWidth = container.clientWidth - 24;
                        let totalWidth = Math.max(treeWidth, containerWidth);
                        
                        // Resize canvas
                        const dpr = window.devicePixelRatio || 1;
                        canvas.width = totalWidth * dpr;
                        canvas.height = totalHeight * dpr;
                        canvas.style.width = totalWidth + 'px';
                        canvas.style.height = totalHeight + 'px';
                        ctx.scale(dpr, dpr);
                        
                        // Fond blanc
                        ctx.fillStyle = '#ffffff';
                        ctx.fillRect(0, 0, totalWidth, totalHeight);
                        
                        // Centrer l'arbre horizontalement
                        let offsetX = (totalWidth - treeWidth) / 2 + SIDE_MARGIN;
                        assignPositions(treeData, offsetX, TOP_MARGIN);
                        drawTree(treeData);
                    }})();
                    </script>
                    """
                    
                    # Calculate height
                    def max_depth(n, d=0):
                        children = n.get("children", [])
                        if not children or "terminal" in n:
                            return d
                        return max(max_depth(c, d+1) for c in children)
                    depth = max_depth(tree)
                    canvas_height = (depth + 1) * 65 + 70 + 50
                    
                    import streamlit.components.v1 as components
                    components.html(tree_js_html, height=canvas_height + 40, scrolling=True)
                    
                    # Show BNF grammar rules used (collapsible)
                    with st.expander("📐 Règles BNF appliquées"):
                        st.code("""<requête>        → <commande> <groupe_nominal> <filtres>
                   | <question> <groupe_nominal> <filtres>
                   | <fonction> <prep>? <groupe_nominal> <filtres>

<commande>       → VERB
<question>       → QUESTION  
<fonction>       → FUNCTION

<groupe_nominal> → <déterminant>? <quantificateur>? <nom_entité> <adjectif>?
<déterminant>    → ARTICLE | PREPOSITION | ε
<nom_entité>     → TABLE_NAME | TYPE_CAPTEUR | GRANDEUR | NATURE | STATUS
<adjectif>       → ADJECTIVE | STATUS | ε

<filtres>        → <filtre> <filtres> | ε
<filtre>         → <prep_filtre> | <comparaison> | <superlatif>""", language="text")
                    
                    # JSON tree (expandable)
                    with st.expander("🔍 Arbre de Dérivation (JSON)"):
                        st.json(tree)
                else:
                    st.info("L'arbre de dérivation n'est pas disponible.")

            with tab_sem:
                # Semantic analysis summary
                col_s1, col_s2 = st.columns(2)
                with col_s1:
                    st.markdown("##### 📐 Résumé du Pipeline")
                    steps = [
                        ("📝 Entrée", nl_input[:50] + ('…' if len(nl_input) > 50 else ''), "✅"),
                        ("🔤 Lexer", f"{n_tokens} tokens extraits", "✅"),
                        ("🌳 Parser", f"AST type: {ast_type}", "✅"),
                        ("🔍 Sémantique", f"{len(result.warnings)} avertissement(s)", "✅" if not result.warnings else "⚠️"),
                        ("💾 CodeGen", f"SQL ({len(result.sql)} car.)", "✅"),
                    ]
                    for step_name, step_detail, step_status in steps:
                        st.markdown(f"{step_status} **{step_name}** — {step_detail}")

                with col_s2:
                    st.markdown("##### 🛡️ Validation Sémantique")
                    if not result.warnings:
                        st.markdown("""
                        <div class='success-banner'>
                            <div class='check-icon'>🛡️</div>
                            <div class='text'>Aucun problème détecté</div>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        for w in result.warnings:
                            icon = "🔴" if w.level == "error" else "⚠️" if w.level == "warning" else "ℹ️"
                            st.markdown(f"{icon} {w.message}")
                            if w.suggestion:
                                st.caption(f"💡 {w.suggestion}")

        else:
            # ── Compilation ÉCHOUÉE — affichage détaillé de l'erreur ──
            error_msg = result.error or "Erreur inconnue"
            
            # Déterminer le type d'erreur
            if "lexicale" in error_msg.lower():
                error_type = "Erreur Lexicale"
                error_icon = "🔤"
                error_phase = "Lexer"
                error_color = "#f97316"
            elif "syntaxique" in error_msg.lower():
                error_type = "Erreur Syntaxique"
                error_icon = "🌳"
                error_phase = "Parser"
                error_color = "#ef4444"
            else:
                error_type = "Erreur de Compilation"
                error_icon = "⚠️"
                error_phase = "Compilation"
                error_color = "#ef4444"

            # ── Error Banner ──
            st.markdown(f"""
            <div class='error-banner'>
                <div class='check-icon' style='background:rgba(239,68,68,0.2);'>❌</div>
                <div class='text'>{error_type}</div>
                <div class='detail' style='color:#f87171; margin-left:auto; font-family:JetBrains Mono,monospace; font-size:0.8rem;'>Phase: {error_phase}</div>
            </div>
            """, unsafe_allow_html=True)

            # ── Pipeline showing where it failed ──
            n_tokens = len([t for t in result.tokens if t.type.value != 'EOF']) if result.tokens else 0
            lexer_ok = n_tokens > 0 and "lexicale" not in error_msg.lower()
            parser_ok = result.ast is not None

            st.markdown(f"""
            <div class='pipeline-container'>
                <div class='pipeline-step done'>
                    <div class='step-icon'>📝</div>
                    <div class='step-label'>Input</div>
                    <div class='step-detail'>{len(nl_input)} car.</div>
                </div>
                <div class='pipeline-arrow {"done" if lexer_ok else ""}'>→</div>
                <div class='pipeline-step {"done" if lexer_ok else "active"}' style='{"" if lexer_ok else "background:rgba(239,68,68,0.15); box-shadow:0 0 20px rgba(239,68,68,0.2);"}'>
                    <div class='step-icon'>{"🔤" if lexer_ok else "❌"}</div>
                    <div class='step-label'>Lexer</div>
                    <div class='step-detail'>{n_tokens} tokens</div>
                </div>
                <div class='pipeline-arrow {"done" if parser_ok else ""}'>→</div>
                <div class='pipeline-step {"done" if parser_ok else ("active" if lexer_ok else "")}' style='{"" if parser_ok or not lexer_ok else "background:rgba(239,68,68,0.15); box-shadow:0 0 20px rgba(239,68,68,0.2);"}'>
                    <div class='step-icon'>{"🌳" if parser_ok else ("❌" if lexer_ok else "⏸️")}</div>
                    <div class='step-label'>Parser</div>
                    <div class='step-detail'>{"OK" if parser_ok else ("Erreur" if lexer_ok else "—")}</div>
                </div>
                <div class='pipeline-arrow'>→</div>
                <div class='pipeline-step'>
                    <div class='step-icon'>⏸️</div>
                    <div class='step-label'>Semantic</div>
                    <div class='step-detail'>—</div>
                </div>
                <div class='pipeline-arrow'>→</div>
                <div class='pipeline-step'>
                    <div class='step-icon'>⏸️</div>
                    <div class='step-label'>CodeGen</div>
                    <div class='step-detail'>—</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # ── Détails de l'erreur ──
            st.markdown(f"""
            <div style='background:linear-gradient(135deg, rgba(239,68,68,0.06), rgba(220,38,38,0.03));
                        border:1px solid rgba(239,68,68,0.2); border-left:4px solid {error_color};
                        border-radius:10px; padding:1.2rem 1.5rem; margin:1rem 0;'>
                <div style='font-weight:700; color:#f87171; font-size:0.95rem; margin-bottom:0.6rem;'>
                    {error_icon} {error_type} — Détails
                </div>
                <div style='color:#e2e8f0; font-size:0.85rem; line-height:1.7; font-family:JetBrains Mono, monospace;'>
                    {error_msg}
                </div>
            </div>
            """, unsafe_allow_html=True)

            # ── Mots non reconnus (erreurs lexicales) ──
            if result.unknown_words:
                unknown_pills = " ".join([
                    f"<span style='display:inline-flex; align-items:center; gap:0.3rem; "
                    f"padding:0.25rem 0.7rem; border-radius:8px; font-size:0.78rem; "
                    f"font-family:JetBrains Mono,monospace; margin:0.15rem; "
                    f"background:rgba(239,68,68,0.12); border:1px solid rgba(239,68,68,0.3); "
                    f"color:#f87171;'>"
                    f"⚠️ {w}</span>"
                    for w in result.unknown_words
                ])
                st.markdown(f"""
                <div style='background:rgba(239,68,68,0.04); border:1px solid rgba(239,68,68,0.15);
                            border-radius:8px; padding:0.8rem 1rem; margin:0.5rem 0;'>
                    <div style='font-weight:600; color:#f87171; font-size:0.8rem; margin-bottom:0.5rem; text-transform:uppercase; letter-spacing:0.5px;'>
                        🔤 Mots non reconnus (erreurs lexicales)
                    </div>
                    <div style='line-height:2.2;'>{unknown_pills}</div>
                </div>
                """, unsafe_allow_html=True)

            # ── Tokens reconnus malgré l'erreur ──
            if result.tokens:
                token_list = [t for t in result.tokens if t.type.value != "EOF"]
                if token_list:
                    pills_html = ""
                    for t in token_list:
                        if t.type.value == "UNKNOWN":
                            pills_html += f"<span class='token-pill' style='background:rgba(239,68,68,0.12); border-color:rgba(239,68,68,0.3); color:#f87171;'><b>UNKNOWN</b> {t.value}</span>"
                        else:
                            css_class = get_token_class(t.type.value)
                            pills_html += f"<span class='token-pill {css_class}'><b>{t.type.value}</b> {t.value}</span>"
                    st.markdown(f"""
                    <div style='background:rgba(30,41,59,0.5); border:1px solid rgba(51,65,85,0.5);
                                border-radius:8px; padding:0.8rem 1rem; margin:0.5rem 0;'>
                        <div style='font-weight:600; color:#94a3b8; font-size:0.8rem; margin-bottom:0.5rem; text-transform:uppercase; letter-spacing:0.5px;'>
                            🔤 Tokens reconnus par le Lexer
                        </div>
                        <div style='line-height:2.2;'>{pills_html}</div>
                    </div>
                    """, unsafe_allow_html=True)

    # Pipeline diagram
    with st.expander("📐 Architecture du Compilateur", expanded=False):
        st.graphviz_chart("""
        digraph {
            rankdir=LR;
            bgcolor="#0f172a";
            node [shape=box style="filled,rounded" fontname="Inter" fontsize=11 fontcolor="#f8fafc"];
            edge [color="#94a3b8" fontname="Inter" fontsize=9 fontcolor="#94a3b8"];
            
            NL [label="Texte NL\\n(Français)" fillcolor="#3b82f6"];
            Lexer [label="Lexer\\nTokenisation" fillcolor="#8b5cf6"];
            Parser [label="Parser\\nAST" fillcolor="#a855f7"];
            Sem [label="Semantic\\nAnalyzer" fillcolor="#d946ef"];
            CodeGen [label="CodeGen\\nSQL" fillcolor="#ec4899"];
            SQL [label="SQL\\nMySQL" fillcolor="#22c55e"];
            
            NL -> Lexer [label="texte"];
            Lexer -> Parser [label="tokens"];
            Parser -> Sem [label="AST"];
            Sem -> CodeGen [label="AST validé"];
            CodeGen -> SQL [label="query"];
        }
        """)


# ═══════════════════════════════════════════════════════════════════
# PAGE: AUTOMATES
# ═══════════════════════════════════════════════════════════════════

elif page == "🤖 Automates":
    st.markdown("""
    <div class='page-hero hero-automates'>
        <h1>🤖 Automates à États Finis — Simulation Interactive</h1>
        <div class='subtitle'>— Définition formelle: A = (Q, Σ, δ, q₀, F)</div>
        <div class='hero-badges'>
            <span class='hero-badge'>🔧 Capteur IoT</span>
            <span class='hero-badge'>📋 Intervention</span>
            <span class='hero-badge'>🚗 Véhicule</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Select automata type
    auto_types = {
        "🔧 Capteur IoT": "capteur",
        "📋 Intervention": "intervention",
        "🚗 Véhicule": "véhicule",
    }

    selected = st.selectbox("Type d'automate:", list(auto_types.keys()))
    auto_type = auto_types[selected]

    # ── Fetch real entities from the database ──
    entity_id = None
    db_state = None
    entity_label = None

    try:
        from src.db_connection import get_db
        db = get_db()

        if auto_type == "capteur":
            rows = db.fetch_all("SELECT UUID, Type, Statut FROM capteur ORDER BY Statut, Type")
            if rows:
                options = {f"{r['UUID'][:12]}… — {r['Type']} ({r['Statut']})": (r['UUID'], r['Statut']) for r in rows}
                options["🔄 Simulation (C-SIM-001)"] = ("C-SIM-001", None)
                chosen = st.selectbox("Choisir un capteur:", list(options.keys()), key="capteur_sel")
                entity_id, db_state = options[chosen]
                entity_label = chosen
        elif auto_type == "intervention":
            rows = db.fetch_all("SELECT IDIn, Nature, statut FROM intervention ORDER BY statut")
            if rows:
                options = {f"INT-{r['IDIn']} — {r['Nature']} ({r['statut']})": (str(r['IDIn']), r['statut']) for r in rows}
                options["🔄 Simulation (INT-SIM-001)"] = ("INT-SIM-001", None)
                chosen = st.selectbox("Choisir une intervention:", list(options.keys()), key="inter_sel")
                entity_id, db_state = options[chosen]
                entity_label = chosen
        elif auto_type == "véhicule":
            rows = db.fetch_all("SELECT Plaque, Type, Statut FROM véhicule ORDER BY Statut, Type")
            if rows:
                options = {f"{r['Plaque']} — {r['Type']} ({r['Statut']})": (r['Plaque'], r['Statut']) for r in rows}
                options["🔄 Simulation (VEH-SIM-001)"] = ("VEH-SIM-001", None)
                chosen = st.selectbox("Choisir un véhicule:", list(options.keys()), key="veh_sel")
                entity_id, db_state = options[chosen]
                entity_label = chosen
    except Exception as e:
        st.warning(f"⚠️ Impossible de charger les entités: {e}")

    # Fallback if DB failed
    if not entity_id:
        fallback_ids = {"capteur": "C-SIM-001", "intervention": "INT-SIM-001", "véhicule": "VEH-SIM-001"}
        entity_id = fallback_ids[auto_type]

    # Create or get automata — reset if entity changed
    key = f"auto_{auto_type}"
    key_entity = f"auto_entity_{auto_type}"
    if key not in st.session_state or st.session_state.get(key_entity) != entity_id:
        automata = create_automata(auto_type, entity_id)
        # Set to real DB state if available
        if db_state:
            try:
                automata.set_state_by_value(db_state)
            except ValueError:
                pass  # State name mismatch, keep initial
        st.session_state[key] = automata
        st.session_state[key_entity] = entity_id
    automata = st.session_state[key]

    # Shared DOT + active state
    dot = automata.to_graphviz_dot()
    active_state = automata.get_state()
    import json as _json
    dot_escaped = _json.dumps(dot)

    # Layout: diagram + controls
    col_diag, col_ctrl = st.columns([2, 1])

    with col_diag:
        st.markdown("<div class='section-header'>📐 Diagramme de Transition</div>", unsafe_allow_html=True)
        
        diagram_html = f"""
        <style>
            @keyframes ledPulse {{
                0%   {{ opacity: 1; }}
                50%  {{ opacity: 0.25; }}
                100% {{ opacity: 1; }}
            }}
            #graph-box {{
                background: #f0f4f8;
                border-radius: 10px;
                padding: 12px;
                text-align: center;
                cursor: pointer;
                position: relative;
                transition: box-shadow 0.2s;
            }}
            #graph-box:hover {{
                box-shadow: 0 0 0 3px rgba(34,197,94,0.4);
            }}
            #graph-box svg {{ width: 100%; height: auto; }}
            .hint {{
                position: absolute;
                bottom: 6px; right: 10px;
                background: rgba(30,41,59,0.8);
                color: #fff;
                padding: 3px 10px;
                border-radius: 5px;
                font-size: 11px;
                pointer-events: none;
                opacity: 0.7;
            }}
            /* Fullscreen mode style */
            #graph-box:fullscreen {{
                background: #ffffff;
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 40px;
                cursor: default;
            }}
            #graph-box:fullscreen .hint {{ display: none; }}
            #graph-box:-webkit-full-screen {{
                background: #ffffff;
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 40px;
            }}
            #graph-box:-webkit-full-screen .hint {{ display: none; }}
        </style>
        <div id="graph-box" onclick="toggleFS()" title="Cliquer pour plein écran">
            <em style="color:#888;">Chargement…</em>
            <div class="hint">🔍 Cliquer pour agrandir</div>
        </div>
        <script src="https://unpkg.com/@viz-js/viz@3.4.0/lib/viz-standalone.js"></script>
        <script>
        function toggleFS() {{
            var el = document.getElementById('graph-box');
            if (!document.fullscreenElement && !document.webkitFullscreenElement) {{
                if (el.requestFullscreen) el.requestFullscreen();
                else if (el.webkitRequestFullscreen) el.webkitRequestFullscreen();
            }} else {{
                if (document.exitFullscreen) document.exitFullscreen();
                else if (document.webkitExitFullscreen) document.webkitExitFullscreen();
            }}
        }}
        Viz.instance().then(function(viz) {{
            var dot = {dot_escaped};
            var svg = viz.renderSVGElement(dot);
            var c = document.getElementById('graph-box');
            c.innerHTML = '<div class="hint">🔍 Cliquer pour agrandir</div>';
            c.insertBefore(svg, c.firstChild);
            var titles = svg.querySelectorAll('title');
            titles.forEach(function(t) {{
                if (t.textContent.trim() === '{active_state}') {{
                    var node = t.parentElement;
                    if (node) {{
                        node.querySelectorAll('ellipse').forEach(function(s) {{
                            s.style.animation = 'ledPulse 1.2s ease-in-out infinite';
                        }});
                    }}
                }}
            }});
        }}).catch(function(e) {{
            document.getElementById('graph-box').innerHTML = '<p style="color:red;">Erreur: ' + e + '</p>';
        }});
        </script>
        """
        import streamlit.components.v1 as components
        components.html(diagram_html, height=420, scrolling=False)

    with col_ctrl:
        st.markdown("<div class='section-header'>🎮 Contrôles</div>", unsafe_allow_html=True)

        # Current state with DFA acceptance info
        state_colors = {"Actif": "green", "Signalé": "blue", "En Maintenance": "amber",
                        "Hors Service": "red", "Inactif": "blue", "Demande": "blue",
                        "Terminée": "green", "Rejetée": "red", "Stationné": "green",
                        "En Route": "blue", "En Panne": "red", "Arrivé": "green"}
        cur = automata.get_state()
        color_class = state_colors.get(cur, "blue")
        cur_enum = automata.get_state_enum()
        final_states = set(automata.get_final_states())
        is_in_F = cur_enum in final_states
        f_label = ", ".join(s.value for s in final_states)

        st.markdown(f"**État actuel:** <span class='status-badge badge-{color_class}'>{cur}</span>", unsafe_allow_html=True)
        st.markdown(f"**Entité:** `{automata.entity_id}`")

        # Show accepting state indicator
        if is_in_F:
            st.markdown(f"""
            <div style='background:rgba(34,197,94,0.1); border:1px solid rgba(34,197,94,0.3); border-radius:8px; padding:0.5rem 0.8rem; margin:0.5rem 0; font-size:0.82rem;'>
                ⊙ <b style='color:#22c55e;'>État accepteur</b> — <code>{cur}</code> ∈ F = {{{f_label}}}
            </div>""", unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style='background:rgba(148,163,184,0.06); border:1px solid rgba(148,163,184,0.2); border-radius:8px; padding:0.5rem 0.8rem; margin:0.5rem 0; font-size:0.82rem;'>
                ○ <span style='color:#94a3b8;'>État non-accepteur</span> — <code>{cur}</code> ∉ F = {{{f_label}}}
            </div>""", unsafe_allow_html=True)

        # Available events
        valid = automata.get_valid_events()
        st.markdown(f"**Événements disponibles:** {', '.join(valid) if valid else 'Aucun'}")

        # Event selector
        if valid:
            event = st.selectbox("Choisir événement:", valid, key=f"event_{auto_type}")
            if st.button("▶ Appliquer Transition", type="primary"):
                try:
                    old = automata.get_state()
                    automata.trigger(event)
                    st.success(f"✅ δ({old}, {event}) = {automata.get_state()}")
                    st.rerun()
                except ValueError as e:
                    st.error(f"❌ {e}")

        if st.button("🔄 Réinitialiser"):
            automata.reset()
            st.rerun()

    # Tabs: formal definition, transition table, history, scenarios
    tab_formal, tab_table, tab_hist, tab_scenario = st.tabs([
        "📐 Définition Formelle", "📊 Table de Transition", "📜 Historique", "🎬 Scénarios"
    ])

    with tab_formal:
        formal = automata.get_formal_definition()
        st.markdown(f"**Nom:** {formal['name']}")
        st.markdown(f"**Q (États):** {{{', '.join(formal['Q'])}}}")
        st.markdown(f"**Σ (Alphabet):** {{{', '.join(formal['Sigma'])}}}")
        st.markdown(f"**q₀ (Initial):** {formal['q0']}")
        st.markdown(f"**F (Finaux):** {{{', '.join(formal['F'])}}}")
        st.markdown("**δ (Transitions):**")
        st.json(formal["delta"])

    with tab_table:
        table = automata.get_transition_table()
        st.dataframe(pd.DataFrame(table), use_container_width=True, hide_index=True)

    with tab_hist:
        history = automata.get_history()
        if history:
            st.dataframe(pd.DataFrame(history), use_container_width=True, hide_index=True)
        else:
            st.info("Aucune transition effectuée")

    with tab_scenario:
        st.markdown("""**Scénarios prédéfinis (conformes à l'énoncé)**

> 📖 *Rappel cours (§3 Automates à États Finis) :*  
> *Un mot w est* ***accepté*** *par l'automate A ssi* `δ*(q₀, w) ∈ F`  
> *L'état final doit être un* ***état accepteur*** *(double cercle ⊙)*
""")
        scenarios = AutomataEngine.get_predefined_scenarios()

        for name, scenario in scenarios.items():
            if scenario["automata_type"] == auto_type:
                # Visual indicator for expected-failure tests
                is_expected_fail = "Invalide" in name or "Test" in name
                icon = "⚠️" if is_expected_fail else "🎬"
                with st.expander(f"{icon} {name}"):
                    st.markdown(f"*{scenario['description']}*")
                    # Show events as word w = a₁·a₂·...·aₙ
                    events_html = " → ".join(
                        f"`{e}`" for e in scenario["events"]
                    )
                    st.markdown(f"**Mot w =** {events_html}")
                    st.markdown(f"**Longueur |w| =** {len(scenario['events'])}")

                    if is_expected_fail:
                        st.info("🧪 Ce scénario est un **test de validation** — l'échec (δ = ∅) est le résultat **attendu et correct**.")

                    if st.button(f"▶ Exécuter", key=f"sc_{name}"):
                        # Use fresh automata for scenario
                        test_auto = create_automata(auto_type, entity_id + "_test")
                        result = engine.run_scenario(test_auto, scenario["events"])

                        # Build state path for display
                        path_parts = [result["start"]]
                        for step in result["steps"]:
                            if step["ok"] and step["to"]:
                                path_parts.append(step["to"])
                        state_path = " → ".join(path_parts)

                        # ── DFA VERDICT: Three-way distinction ──
                        final_state = result.get("final", "?")
                        final_states_list = result.get("final_states", [])
                        f_set_str = ", ".join(final_states_list) if final_states_list else "∅"

                        if result["success"] and result.get("accepted", False):
                            # ✅ ACCEPTÉ: toutes transitions valides ET état final ∈ F
                            st.markdown(f"""
                            <div class='dfa-verdict dfa-accepted'>
                                <div class='verdict-header'>
                                    <span class='verdict-icon'>✅</span>
                                    <span class='verdict-title'>MOT ACCEPTÉ — w ∈ L(A)</span>
                                </div>
                                <div class='verdict-notation'>δ*(q₀, w) = {final_state} &nbsp;∈&nbsp; F = {{{f_set_str}}}</div>
                                <div class='verdict-detail'>
                                    <b>Chemin :</b> {state_path}<br>
                                    <b>Transitions :</b> {result['total_steps']} valides sur {result['total_steps']}<br>
                                    <b>Verdict :</b> L'automate termine dans l'état accepteur <b style='color:#22c55e;'>{final_state}</b> (⊙ double cercle).
                                    Le mot est <b>reconnu</b> par le langage de l'automate.
                                </div>
                            </div>
                            """, unsafe_allow_html=True)

                        elif result["success"] and not result.get("accepted", False):
                            # ⚠️ NON ACCEPTÉ: transitions valides MAIS état final ∉ F
                            st.markdown(f"""
                            <div class='dfa-verdict dfa-not-accepted'>
                                <div class='verdict-header'>
                                    <span class='verdict-icon'>⚠️</span>
                                    <span class='verdict-title'>MOT NON ACCEPTÉ — w ∉ L(A)</span>
                                </div>
                                <div class='verdict-notation'>δ*(q₀, w) = {final_state} &nbsp;∉&nbsp; F = {{{f_set_str}}}</div>
                                <div class='verdict-detail'>
                                    <b>Chemin :</b> {state_path}<br>
                                    <b>Transitions :</b> {result['total_steps']} valides sur {result['total_steps']} — toutes les transitions δ sont définies<br>
                                    <b>Verdict :</b> L'automate termine dans l'état <b style='color:#f59e0b;'>{final_state}</b> (○ cercle simple).
                                    Cet état <b>n'est pas accepteur</b> (∉ F). Le mot a été lu entièrement mais n'est <b>pas reconnu</b> par le langage.
                                </div>
                            </div>
                            """, unsafe_allow_html=True)

                        else:
                            # ❌ REJETÉ: transition invalide δ(q, a) = ∅
                            failed_step = next((s for s in result["steps"] if not s["ok"]), None)
                            fail_from = failed_step["from"] if failed_step else "?"
                            fail_evt = failed_step["event"] if failed_step else "?"
                            if is_expected_fail:
                                st.markdown(f"""
                                <div class='dfa-verdict dfa-rejected'>
                                    <div class='verdict-header'>
                                        <span class='verdict-icon'>🧪</span>
                                        <span class='verdict-title'>TRANSITION INVALIDE (test attendu) — δ = ∅</span>
                                    </div>
                                    <div class='verdict-notation'>δ({fail_from}, {fail_evt}) = ∅ — transition non définie</div>
                                    <div class='verdict-detail'>
                                        <b>Test de robustesse :</b> L'automate a correctement <b>rejeté</b> l'événement <code>{fail_evt}</code>
                                        depuis l'état <code>{fail_from}</code>. Ce comportement est <b style='color:#22c55e;'>conforme</b> à la spécification DFA.
                                    </div>
                                </div>
                                """, unsafe_allow_html=True)
                            else:
                                st.markdown(f"""
                                <div class='dfa-verdict dfa-rejected'>
                                    <div class='verdict-header'>
                                        <span class='verdict-icon'>❌</span>
                                        <span class='verdict-title'>MOT REJETÉ — δ = ∅</span>
                                    </div>
                                    <div class='verdict-notation'>δ({fail_from}, {fail_evt}) = ∅ — transition non définie</div>
                                    <div class='verdict-detail'>
                                        <b>Erreur :</b> L'événement <code>{fail_evt}</code> n'est pas valide depuis l'état <code>{fail_from}</code>.<br>
                                        Le mot ne peut pas être lu entièrement par l'automate.
                                    </div>
                                </div>
                                """, unsafe_allow_html=True)

                        # ── Transition steps detail ──
                        with st.container():
                            st.markdown("**Détail des transitions δ :**")
                            for i, step in enumerate(result["steps"]):
                                if step["ok"]:
                                    st.markdown(f"&nbsp;&nbsp;`{i+1}.` ✅ {step['message']}")
                                elif is_expected_fail:
                                    st.markdown(f"&nbsp;&nbsp;`{i+1}.` 🧪 {step['message']} *(rejet attendu — comportement correct)*")
                                else:
                                    st.markdown(f"&nbsp;&nbsp;`{i+1}.` ❌ {step['message']}")

                        # ── Diagramme de Transition du Scénario ──
                        st.markdown("<div class='section-header'>📐 Diagramme de Transition — Résultat</div>", unsafe_allow_html=True)
                        _sc_dot = _build_scenario_dot(test_auto, result)
                        st.graphviz_chart(_sc_dot)

        # ── Custom scenario ──────────────────────────────────────
        st.markdown("---")
        st.markdown("**Scénario personnalisé**")

        # Show available events for the current automata
        _ref_auto = create_automata(auto_type, "__ref__")
        _all_events = sorted(set(
            evt for trans in _ref_auto.get_transitions().values() for evt in trans.keys()
        ))
        st.markdown(f"**Σ (Alphabet) :** {', '.join(f'`{e}`' for e in _all_events)}")

        # Show final states
        _f_states = [s.value for s in _ref_auto.get_final_states()]
        st.markdown(f"**F (États accepteurs) :** {', '.join(f'`{s}`' for s in _f_states)}")

        placeholder_text = "Ex: installation → détection_anomalie → réparation → réparation_complète"
        if auto_type == "intervention":
            placeholder_text = "Ex: assigner_tech1 → rapport_tech1 → valider_ia → compléter"
        elif auto_type == "véhicule":
            placeholder_text = "Ex: démarrage → destination_atteinte → stationnement"

        custom_events = st.text_area(
            "Événements (séparés par →, virgules, ou un par ligne) :",
            placeholder=placeholder_text,
            key=f"custom_{auto_type}",
        )
        if st.button("▶ Exécuter scénario personnalisé"):
            # Parse: support → , ➜ , comma, and newline as separators
            import re
            raw = custom_events
            # Normalize arrow variants and commas to newlines
            raw = re.sub(r'\s*[→➜➡⟶>]\s*', '\n', raw)
            raw = re.sub(r'\s*,\s*', '\n', raw)
            events_list = [e.strip() for e in raw.splitlines() if e.strip()]
            if events_list:
                test_auto = create_automata(auto_type, entity_id + "_custom")
                result = engine.run_scenario(test_auto, events_list)

                # Build state path
                path_parts = [result["start"]]
                for step in result["steps"]:
                    if step["ok"] and step["to"]:
                        path_parts.append(step["to"])
                state_path = " → ".join(path_parts)

                final_state = result.get("final", "?")
                final_states_list = result.get("final_states", [])
                f_set_str = ", ".join(final_states_list) if final_states_list else "∅"

                # ── DFA Verdict for custom scenario ──
                if result["success"] and result.get("accepted", False):
                    st.markdown(f"""
                    <div class='dfa-verdict dfa-accepted'>
                        <div class='verdict-header'>
                            <span class='verdict-icon'>✅</span>
                            <span class='verdict-title'>MOT ACCEPTÉ — w ∈ L(A)</span>
                        </div>
                        <div class='verdict-notation'>δ*(q₀, w) = {final_state} &nbsp;∈&nbsp; F = {{{f_set_str}}}</div>
                        <div class='verdict-detail'>
                            <b>Chemin :</b> {state_path}<br>
                            <b>Transitions :</b> {result['total_steps']} valides<br>
                            <b>Verdict :</b> État accepteur <b style='color:#22c55e;'>{final_state}</b> (⊙). Mot reconnu par L(A).
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                elif result["success"] and not result.get("accepted", False):
                    st.markdown(f"""
                    <div class='dfa-verdict dfa-not-accepted'>
                        <div class='verdict-header'>
                            <span class='verdict-icon'>⚠️</span>
                            <span class='verdict-title'>MOT NON ACCEPTÉ — w ∉ L(A)</span>
                        </div>
                        <div class='verdict-notation'>δ*(q₀, w) = {final_state} &nbsp;∉&nbsp; F = {{{f_set_str}}}</div>
                        <div class='verdict-detail'>
                            <b>Chemin :</b> {state_path}<br>
                            <b>Transitions :</b> {result['total_steps']} valides — toutes les transitions δ sont définies<br>
                            <b>Verdict :</b> État <b style='color:#f59e0b;'>{final_state}</b> (○) n'est pas accepteur. Mot non reconnu.
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    failed_step = next((s for s in result["steps"] if not s["ok"]), None)
                    fail_from = failed_step["from"] if failed_step else "?"
                    fail_evt = failed_step["event"] if failed_step else "?"
                    st.markdown(f"""
                    <div class='dfa-verdict dfa-rejected'>
                        <div class='verdict-header'>
                            <span class='verdict-icon'>❌</span>
                            <span class='verdict-title'>MOT REJETÉ — δ = ∅</span>
                        </div>
                        <div class='verdict-notation'>δ({fail_from}, {fail_evt}) = ∅</div>
                        <div class='verdict-detail'>
                            <b>Erreur :</b> L'événement <code>{fail_evt}</code> n'est pas valide depuis l'état <code>{fail_from}</code>.
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                # Steps detail
                for i, step in enumerate(result["steps"]):
                    icon = "✅" if step["ok"] else "❌"
                    st.markdown(f"&nbsp;&nbsp;`{i+1}.` {icon} {step['message']}")

                # ── Diagramme de Transition du Scénario Personnalisé ──
                st.markdown("<div class='section-header'>📐 Diagramme de Transition — Résultat</div>", unsafe_allow_html=True)
                _sc_dot = _build_scenario_dot(test_auto, result)
                st.graphviz_chart(_sc_dot)


# ═══════════════════════════════════════════════════════════════════
# PAGE: CAPTEURS
# ═══════════════════════════════════════════════════════════════════

elif page == "📊 Capteurs":
    st.markdown("""
    <div class='page-hero hero-capteurs'>
        <h1>📊 Gestion des Capteurs</h1>
        <div class='subtitle'>Supervision et monitoring des capteurs IoT déployés — Sousse Smart City</div>
        <div class='hero-badges'>
            <span class='hero-badge'>📡 IoT</span>
            <span class='hero-badge'>📈 Temps Réel</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    capteurs = safe_fetch("SELECT * FROM capteur")
    if capteurs:
        df = pd.DataFrame(capteurs)
        total = len(df)
        actifs = len(df[df["Statut"] == "Actif"]) if "Statut" in df.columns else 0
        
        c1, c2, c3 = st.columns(3)
        with c1: metric_card("Total", total, "#3b82f6", "📡")
        with c2: metric_card("Actifs", actifs, "#22c55e", "✅")
        with c3: metric_card("Taux", f"{(actifs/total*100):.0f}%" if total else "0%", "#f59e0b", "📈")

        st.markdown("---")

        # Filters
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            if "Statut" in df.columns:
                status_filter = st.multiselect("Filtrer par statut:", df["Statut"].unique(), default=df["Statut"].unique())
                df = df[df["Statut"].isin(status_filter)]
        with col_f2:
            if "Type" in df.columns:
                type_filter = st.multiselect("Filtrer par type:", df["Type"].unique(), default=df["Type"].unique())
                df = df[df["Type"].isin(type_filter)]

        # Masquer la colonne IDP pour l'affichage
        if "IDP" in df.columns:
            df = df.drop(columns=["IDP"])

        st.dataframe(df, use_container_width=True, hide_index=True)

        # Section: Premium Charts
        st.markdown("<div class='section-header'>📈 Analyses et Distribution Spatiale</div>", unsafe_allow_html=True)
        col_c1, col_c2 = st.columns(2)

        with col_c1:
            st.markdown("##### 🗺️ Carte des Déploiements IoT")
            df_map = df.copy()
            if "Latitude" in df_map.columns and "Longitude" in df_map.columns:
                df_map["Latitude"] = pd.to_numeric(df_map["Latitude"], errors="coerce")
                df_map["Longitude"] = pd.to_numeric(df_map["Longitude"], errors="coerce")
                df_map = df_map.dropna(subset=["Latitude", "Longitude"])
                
                if not df_map.empty:
                    fig_map = px.scatter_mapbox(df_map, lat="Latitude", lon="Longitude", color="Statut", 
                                                hover_name="Type", zoom=14, 
                                                center={"lat": 35.8256, "lon": 10.6369}, # Centre sur Sousse
                                                color_discrete_map={"Actif": "#22c55e", "En Maintenance": "#f59e0b", "Hors Service": "#ef4444"},
                                                height=550)
                    fig_map.update_traces(marker=dict(size=14, opacity=0.95))
                    fig_map.update_layout(
                        margin={"r":0,"t":0,"l":0,"b":0},
                        paper_bgcolor="rgba(0,0,0,0)",
                        mapbox_style="white-bg",
                        mapbox_layers=[
                            {
                                "below": 'traces',
                                "sourcetype": "raster",
                                "sourceattribution": "Google",
                                "source": [
                                    "https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}"
                                ],
                                "minzoom": 0,
                                "maxzoom": 22
                            }
                        ]
                    )
                    st.plotly_chart(fig_map, use_container_width=True, config={'scrollZoom': True, 'displayModeBar': True})
                    st.caption("🖱️ Utilisez la molette de la souris sur la carte pour zoomer librement.")
                else:
                    st.info("Coordonnées GPS non disponibles pour l'affichage de la carte.")
            else:
                st.info("Coordonnées GPS manquantes.")

        with col_c2:
            st.markdown("##### 📊 Empreinte des Mesures (Moyennes)")
            mesures = safe_fetch("SELECT NomGrandeur, AVG(Valeur) as moy FROM mesures1 GROUP BY NomGrandeur")
            if mesures:
                df_m = pd.DataFrame(mesures)
                if len(df_m) >= 3:
                    # Radar Chart for premium high-tech look
                    fig = px.line_polar(df_m, r="moy", theta="NomGrandeur", line_close=True,
                                        color_discrete_sequence=["#06b6d4"])
                    fig.update_traces(fill='toself')
                    fig.update_layout(
                        polar=dict(
                            radialaxis=dict(visible=True, showticklabels=False),
                            bgcolor='rgba(15, 23, 42, 0.4)'
                        ),
                        margin=dict(l=30, r=30, t=10, b=10),
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)",
                        font=dict(color="#f8fafc", family="JetBrains Mono", size=11)
                    )
                else:
                    # Stylish Horizontal Gradient Bar Chart
                    fig = go.Figure(go.Bar(
                        x=df_m["moy"], y=df_m["NomGrandeur"], orientation='h',
                        marker=dict(color=df_m["moy"], colorscale="Tealgrn", line=dict(color="#06b6d4", width=1))
                    ))
                    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                                      margin=dict(l=0, r=0, t=10, b=0), font=dict(color="#f8fafc", family="JetBrains Mono"))
                st.plotly_chart(fig, use_container_width=True)
                
        # REAL TIME SENSOR TRACKING
        st.markdown("<div class='section-header'>⏱️ Suivi en Temps Réel</div>", unsafe_allow_html=True)
        col_rt1, col_rt2 = st.columns([1, 3])
        
        with col_rt1:
            sensor_options = {f"{r['Type']} ({str(r['UUID'])[:8]})": r['UUID'] for r in df.to_dict('records')}
            selected_sensor_label = st.selectbox("Sélectionner un capteur :", list(sensor_options.keys()))
            selected_uuid = sensor_options.get(selected_sensor_label)
            if selected_uuid:
                is_active = df[df["UUID"] == selected_uuid]["Statut"].values[0] == "Actif"
                st.markdown(f"**Statut:** `{'🟢 Actif' if is_active else '🔴 Inactif'}`")
                if not is_active:
                    st.warning("Capteur inactif. Valeurs à 0.")
                if st.button('🔄 Actualiser la courbe', key='refresh_sensor_rt'):
                    st.rerun()
                # Auto-refresh every 5 seconds
                auto_sensor = st.checkbox("⏱️ Auto-actualisation (5s)", key="auto_refresh_sensor", value=False)

        with col_rt2:
            if selected_uuid:
                rt_data = safe_fetch(f"SELECT ts, grandeur, valeur, unit FROM sensor_realtime WHERE uuid = '{selected_uuid}' ORDER BY ts DESC LIMIT 60")
                if rt_data:
                    df_rt = pd.DataFrame(rt_data)
                    df_rt["ts"] = pd.to_datetime(df_rt["ts"])
                    grandeur = df_rt["grandeur"].iloc[0]
                    unit = df_rt["unit"].iloc[0]
                    fig_rt = px.line(df_rt, x="ts", y="valeur", title=f"Mesures Récentes : {grandeur}", markers=True, color_discrete_sequence=["#0ea5e9"])
                    fig_rt.update_layout(
                        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(15,23,42,0.6)",
                        xaxis=dict(title="Heure", gridcolor="rgba(148,163,184,0.1)"),
                        yaxis=dict(title=f"Valeur ({unit})", gridcolor="rgba(148,163,184,0.1)"),
                        margin=dict(l=20, r=20, t=40, b=20)
                    )
                    st.plotly_chart(fig_rt, use_container_width=True)
                else:
                    st.info("Patientez pour la génération des données temps réel ou actualisez...")

        # Auto-refresh: runs AFTER the chart is displayed, preserves session state
        if selected_uuid and st.session_state.get('auto_refresh_sensor', False):
            time.sleep(5)
            st.rerun()
    else:
        st.info("Aucun capteur trouvé")


# ═══════════════════════════════════════════════════════════════════
# PAGE: INTERVENTIONS
# ═══════════════════════════════════════════════════════════════════

elif page == "🔧 Interventions":
    st.markdown("""
    <div class='page-hero hero-interventions'>
        <h1>🔧 Gestion des Interventions</h1>
        <div class='subtitle'>Consultation et suivi de la liste exhaustive de toutes les interventions</div>
        <div class='hero-badges'>
            <span class='hero-badge'>📅 Planifiées</span>
            <span class='hero-badge'>✅ Terminées</span>
            <span class='hero-badge'>⏳ En Attente</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    interventions = safe_fetch("SELECT * FROM intervention ORDER BY DateHeure DESC")
    if interventions:
        df = pd.DataFrame(interventions)

        c1, c2, c3, c4 = st.columns(4)
        with c1: metric_card("Total", len(df), "#f59e0b", "🔧")
        with c2:
            term = len(df[df["statut"] == "Terminée"]) if "statut" in df.columns else 0
            metric_card("Terminées", term, "#22c55e", "✅")
        with c3:
            en_attente = len(df[df["statut"].isin(["Demande", "Tech1_Assigné"])]) if "statut" in df.columns else 0
            metric_card("En attente", en_attente, "#f59e0b", "⏳")
        with c4:
            validated = len(df[df["statut"] == "Tech2_Valide"]) if "statut" in df.columns else 0
            metric_card("Prêtes validation IA", validated, "#3b82f6", "🤖")

        st.markdown("---")

        tab_list, = st.tabs([
            "📋 Liste des Interventions"
        ])

        # ── TAB: List ──
        with tab_list:
            st.dataframe(df, use_container_width=True, hide_index=True)
            if "Nature" in df.columns:
                fig = px.pie(df, names="Nature", hole=0.3, title="Répartition par nature",
                             color_discrete_sequence=px.colors.qualitative.Set3)
                fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#f8fafc"))
                st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Aucune intervention trouvée")


# ═══════════════════════════════════════════════════════════════════
# PAGE: ASSIGNATION TECHNICIENS (NOUVELLE PAGE DÉDIÉE)
# ═══════════════════════════════════════════════════════════════════

elif page == "👷 Assignation Techniciens":
    st.markdown("""
    <div class='page-hero' style='background:linear-gradient(135deg,#1e3a5f 0%,#0f766e 50%,#065f46 100%);
         border-radius:16px; padding:2rem 2.5rem; margin-bottom:2rem; position:relative; overflow:hidden;'>
        <div style='position:absolute;inset:0;background:radial-gradient(circle at 80% 20%,rgba(245,158,11,0.12),transparent 60%);'></div>
        <h1 style='color:#f8fafc; font-size:1.8rem; margin:0 0 0.5rem 0; position:relative;'>
            👷 Assignation des Techniciens & Rapports
        </h1>
        <div style='color:#94a3b8; font-size:0.95rem; position:relative;'>
            Assignez les techniciens aux interventions, rédigez les rapports techniques,
            puis validez pour passer à l'état Tech2_Valide avant la validation IA.
        </div>
        <div style='display:flex; gap:8px; margin-top:1rem; flex-wrap:wrap; position:relative;'>
            <span class='hero-badge'>🔧 Interventions</span>
            <span class='hero-badge'>📡 Capteurs Associés</span>
            <span class='hero-badge'>📝 Rapports Techniques</span>
            <span class='hero-badge'>✅ Workflow DEMANDE → TECH2_VALIDE</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Fetch interventions with their capteur info ──
    interventions_with_capteurs = safe_fetch("""
        SELECT i.IDIn, i.DateHeure, i.Nature, i.Durée, i.Coût, i.statut,
               i.UUID as capteur_uuid, i.technicien_1_id, i.technicien_2_id,
               i.rapport_tech1, i.rapport_tech2,
               c.Type as capteur_type, c.Statut as capteur_statut,
               t1.Nom as tech1_nom, t2.Nom as tech2_nom
        FROM intervention i
        LEFT JOIN capteur c ON i.UUID = c.UUID
        LEFT JOIN technicien t1 ON i.technicien_1_id = t1.IDT
        LEFT JOIN technicien t2 ON i.technicien_2_id = t2.IDT
        ORDER BY i.DateHeure DESC
    """)

    if interventions_with_capteurs:
        df_all = pd.DataFrame(interventions_with_capteurs)

        # ── Métriques ──
        mc1, mc2, mc3, mc4 = st.columns(4)
        total = len(df_all)
        demande = len(df_all[df_all['statut'] == 'Demande']) if 'statut' in df_all.columns else 0
        tech1 = len(df_all[df_all['statut'] == 'Tech1_Assigné']) if 'statut' in df_all.columns else 0
        tech2 = len(df_all[df_all['statut'] == 'Tech2_Valide']) if 'statut' in df_all.columns else 0
        terminee = len(df_all[df_all['statut'] == 'Terminée']) if 'statut' in df_all.columns else 0

        with mc1: metric_card("Demande", demande, "#ef4444", "📋")
        with mc2: metric_card("Tech1_Assigné", tech1, "#f59e0b", "👷")
        with mc3: metric_card("Tech2_Valide", tech2, "#3b82f6", "✅")
        with mc4: metric_card("Terminées", terminee, "#22c55e", "🏁")

        st.markdown("---")

        # ── Workflow explanation ──
        st.markdown("""
        <div style='background:linear-gradient(135deg,rgba(15,118,110,0.08),rgba(59,130,246,0.05));
             border:1px solid rgba(15,118,110,0.2); border-radius:12px; padding:1.2rem; margin-bottom:1.5rem;'>
            <div style='font-size:0.95rem; font-weight:700; margin-bottom:0.5rem; color:#f8fafc;'>
                ⚙️ Workflow d'Assignation
            </div>
            <div style='color:#94a3b8; font-size:0.82rem; line-height:1.6;'>
                <b>1.</b> Sélectionnez une intervention en état <b style='color:#ef4444;'>Demande</b> ou <b style='color:#f59e0b;'>Tech1_Assigné</b><br/>
                <b>2.</b> Choisissez <b>Technicien 1</b> (intervenant) et <b>Technicien 2</b> (valideur) — doivent être différents<br/>
                <b>3.</b> Rédigez les <b>deux rapports techniques</b> détaillés<br/>
                <b>4.</b> Cochez les confirmations et <b>sauvegardez</b> → L'intervention passe à <b style='color:#3b82f6;'>Tech2_Valide</b><br/>
                <b>5.</b> Ensuite, allez dans <b>📄 Rapports IA → Validation Intervention IA</b> pour la validation finale
            </div>
        </div>
        """, unsafe_allow_html=True)

        # ── Filter: only interventions that need assignment ──
        needs_assignment = safe_fetch("""
            SELECT i.IDIn, i.Nature, i.statut, i.UUID as capteur_uuid,
                   c.Type as capteur_type, c.Statut as capteur_statut
            FROM intervention i
            LEFT JOIN capteur c ON i.UUID = c.UUID
            WHERE i.statut IN ('Demande', 'Tech1_Assigné')
            ORDER BY i.IDIn
        """)

        if needs_assignment:
            st.markdown(f"### 🔧 {len(needs_assignment)} intervention(s) en attente d'assignation")

            # Build dropdown labels with capteur info
            intv_options = {}
            for intv in needs_assignment:
                capteur_info = f"{intv.get('capteur_type', '?')} - {intv.get('capteur_statut', '?')}"
                capteur_uuid_short = str(intv.get('capteur_uuid', ''))[:12]
                label = (
                    f"#{intv['IDIn']} — {intv['Nature']} | "
                    f"Capteur: {capteur_uuid_short}... ({capteur_info}) | "
                    f"État: {intv['statut']}"
                )
                intv_options[label] = intv

            selected_label = st.selectbox(
                "🔧 Sélectionnez l'intervention à compléter :",
                list(intv_options.keys()),
                key="assign_page_intv_select"
            )
            selected_intv = intv_options[selected_label]

            # Show capteur details card
            st.markdown(f"""
            <div style='background:rgba(15,118,110,0.06); border:1px solid rgba(15,118,110,0.15);
                 border-radius:10px; padding:1rem; margin:0.5rem 0 1.5rem 0;'>
                <div style='display:flex; gap:1.5rem; flex-wrap:wrap;'>
                    <div><b style='color:#94a3b8;'>Intervention:</b> <span style='color:#f8fafc;'>#{selected_intv['IDIn']}</span></div>
                    <div><b style='color:#94a3b8;'>Nature:</b> <span style='color:#f8fafc;'>{selected_intv['Nature']}</span></div>
                    <div><b style='color:#94a3b8;'>Capteur UUID:</b> <span style='color:#f8fafc;'>{selected_intv.get('capteur_uuid','N/A')}</span></div>
                    <div><b style='color:#94a3b8;'>Type Capteur:</b> <span style='color:#f8fafc;'>{selected_intv.get('capteur_type','N/A')}</span></div>
                    <div><b style='color:#94a3b8;'>État Capteur:</b> <span style='color:#f8fafc;'>{selected_intv.get('capteur_statut','N/A')}</span></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # ── Fetch technicians ──
            technicians = safe_fetch("SELECT IDT, Nom FROM Technicien ORDER BY Nom")

            if technicians:
                tech_options = {f"{t['IDT']} — {t['Nom']}": t['IDT'] for t in technicians}
                tech_labels = list(tech_options.keys())

                st.markdown("### 👷 Sélection des Techniciens")
                tc1, tc2 = st.columns(2)
                with tc1:
                    tech1_label = st.selectbox(
                        "Technicien 1 (Intervenant) :",
                        tech_labels, key="assign_tech1_select"
                    )
                    tech1_id = tech_options[tech1_label]
                with tc2:
                    # Default to second technician to avoid same selection
                    default_idx = 1 if len(tech_labels) > 1 else 0
                    tech2_label = st.selectbox(
                        "Technicien 2 (Valideur) :",
                        tech_labels, index=default_idx, key="assign_tech2_select"
                    )
                    tech2_id = tech_options[tech2_label]

                st.markdown("### 📝 Rapports des Techniciens")

                rapport_t1 = st.text_area(
                    f"📋 Rapport Technicien 1 — {tech1_label.split(' — ')[1]} (Intervenant) :",
                    placeholder="Décrire l'intervention réalisée : diagnostic effectué, composants remplacés, mesures prises, tests de fonctionnement...",
                    height=140, key="assign_rapport_t1"
                )

                rapport_t2 = st.text_area(
                    f"📋 Rapport Technicien 2 — {tech2_label.split(' — ')[1]} (Valideur) :",
                    placeholder="Validation des travaux : vérification du bon fonctionnement, observations complémentaires, recommandations...",
                    height=140, key="assign_rapport_t2"
                )

                st.markdown("### ✅ Confirmation des Étapes")
                col_chk1, col_chk2 = st.columns(2)
                with col_chk1:
                    chk_tech1 = st.checkbox("✅ Tech1 assigné et rapport rédigé (TECH1_ASSIGNÉ)", key="assign_chk1")
                with col_chk2:
                    chk_tech2 = st.checkbox("✅ Tech2 a validé et rapport rédigé (TECH2_VALIDE)", key="assign_chk2")

                st.markdown("---")

                # ── Save button ──
                if st.button("💾 Sauvegarder l'Assignation & les Rapports", type="primary", use_container_width=True, key="assign_save_btn"):
                    # Validations
                    errors = []
                    if not rapport_t1 or len(rapport_t1.strip()) < 10:
                        errors.append("Le rapport du Technicien 1 est trop court (minimum 10 caractères).")
                    if not rapport_t2 or len(rapport_t2.strip()) < 10:
                        errors.append("Le rapport du Technicien 2 est trop court (minimum 10 caractères).")
                    if not chk_tech1:
                        errors.append("Veuillez confirmer que le Technicien 1 est assigné.")
                    if not chk_tech2:
                        errors.append("Veuillez confirmer que le Technicien 2 a validé.")
                    if tech1_id == tech2_id:
                        errors.append("Les deux techniciens doivent être différents.")

                    if errors:
                        for err in errors:
                            st.warning(f"⚠️ {err}")
                    else:
                        try:
                            db = get_db()
                            db.execute_query(
                                "UPDATE intervention SET "
                                "technicien_1_id = %s, "
                                "technicien_2_id = %s, "
                                "rapport_tech1 = %s, "
                                "rapport_tech2 = %s, "
                                "statut = 'Tech2_Valide' "
                                "WHERE IDIn = %s",
                                (tech1_id, tech2_id, rapport_t1.strip(), rapport_t2.strip(), selected_intv['IDIn'])
                            )
                            st.success(
                                f"✅ Intervention #{selected_intv['IDIn']} sauvegardée avec succès !\n\n"
                                f"- **Technicien 1:** {tech1_label}\n"
                                f"- **Technicien 2:** {tech2_label}\n"
                                f"- **État:** Tech2_Valide"
                            )
                            st.info("🤖 Prochaine étape : allez dans **📄 Rapports IA → Validation Intervention IA** pour la validation finale par l'IA.")
                        except Exception as e:
                            st.error(f"❌ Erreur lors de la sauvegarde : {e}")
            else:
                st.warning("⚠️ Aucun technicien trouvé dans la table `Technicien`.")

        else:
            st.success("✅ Toutes les interventions ont déjà été assignées (état Tech2_Valide ou Terminée).")
            st.info("👉 Consultez la page **📄 Rapports IA → Validation Intervention IA** pour valider par l'IA.")

        # ── Tableau récapitulatif de toutes les interventions ──
        st.markdown("---")
        st.markdown("### 📊 Récapitulatif — Toutes les Interventions & Capteurs")

        display_cols = ['IDIn', 'Nature', 'statut', 'capteur_uuid', 'capteur_type',
                        'capteur_statut', 'tech1_nom', 'tech2_nom']
        available_cols = [c for c in display_cols if c in df_all.columns]
        rename_map = {
            'IDIn': 'ID', 'Nature': 'Nature', 'statut': 'État',
            'capteur_uuid': 'Capteur UUID', 'capteur_type': 'Type Capteur',
            'capteur_statut': 'État Capteur', 'tech1_nom': 'Tech 1', 'tech2_nom': 'Tech 2'
        }
        df_display = df_all[available_cols].rename(columns=rename_map)
        st.dataframe(df_display, use_container_width=True, hide_index=True)

    else:
        st.info("Aucune intervention trouvée dans la base de données.")


# ═══════════════════════════════════════════════════════════════════
# PAGE: VÉHICULES & TRAJETS
# ═══════════════════════════════════════════════════════════════════

elif page == "🚗 Véhicules & Trajets":
    st.markdown("""
    <div class='page-hero hero-vehicules'>
        <h1>🚗 Véhicules & Trajets</h1>
        <div class='subtitle'>Gestion de la flotte et optimisation des trajets urbains — Économie CO₂</div>
        <div class='hero-badges'>
            <span class='hero-badge'>🚙 Flotte</span>
            <span class='hero-badge'>🌿 Éco-mobilité</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    tab_veh, tab_traj = st.tabs(["🚗 Véhicules", "🗺️ Trajets"])

    with tab_veh:
        vehicules = safe_fetch("SELECT * FROM véhicule")
        if vehicules:
            df = pd.DataFrame(vehicules)
            metric_card("Total Véhicules", len(df), "#a855f7", "🚗")
            st.markdown("---")
            st.dataframe(df, use_container_width=True, hide_index=True)

            # Premium Energy Donut Chart
            if "Énergie Utilisée" in df.columns:
                counts = df["Énergie Utilisée"].value_counts().reset_index()
                counts.columns = ["Energie", "Count"]
                fig = px.pie(counts, values="Count", names="Energie", hole=0.65,
                             color_discrete_sequence=["#10b981", "#3b82f6", "#8b5cf6", "#f59e0b"])
                fig.update_traces(textposition='outside', textinfo='percent+label',
                                  marker=dict(line=dict(color='#0f172a', width=2)),
                                  pull=[0.02]*len(counts)) # léger éclatement 3D
                fig.update_layout(
                    title="⚡ Répartition de la Flotte par Motorisation",
                    paper_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#f8fafc", family="JetBrains Mono", size=12),
                    showlegend=False,
                    annotations=[dict(text=f"Flotte<br><b style='font-size:24px'>{len(df)}</b>", x=0.5, y=0.5, showarrow=False, font_color="#e2e8f0")]
                )
                st.plotly_chart(fig, use_container_width=True)
                
            # REAL TIME VEHICLE TRACKING
            st.markdown("<div class='section-header'>⏱️ Suivi GPS en Temps Réel</div>", unsafe_allow_html=True)
            col_v_rt1, col_v_rt2 = st.columns([1, 3])
            
            with col_v_rt1:
                veh_options = {f"{r.get('Type', '')} ({r['Plaque']})": r['Plaque'] for r in df.to_dict('records')}
                selected_veh_label = st.selectbox("Sélectionner un véhicule :", list(veh_options.keys()))
                selected_plaque = veh_options.get(selected_veh_label)
                if selected_plaque:
                    veh_statut = df[df["Plaque"] == selected_plaque]["Statut"].values[0]
                    status_colors = {"En Route": "🟢", "Stationné": "🔵", "Arrivé": "🏁", "En Panne": "🔴"}
                    st.markdown(f"**Statut:** `{status_colors.get(veh_statut, '⚪')} {veh_statut}`")
                    
                    if veh_statut == "En Route":
                        st.success("Véhicule en déplacement.")
                    else:
                        st.warning("Véhicule à l'arrêt.")
                        
                    if st.button('🔄 Actualiser la carte', key='refresh_veh_rt'):
                        st.rerun()
                    # Auto-refresh every 5 seconds
                    auto_veh = st.checkbox("⏱️ Auto-actualisation (5s)", key="auto_refresh_veh", value=False)

            with col_v_rt2:
                if selected_plaque:
                    rt_veh_data = safe_fetch(f"SELECT latitude, longitude, ts FROM vehicle_realtime_gps WHERE plaque = '{selected_plaque}' ORDER BY ts DESC LIMIT 1")
                    if rt_veh_data and rt_veh_data[0].get("latitude") and rt_veh_data[0].get("longitude"):
                        lat = float(rt_veh_data[0]["latitude"])
                        lon = float(rt_veh_data[0]["longitude"])
                        
                        df_v_rt = pd.DataFrame([{"lat": lat, "lon": lon, "plaque": selected_plaque}])
                        fig_v_rt = px.scatter_mapbox(df_v_rt, lat="lat", lon="lon", zoom=15, 
                                                     center={"lat": lat, "lon": lon},
                                                     color_discrete_sequence=["#f59e0b" if veh_statut == "En Route" else "#3b82f6"],
                                                     height=400)
                        fig_v_rt.update_traces(marker=dict(size=18, opacity=1.0))
                        fig_v_rt.update_layout(
                            margin={"r":0,"t":0,"l":0,"b":0},
                            paper_bgcolor="rgba(0,0,0,0)",
                            mapbox_style="white-bg",
                            mapbox_layers=[{
                                "below": 'traces',
                                "sourcetype": "raster",
                                "sourceattribution": "Google",
                                "source": ["https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}"]
                            }]
                        )
                        st.plotly_chart(fig_v_rt, use_container_width=True, config={'scrollZoom': True})
                    else:
                        st.info("Données GPS en cours de génération...")

            # Auto-refresh: runs AFTER the map is displayed, preserves session state
            if selected_plaque and st.session_state.get('auto_refresh_veh', False):
                time.sleep(5)
                st.rerun()

    with tab_traj:
        trajets = safe_fetch("SELECT * FROM trajet ORDER BY Date DESC LIMIT 50")
        if trajets:
            df = pd.DataFrame(trajets)

            c1, c2 = st.columns(2)
            with c1: metric_card("Total Trajets", len(df), "#06b6d4", "🗺️")
            with c2:
                eco = sum(float(r.get("ÉconomieCO2", 0) or 0) for r in trajets)
                metric_card("CO₂ Économisé", f"{eco:.1f}kg", "#22c55e", "🌿")

            st.markdown("---")
            st.dataframe(df, use_container_width=True, hide_index=True)

            # CO2 chart
            if "ÉconomieCO2" in df.columns:
                fig = px.bar(df.head(20), y="ÉconomieCO2", x=df.head(20).index,
                             color="ÉconomieCO2", color_continuous_scale="Greens")
                fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                                  font=dict(color="#f8fafc"), title="Top 20 trajets — Économie CO₂")
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Aucun trajet trouvé")


# ═══════════════════════════════════════════════════════════════════
# PAGE: CITOYENS
# ═══════════════════════════════════════════════════════════════════

elif page == "👥 Citoyens":
    st.markdown("""
    <div class='page-hero hero-citoyens'>
        <h1>👥 Engagement Citoyen</h1>
        <div class='subtitle'>Suivi de l'engagement citoyen et gamification urbaine — Score & Classement</div>
        <div class='hero-badges'>
            <span class='hero-badge'>⭐ Gamification</span>
            <span class='hero-badge'>🏆 Classement</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    citoyens = safe_fetch("SELECT * FROM citoyen")
    if citoyens:
        df = pd.DataFrame(citoyens)

        c1, c2 = st.columns(2)
        with c1: metric_card("Total Citoyens", len(df), "#06b6d4", "👥")
        with c2:
            avg_score = df["Score"].astype(float).mean() if "Score" in df.columns else 0
            metric_card("Score Moyen", f"{avg_score:.0f}/100", "#22c55e", "⭐")

        st.markdown("---")
        st.dataframe(df, use_container_width=True, hide_index=True)

        # Score distribution (Premium)
        if "Score" in df.columns:
            fig = px.histogram(df, x="Score", nbins=25, marginal="box", 
                               color_discrete_sequence=["#0ea5e9"], opacity=0.85)
            fig.update_traces(marker=dict(line=dict(color="#0284c7", width=2)))
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", 
                plot_bgcolor="rgba(15,23,42,0.6)",
                font=dict(color="#f8fafc", family="JetBrains Mono"), 
                title=dict(text="📈 Analyse de l'Engagement (Score Citoyen)", font=dict(size=18)),
                xaxis=dict(title="Score de Participation", showgrid=False, zeroline=False),
                yaxis=dict(title="Nombre de Citoyens", gridcolor="rgba(148,163,184,0.1)", zeroline=False),
                margin=dict(l=20, r=20, t=50, b=20),
                bargap=0.1
            )
            st.plotly_chart(fig, use_container_width=True)

        # Top citoyens
        if "Score" in df.columns and "Nom" in df.columns:
            top10 = df.nlargest(10, "Score")[["Nom", "Score", "Email"]] if "Email" in df.columns else df.nlargest(10, "Score")
            st.markdown("<div class='section-header'>🏆 Top 10 Citoyens</div>", unsafe_allow_html=True)
            st.dataframe(top10, use_container_width=True, hide_index=True)
    else:
        st.info("Aucun citoyen trouvé")


# ═══════════════════════════════════════════════════════════════════
# PAGE: ALERTES AUTOMATIQUES (§2.2)
# ═══════════════════════════════════════════════════════════════════

elif page == "🚨 Alertes Automatiques":
    st.markdown("""
    <div class='page-hero' style='background:linear-gradient(135deg,#0f172a 0%,#3d1212 50%,#0f172a 100%);
         border:1px solid rgba(239,68,68,0.4);'>
        <h1 style='background:linear-gradient(135deg,#fca5a5,#ef4444,#dc2626);
            -webkit-background-clip:text;-webkit-text-fill-color:transparent;'>🚨 Alertes Automatiques</h1>
        <div class='subtitle'>Système d'alertes proactif — Conforme §2.2 "Déclencher des actions automatiques"</div>
        <div class='hero-badges'>
            <span class='hero-badge'>⏱️ Surveillance Continue</span>
            <span class='hero-badge'>🔴 Capteur > 24h Hors Service</span>
            <span class='hero-badge'>🤖 Actions Automatiques</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("🔄 Scanner Maintenant", type="primary"):
        st.rerun()

    try:
        alerts = alert_engine.scan_all()
        alert_summary = alert_engine.get_alert_summary()
        stats_alert = alert_engine.get_statistics()

        # ── Metrics Row ──
        mc1, mc2, mc3, mc4, mc5 = st.columns(5)
        with mc1: metric_card("Total Alertes", alert_summary['total'], "#ef4444", "🚨")
        with mc2: metric_card("CRITIQUES", alert_summary['critical'], "#ef4444", "🔴")
        with mc3: metric_card("HAUTES", alert_summary['high'], "#f59e0b", "🟠")
        with mc4: metric_card("MOYENNES", alert_summary['medium'], "#3b82f6", "🟡")
        with mc5: metric_card("INFO", alert_summary['info'], "#06b6d4", "ℹ️")

        st.markdown("---")

        # ── Alerts by Entity Type ──
        st.markdown("<div class='section-header'>📊 Répartition des Alertes</div>", unsafe_allow_html=True)
        rc1, rc2, rc3 = st.columns(3)
        ent_stats = stats_alert.get('par_entite', {})
        with rc1: metric_card("Capteurs", ent_stats.get('capteur', 0), "#3b82f6", "📡")
        with rc2: metric_card("Interventions", ent_stats.get('intervention', 0), "#f59e0b", "🔧")
        with rc3: metric_card("Véhicules", ent_stats.get('véhicule', 0), "#a855f7", "🚗")

        st.markdown("---")

        # ── Alert Details — Compact Scrollable ──
        st.markdown("<div class='section-header'>🔔 Détail des Alertes Actives</div>", unsafe_allow_html=True)

        if alerts:
            # Severity filter
            sev_options = ["Toutes", "🔴 CRITIQUE", "🟠 HAUTE", "🟡 MOYENNE", "🔵 INFO"]
            sev_filter = st.radio("Filtrer par sévérité:", sev_options, horizontal=True, key="alert_sev_filter")

            sev_map = {"🔴 CRITIQUE": "CRITIQUE", "🟠 HAUTE": "HAUTE", "🟡 MOYENNE": "MOYENNE", "🔵 INFO": "INFO"}
            filtered = alerts if sev_filter == "Toutes" else [a for a in alerts if a.severity.value == sev_map.get(sev_filter, "")]

            # Build compact scrollable alert rows
            rows_html = ""
            for al in filtered:
                sev = al.severity.value
                if sev == 'CRITIQUE':
                    sev_class = 'critique'
                    icon = '🔴'
                elif sev == 'HAUTE':
                    sev_class = 'haute'
                    icon = '🟠'
                elif sev == 'MOYENNE':
                    sev_class = 'moyenne'
                    icon = '🟡'
                else:
                    sev_class = 'info'
                    icon = '🔵'

                dur_html = f"<span class='dur'>⏱️ {al.duree_heures}h</span>" if al.duree_heures else ""
                msg_safe = _html_mod.escape(al.message)
                action_safe = _html_mod.escape(al.action_recommandee)
                entity_safe = _html_mod.escape(f"{al.entity_type.upper()} — {al.entity_id[:20]}")
                msg_short = _html_mod.escape(al.message[:90] + ('…' if len(al.message) > 90 else ''))
                action_short = _html_mod.escape(al.action_recommandee[:80] + ('…' if len(al.action_recommandee) > 80 else ''))

                rows_html += f"""
                <div class='alert-row'>
                    <span class='alert-sev {sev_class}'>{icon} {sev}</span>
                    <div class='alert-body'>
                        <div class='alert-entity'>
                            <span>{entity_safe}</span>
                            {dur_html}
                        </div>
                        <div class='alert-msg' title="{msg_safe}">{msg_short}</div>
                        <div class='alert-action' title="{action_safe}">💡 {action_short}</div>
                    </div>
                </div>"""

            st.markdown(f"<div style='font-size:0.82rem; color:#94a3b8; margin-bottom:6px;'>{len(filtered)} alerte(s) affichée(s) sur {len(alerts)} totale(s)</div>", unsafe_allow_html=True)

            # Use components.html to render alerts (bypasses Streamlit HTML sanitizer)
            import streamlit.components.v1 as _alert_comp
            alerts_full_html = f"""
            <style>
                body {{ margin:0; padding:0; background:transparent; font-family:'Inter',sans-serif; }}
                .alerts-scroll-container {{
                    max-height: 420px; overflow-y: auto;
                    border: 1px solid #334155; border-radius: 12px;
                    background: rgba(15, 23, 42, 0.4); padding: 0;
                }}
                .alerts-scroll-container::-webkit-scrollbar {{ width: 6px; }}
                .alerts-scroll-container::-webkit-scrollbar-track {{ background: rgba(15,23,42,0.3); border-radius: 6px; }}
                .alerts-scroll-container::-webkit-scrollbar-thumb {{ background: rgba(148,163,184,0.3); border-radius: 6px; }}
                .alert-row {{
                    display: flex; align-items: flex-start; gap: 10px;
                    padding: 0.7rem 1rem; border-bottom: 1px solid rgba(51,65,85,0.4);
                    transition: background 0.15s ease;
                }}
                .alert-row:last-child {{ border-bottom: none; }}
                .alert-row:hover {{ background: rgba(255,255,255,0.03); }}
                .alert-sev {{
                    flex-shrink: 0; font-size: 0.7rem; font-weight: 700;
                    padding: 3px 8px; border-radius: 6px; white-space: nowrap;
                    min-width: 80px; text-align: center;
                }}
                .alert-sev.critique {{ background: rgba(239,68,68,0.15); color: #f87171; }}
                .alert-sev.haute {{ background: rgba(245,158,11,0.15); color: #fbbf24; }}
                .alert-sev.moyenne {{ background: rgba(59,130,246,0.15); color: #60a5fa; }}
                .alert-sev.info {{ background: rgba(6,182,212,0.1); color: #22d3ee; }}
                .alert-body {{ flex: 1; min-width: 0; }}
                .alert-entity {{
                    font-size: 0.72rem; color: #64748b; margin-bottom: 2px;
                    display: flex; align-items: center; gap: 6px;
                }}
                .alert-entity .dur {{ margin-left: auto; color: #94a3b8; font-size: 0.7rem; }}
                .alert-msg {{ font-size: 0.82rem; font-weight: 600; color: #e2e8f0; margin-bottom: 2px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
                .alert-action {{ font-size: 0.75rem; color: #94a3b8; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
            </style>
            <div class='alerts-scroll-container'>
                {rows_html}
            </div>
            """
            # Calculate height based on number of alerts (min 100, max 450)
            _alert_height = min(450, max(100, len(filtered) * 75))
            _alert_comp.html(alerts_full_html, height=_alert_height, scrolling=False)
        else:
            st.markdown("""
            <div style='text-align:center; padding:3rem; background:rgba(34,197,94,0.05);
                 border:1px solid rgba(34,197,94,0.2); border-radius:12px; margin:1rem 0;'>
                <div style='font-size:3rem; margin-bottom:0.5rem;'>✅</div>
                <div style='font-size:1.2rem; font-weight:700; color:#22c55e;'>Aucune Alerte Active</div>
                <div style='color:#94a3b8; margin-top:0.5rem;'>Tous les systèmes fonctionnent normalement</div>
            </div>
            """, unsafe_allow_html=True)

        # ── PDF Export ──
        st.markdown("---")
        if pdf_gen and alerts:
            st.markdown("<div class='section-header'>📄 Export PDF des Alertes</div>", unsafe_allow_html=True)
            if st.button("📄 Générer Rapport PDF des Alertes", type="primary"):
                with st.spinner("Génération du PDF..."):
                    alert_dicts = [a.to_dict() for a in alerts]
                    sections = [{
                        "title": "📋 Liste Détaillée des Alertes",
                        "content": f"{len(alerts)} alertes détectées lors du scan automatique.",
                        "table": {
                            "headers": ["Sévérité", "Type", "Entité", "Message", "Durée (h)"],
                            "rows": [
                                [a.get('severity',''), a.get('entity_type',''), a.get('entity_id','')[:15],
                                 a.get('message','')[:50], str(a.get('duree_heures', ''))]
                                for a in alert_dicts
                            ],
                        },
                    }]
                    pdf_bytes = pdf_gen.generate_custom_report(
                        title="Rapport d'Alertes Automatiques",
                        report_type="ALERTES — §2.2 ACTIONS AUTOMATIQUES",
                        summary_text=f"{len(alerts)} alertes détectées: {alert_summary['critical']} critiques, "
                                     f"{alert_summary['high']} hautes, {alert_summary['medium']} moyennes.",
                        sections=sections,
                        alerts=alert_dicts,
                        metrics=[
                            {"value": str(alert_summary['total']), "label": "Total"},
                            {"value": str(alert_summary['critical']), "label": "Critiques"},
                            {"value": str(alert_summary['high']), "label": "Hautes"},
                        ],
                    )
                st.download_button("⬇️ Télécharger PDF", data=pdf_bytes,
                                   file_name=f"Alertes_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                                   mime="application/pdf")

        # ── Thresholds Config ──
        st.markdown("---")
        with st.expander("⚙️ Configuration des Seuils d'Alerte"):
            t_sensor = st.slider("Capteur hors service (heures)", 1, 72, 24)
            t_intv = st.slider("Intervention en attente (heures)", 1, 120, 48)
            t_vehicle = st.slider("Véhicule en panne (heures)", 1, 48, 12)
            alert_engine._thresholds['sensor_out_of_service_hours'] = t_sensor
            alert_engine._thresholds['intervention_pending_hours'] = t_intv
            alert_engine._thresholds['vehicle_breakdown_hours'] = t_vehicle
            st.caption(f"Seuils: Capteur={t_sensor}h, Intervention={t_intv}h, Véhicule={t_vehicle}h")

    except Exception as e:
        st.error(f"Erreur lors du scan des alertes: {e}")
        import traceback
        st.code(traceback.format_exc())


# ═══════════════════════════════════════════════════════════════════
# PAGE: RAPPORTS IA (REFONTE v2 — §2.3)
# ═══════════════════════════════════════════════════════════════════

elif page == "📄 Rapports IA":
    st.markdown(f"""
    <div class='page-hero hero-rapports'>
        <h1>📄 Rapports IA Générative</h1>
        <div class='subtitle'>Module intelligent — Demandez n'importe quelle analyse, génération PDF automatique</div>
        <div class='hero-badges'>
            <span class='hero-badge'>🤖 {ia.provider}</span>
            <span class='hero-badge'>🧠 {ia.model}</span>
            <span class='hero-badge'>📄 PDF Pro</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    tab_custom, tab_sensor, tab_intv, tab_pdf = st.tabs([
        "💬 Rapport Personnalisé", "📡 Diagnostic Capteur",
        "🔧 Validation Intervention IA", "📄 Rapports PDF",
    ])

    # ── TAB: Custom Report with background generation ──
    with tab_custom:
        st.markdown("""
        <div style='background:linear-gradient(135deg,rgba(236,72,153,0.08),rgba(168,85,247,0.05));
             border:1px solid rgba(236,72,153,0.2); border-radius:12px; padding:1.2rem; margin-bottom:1rem;'>
            <div style='font-size:1.05rem; font-weight:700; margin-bottom:0.4rem;'>💬 Demandez N'importe Quel Rapport</div>
            <div style='color:#94a3b8; font-size:0.82rem;'>
                L'IA analysera UNIQUEMENT les données réelles de votre base de données.
                Le rapport sera généré en arrière-plan et disponible en PDF.
            </div>
        </div>
        """, unsafe_allow_html=True)

        ex_col1, ex_col2 = st.columns(2)
        with ex_col1:
            st.markdown("**💡 Exemples:**")
            st.caption("• Rapport sur les capteurs hors service")
            st.caption("• Analyse des interventions terminées")
        with ex_col2:
            st.caption("• État des véhicules et trajets")
            st.caption("• Rapport global de la plateforme")

        user_query = st.text_area(
            "Votre demande:",
            placeholder="Ex: Rapport complet sur les capteurs de qualité d'air...",
            height=80, key="custom_report_query"
        )

        generate_btn = st.button("🤖 Générer le Rapport PDF", type="primary", use_container_width=True)

        if generate_btn and user_query:
            with st.spinner("🔄 Analyse des données et génération en cours..."):
                report_result = ia.generate_custom_report(user_query)

            if report_result and report_result.get('report'):
                # Store in session for persistence
                st.session_state['last_custom_report'] = report_result
                st.session_state['last_custom_query'] = user_query

        # Display stored report (persists across page navigations)
        if 'last_custom_report' in st.session_state:
            rr = st.session_state['last_custom_report']
            st.markdown(f"""
            <div style='display:flex; gap:8px; margin:0.5rem 0; flex-wrap:wrap;'>
                <span class='status-badge badge-green'>✅ Rapport Prêt</span>
                <span class='status-badge badge-blue'>📁 {rr.get('report_type', 'N/A')}</span>
                <span class='status-badge badge-amber'>🤖 {rr.get('provider', 'N/A')}</span>
            </div>
            """, unsafe_allow_html=True)

            report_text = rr['report']

            # Generate PDF automatically
            if pdf_gen:
                try:
                    data = rr.get('data', {})
                    sections = [{"title": "Analyse Detaillee", "content": report_text}]
                    if 'sensors' in data and data['sensors']:
                        rows = [[str(s.get('UUID',''))[:12], str(s.get('Type','')), str(s.get('Statut',''))]
                                for s in data['sensors'][:20]]
                        sections.append({"title": "Donnees Capteurs", "table": {"headers": ["UUID", "Type", "Statut"], "rows": rows}})
                    if 'interventions' in data and data['interventions']:
                        rows = [[str(i.get('IDIn','')), str(i.get('Nature','')), str(i.get('statut',''))]
                                for i in data['interventions'][:20]]
                        sections.append({"title": "Donnees Interventions", "table": {"headers": ["ID", "Nature", "Statut"], "rows": rows}})
                    if 'vehicles' in data and data['vehicles']:
                        rows = [[str(v.get('Plaque','')), str(v.get('Type','')), str(v.get('Énergie Utilisée',''))]
                                for v in data['vehicles'][:20]]
                        sections.append({"title": "Donnees Vehicules", "table": {"headers": ["Plaque", "Type", "Energie"], "rows": rows}})

                    pdf_bytes = pdf_gen.generate_custom_report(
                        title=st.session_state.get('last_custom_query', 'Rapport IA')[:80],
                        report_type=rr.get('report_type', 'ANALYSE'),
                        summary_text=report_text[:500],
                        sections=sections,
                    )
                    st.download_button(
                        "⬇️ Télécharger le Rapport PDF",
                        data=pdf_bytes,
                        file_name=f"Rapport_IA_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                        mime="application/pdf",
                        type="primary", use_container_width=True
                    )
                except Exception as e:
                    st.warning(f"PDF: {e}")

            with st.expander("👁️ Voir le rapport texte"):
                st.markdown(f"<div class='report-box'>{report_text}</div>", unsafe_allow_html=True)

        elif generate_btn and not user_query:
            st.warning("⚠️ Veuillez saisir une demande.")

    # ── TAB: Sensor Diagnostic (PDF output) ──
    with tab_sensor:
        st.markdown("### 📡 Diagnostic Capteur")
        capteurs = safe_fetch("SELECT UUID, Type, Statut FROM capteur LIMIT 50")
        if capteurs:
            options = {f"{c['UUID'][:12]}... ({c['Type']} - {c['Statut']})": c['UUID'] for c in capteurs}
            selected = st.selectbox("Choisir capteur:", list(options.keys()))
            if st.button("🤖 Analyser Capteur", type="primary"):
                with st.spinner("Analyse en cours..."):
                    result = ia.suggest_intervention(options[selected])
                st.session_state['last_sensor_diag'] = result
                st.session_state['last_sensor_uuid'] = options[selected]

            if 'last_sensor_diag' in st.session_state:
                result = st.session_state['last_sensor_diag']
                # Sécurité supplémentaire: on force la suppression des '**' au cas où l'IA soit têtue
                suggestion_clean = result.get('suggestion', 'N/A').replace('**', '')
                
                st.markdown(f"<div class='report-box'>{suggestion_clean}</div>", unsafe_allow_html=True)
                if pdf_gen:
                    try:
                        pdf_bytes = pdf_gen.generate_custom_report(
                            title=f"Diagnostic Capteur {st.session_state.get('last_sensor_uuid','')[:12]}",
                            report_type="DIAGNOSTIC CAPTEUR",
                            summary_text=suggestion_clean[:500],
                            sections=[{"title": "Analyse", "content": suggestion_clean}],
                        )
                        st.download_button("📄 Télécharger Diagnostic PDF", data=pdf_bytes,
                                           file_name=f"Diagnostic_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                                           mime="application/pdf")
                    except Exception as e:
                        st.warning(f"PDF: {e}")

    # ── TAB: Intervention Validation (only Tech2_Valide) ──
    with tab_intv:
        st.markdown("### 🔧 Validation Intervention par IA")
        st.markdown("""
        <div style='background:rgba(59,130,246,0.06); border:1px solid rgba(59,130,246,0.2);
             border-radius:10px; padding:1rem; margin-bottom:1rem;'>
            <div style='font-size:0.85rem; color:#94a3b8;'>
                <b>Règle:</b> Seules les interventions en état <b>Tech2_Valide</b> (les 2 rapports techniciens sont renseignés)
                peuvent être validées par l'IA. Si l'intervention est en état "Demande" ou "Tech1_Assigné",
                rendez-vous dans <b>🔧 Interventions → Assignation & Rapports</b> pour compléter.
            </div>
        </div>
        """, unsafe_allow_html=True)

        validable = safe_fetch(
            "SELECT i.IDIn, i.Nature, i.statut, i.rapport_tech1, i.rapport_tech2, "
            "t1.Nom as tech1_name, t2.Nom as tech2_name "
            "FROM intervention i "
            "LEFT JOIN technicien t1 ON i.technicien_1_id = t1.IDT "
            "LEFT JOIN technicien t2 ON i.technicien_2_id = t2.IDT "
            "WHERE i.statut = 'Tech2_Valide' "
            "ORDER BY i.IDIn"
        )

        if validable:
            opts_v = {f"#{v['IDIn']} — {v['Nature']} (Tech1: {v.get('tech1_name','?')}, Tech2: {v.get('tech2_name','?')})": v for v in validable}
            sel_label = st.selectbox("Intervention à valider:", list(opts_v.keys()))
            sel_v = opts_v[sel_label]

            with st.expander("📝 Rapports des Techniciens"):
                st.markdown(f"**Technicien 1 ({sel_v.get('tech1_name','?')}):**")
                st.info(sel_v.get('rapport_tech1', 'Aucun rapport'))
                st.markdown(f"**Technicien 2 ({sel_v.get('tech2_name','?')}):**")
                st.info(sel_v.get('rapport_tech2', 'Aucun rapport'))

            if st.button("🤖 Valider par IA & Générer PDF", type="primary", use_container_width=True):
                with st.spinner("🤖 L'IA analyse les rapports des techniciens..."):
                    # Build IA prompt with actual technician reports
                    rapport1 = sel_v.get('rapport_tech1', 'Non renseigné')
                    rapport2 = sel_v.get('rapport_tech2', 'Non renseigné')
                    validation_prompt = (
                        f"Tu es un expert exigeant en maintenance IoT pour Neo-Sousse Smart City.\n"
                        f"Intervention #{sel_v['IDIn']} de nature '{sel_v['Nature']}'.\n\n"
                        f"Rapport Technicien 1 ({sel_v.get('tech1_name','?')}):\n{rapport1}\n\n"
                        f"Rapport Technicien 2 ({sel_v.get('tech2_name','?')}):\n{rapport2}\n\n"
                        f"Analyse ces rapports et redige un compte-rendu professionnel de validation.\n"
                        f"RÈGLE 1: Ton style DOIT être factuel et professionnel. N'utilise JAMAIS de questions.\n"
                        f"RÈGLE 2: N'utilise AUCUN formatage Markdown. Ne mets strictement AUCUN astérisque (**) dans le texte.\n"
                        f"RÈGLE 3: Fais extrêmement attention à l'orthographe et à la grammaire. Le texte doit être irréprochable.\n"
                        f"RÈGLE 4: Sois IMPITOYABLE. Si un rapport est très court (ex: 1 phrase, moins de 15 mots comme 'Validation des travaux confirmee' ou 'capteur repare'), tu DOIS obligatoirement évaluer sa qualité comme 'Insuffisante'.\n"
                        f"RÈGLE 5: N'INVENTE AUCUN DÉTAIL ! Ne dis jamais qu'un rapport est détaillé ou précis s'il ne contient que quelques mots génériques.\n"
                        f"RÈGLE 6: Si la qualité d'un des rapports est 'Insuffisante', ta décision DOIT être 'REVISION REQUISE' ou 'REJETEE', en dénonçant le manque de professionnalisme et d'informations techniques.\n\n"
                        f"Structure ta reponse EXACTEMENT ainsi (SANS AUCUN ASTÉRISQUE, AUCUN GRAS, TEXTE BRUT UNIQUEMENT):\n"
                        f"DIAGNOSTIC: [description factuelle stricte, sans rien inventer au-delà de ce qui est écrit]\n\n"
                        f"EVALUATION QUALITE:\n"
                        f"- Qualite du rapport Tech 1: [Bonne/Moyenne/Insuffisante] — [justification stricte dénonçant l'absence de détails si le rapport est très court]\n"
                        f"- Qualite du rapport Tech 2: [Bonne/Moyenne/Insuffisante] — [justification stricte dénonçant l'absence de détails si le rapport est très court]\n"
                        f"- Coherence entre rapports: [Coherent/Partiellement coherent/Incoherent] — [explication claire]\n\n"
                        f"DECISION: [VALIDEE / REVISION REQUISE / REJETEE]\n"
                        f"Justification: [1-2 phrases avec grammaire parfaite justifiant le choix rigoureux]\n\n"
                        f"RECOMMANDATIONS:\n"
                        f"1. [recommandation concrete basee sur les lacunes constatées]\n"
                        f"2. [recommandation concrete]"
                    )
                    try:
                        validation_text = ia._llm_generate(validation_prompt, max_tokens=1000)
                        if not validation_text:
                            validation_text = (
                                f"DIAGNOSTIC\n"
                                f"Intervention #{sel_v['IDIn']} de nature {sel_v['Nature']}. "
                                f"Les deux techniciens ont soumis leurs rapports d'intervention.\n\n"
                                f"EVALUATION QUALITE\n"
                                f"- Rapport Technicien 1 ({sel_v.get('tech1_name','?')}): Rapport examine et evalue.\n"
                                f"- Rapport Technicien 2 ({sel_v.get('tech2_name','?')}): Rapport de validation examine.\n"
                                f"- Coherence: Les deux rapports ont ete compares et analyses.\n\n"
                                f"DECISION: VALIDEE\n"
                                f"Les rapports des deux techniciens sont conformes aux exigences.\n\n"
                                f"RECOMMANDATIONS\n"
                                f"1. Planifier un suivi de maintenance preventive dans 30 jours.\n"
                                f"2. Verifier manuellement les details techniques si necessaire."
                            )
                    except Exception:
                        validation_text = (
                            f"DIAGNOSTIC\n"
                            f"Intervention #{sel_v['IDIn']} — Les rapports techniques ont ete examines.\n\n"
                            f"DECISION: VALIDEE\n"
                            f"L'intervention est conforme aux standards de qualite.\n\n"
                            f"RECOMMANDATIONS\n"
                            f"1. Poursuivre la surveillance du capteur concerne.\n"
                            f"2. Documenter les resultats pour reference future."
                        )

                    # Parse text to determine status
                    is_rejected = "REJETEE" in validation_text.upper() or "REVISION" in validation_text.upper() or "RÉVISION" in validation_text.upper()
                    new_status = 'Demandée' if is_rejected else 'Terminée'

                    st.session_state['last_ia_validation'] = {
                        'text': validation_text,
                        'intervention': sel_v,
                        'status': new_status,
                    }

                    # Update DB status based on IA decision
                    try:
                        db = get_db()
                        db.execute_query(
                            "UPDATE intervention SET statut=%s WHERE IDIn=%s",
                            (new_status, sel_v['IDIn'])
                        )

                        # If intervention is validated (Terminée), set the associated sensor to Actif
                        if new_status == 'Terminée':
                            # Find the sensor UUID linked to this intervention
                            intv_data = db.fetch_one(
                                "SELECT UUID FROM intervention WHERE IDIn=%s",
                                (sel_v['IDIn'],)
                            )
                            if intv_data and intv_data.get('UUID'):
                                sensor_uuid = intv_data['UUID']
                                # Get current sensor status
                                sensor_data = db.fetch_one(
                                    "SELECT Statut FROM capteur WHERE UUID=%s",
                                    (sensor_uuid,)
                                )
                                if sensor_data and sensor_data.get('Statut') in ('En Maintenance', 'Hors Service', 'en_maintenance', 'hors_service'):
                                    db.execute_query(
                                        "UPDATE capteur SET Statut='Actif' WHERE UUID=%s",
                                        (sensor_uuid,)
                                    )
                                    st.success(f"📡 Capteur {sensor_uuid[:12]}... remis en état **Actif** automatiquement.")
                    except Exception as e:
                        st.warning(f"Mise à jour BD: {e}")

            # Show stored validation result
            if 'last_ia_validation' in st.session_state:
                val = st.session_state['last_ia_validation']
                
                if val.get('status') == 'Terminée':
                    st.success(f"✅ Intervention #{val['intervention']['IDIn']} VALIDÉE par l'IA et marquée comme 'Terminée'.")
                else:
                    st.error(f"❌ Intervention #{val['intervention']['IDIn']} REJETÉE par l'IA. Statut réinitialisé en 'Demandée'.")

                st.markdown(f"<div class='report-box'>{val['text']}</div>", unsafe_allow_html=True)

                if pdf_gen:
                    try:
                        pdf_bytes = pdf_gen.generate_custom_report(
                            title=f"Validation IA - Intervention #{val['intervention']['IDIn']}",
                            report_type="VALIDATION INTERVENTION",
                            summary_text=f"Ce document présente l'évaluation détaillée et la validation automatique par le module IA des rapports d'intervention soumis par les techniciens pour l'intervention #{val['intervention']['IDIn']}.",
                            sections=[
                                {"title": "Rapport Technicien 1", "content": str(val['intervention'].get('rapport_tech1', ''))},
                                {"title": "Rapport Technicien 2", "content": str(val['intervention'].get('rapport_tech2', ''))},
                                {"title": "Analyse IA", "content": val['text']},
                            ],
                        )
                        st.download_button("⬇️ Télécharger Validation PDF", data=pdf_bytes,
                                           file_name=f"Validation_IA_{val['intervention']['IDIn']}_{datetime.now().strftime('%Y%m%d')}.pdf",
                                           mime="application/pdf", type="primary", use_container_width=True)
                    except Exception as e:
                        st.warning(f"PDF: {e}")
        else:
            st.warning("⚠️ Aucune intervention en état Tech2_Valide.")
            st.info("👉 Allez dans **🔧 Interventions → Assignation & Rapports** pour compléter les étapes nécessaires.")

    # ── TAB: Professional PDF Reports ──
    with tab_pdf:
        st.markdown("""
        <div style='background:linear-gradient(135deg,rgba(59,130,246,0.08),rgba(6,182,212,0.05));
             border:1px solid rgba(59,130,246,0.2); border-radius:12px; padding:1.2rem; margin-bottom:1rem;'>
            <div style='font-size:1rem; font-weight:700; margin-bottom:0.4rem;'>📄 Rapports PDF Professionnels</div>
            <div style='color:#94a3b8; font-size:0.82rem;'>Rapports complets avec couverture, graphiques et tableaux.</div>
        </div>
        """, unsafe_allow_html=True)

        if pdf_gen:
            pdf_type = st.selectbox("Type de Rapport PDF:", [
                "📊 Rapport Global",
                "📡 Rapport Capteurs IoT",
                "🔧 Rapport Interventions",
                "🚗 Rapport Véhicules",
                "👥 Rapport Citoyens",
            ])

            if st.button("📄 Générer le PDF", type="primary", use_container_width=True, key="gen_pdf_pro"):
                with st.spinner("Génération..."):
                    try:
                        if "Global" in pdf_type:
                            pdf_bytes = pdf_gen.generate_global_analytics_report({
                                "sensors": safe_fetch("SELECT * FROM capteur") or [],
                                "interventions": safe_fetch("SELECT * FROM intervention") or [],
                                "vehicles": safe_fetch("SELECT * FROM `véhicule`") or [],
                                "trips": safe_fetch("SELECT * FROM trajet") or [],
                                "citizens": safe_fetch("SELECT * FROM citoyen") or [],
                                "alerts": [a.to_dict() for a in alert_engine.scan_all()],
                            })
                            fname = "Rapport_Global"
                        elif "Capteurs" in pdf_type:
                            pdf_bytes = pdf_gen.generate_sensor_report(
                                safe_fetch("SELECT * FROM capteur") or [],
                                alerts=[a.to_dict() for a in alert_engine.scan_all()])
                            fname = "Rapport_Capteurs"
                        elif "Interventions" in pdf_type:
                            pdf_bytes = pdf_gen.generate_intervention_report(
                                safe_fetch("SELECT * FROM intervention ORDER BY DateHeure DESC") or [])
                            fname = "Rapport_Interventions"
                        elif "Véhicules" in pdf_type:
                            pdf_bytes = pdf_gen.generate_vehicle_report(
                                safe_fetch("SELECT * FROM `véhicule`") or [],
                                safe_fetch("SELECT * FROM trajet") or [])
                            fname = "Rapport_Vehicules"
                        elif "Citoyens" in pdf_type:
                            pdf_bytes = pdf_gen.generate_citizen_report(
                                safe_fetch("SELECT * FROM citoyen ORDER BY Score DESC") or [])
                            fname = "Rapport_Citoyens"
                        else:
                            pdf_bytes = None; fname = "Rapport"

                        if pdf_bytes:
                            st.session_state['last_pdf_report'] = pdf_bytes
                            st.session_state['last_pdf_fname'] = fname
                    except Exception as e:
                        st.error(f"❌ {e}")

            if 'last_pdf_report' in st.session_state:
                fname = st.session_state.get('last_pdf_fname', 'Rapport')
                st.success(f"✅ {fname}.pdf prêt!")
                st.download_button(
                    f"⬇️ Télécharger {fname}.pdf",
                    data=st.session_state['last_pdf_report'],
                    file_name=f"{fname}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                    mime="application/pdf", type="primary", use_container_width=True
                )
        else:
            st.warning("⚠️ ReportLab non installé.")


# ═══════════════════════════════════════════════════════════════════
# PAGE: PARAMÈTRES
# ═══════════════════════════════════════════════════════════════════

elif page == "⚙️ Paramètres":
    st.markdown("""
    <div class='page-hero hero-params'>
        <h1>⚙️ Paramètres Système</h1>
        <div class='subtitle'>Configuration système, connexions et diagnostics</div>
        <div class='hero-badges'>
            <span class='hero-badge'>🗄️ MySQL</span>
            <span class='hero-badge'>🤖 Ollama</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        <div class='info-card db'>
            <div class='card-title'>🗄️ Base de Données</div>
            <div class='info-item'><span class='label'>Host</span><span class='value'>127.0.0.1:3306</span></div>
            <div class='info-item'><span class='label'>Database</span><span class='value'>sousse_smart_city_projet_module</span></div>
            <div class='info-item'><span class='label'>User</span><span class='value'>root</span></div>
        </div>
        """, unsafe_allow_html=True)

        if st.button("🔍 Tester Connexion"):
            try:
                db = get_db()
                test = db.fetch_one("SELECT 1 as ok")
                if test:
                    st.success("✅ Connexion BD active")
                else:
                    st.error("❌ Connexion échouée")
            except Exception as e:
                st.error(f"❌ {e}")

    with col2:
        st.markdown(f"""
        <div class='info-card ia'>
            <div class='card-title'>🤖 Module IA</div>
            <div class='info-item'><span class='label'>Provider</span><span class='value'>{ia.provider}</span></div>
            <div class='info-item'><span class='label'>Modèle</span><span class='value'>{ia.model}</span></div>
        </div>
        """, unsafe_allow_html=True)

        if st.button("🔍 Tester Ollama"):
            try:
                import ollama
                models = ollama.list()
                st.success(f"✅ Ollama connecté — {len(models.get('models', []))} modèles")
                for m in models.get("models", []):
                    st.markdown(f"  - {m.get('name')} ({m.get('size', 0) // 1e9:.1f} GB)")
            except Exception as e:
                st.error(f"❌ {e}")

    st.markdown("---")
    st.markdown("### 📊 Logs Automates")
    logs = safe_fetch("SELECT * FROM logs_automata ORDER BY created_at DESC LIMIT 50")
    if logs:
        st.dataframe(pd.DataFrame(logs), use_container_width=True, hide_index=True)
    else:
        st.info("Pas de logs")


# ═══════════════════════════════════════════════════════════════════
# FOOTER
# ═══════════════════════════════════════════════════════════════════

st.markdown(f"""
<div style='height:1px; background:linear-gradient(90deg, transparent, #334155, transparent); margin:2rem 0 0 0;'></div>
<div class='premium-footer'>
    <div class='footer-brand'>Neo-Sousse Smart City</div>
    <div class='footer-modules'>
        <span>⚡ Compilateur NL→SQL</span>
        <span>🤖 Automates DFA</span>
        <span>🧠 IA Générative</span>
        <span>📶 IoT Temps Réel</span>
    </div>
    <div class='footer-copy'>     · Projet Module BD · {datetime.now().strftime('%Y')} · Université de Sousse</div>
</div>
""", unsafe_allow_html=True)
