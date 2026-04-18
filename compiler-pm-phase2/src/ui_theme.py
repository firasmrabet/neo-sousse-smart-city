"""
UI Theme helpers for Streamlit app
Provides dark and light palettes and injects CSS for improved layout
"""
from typing import Dict
import streamlit as st


PALETTES = {
    "dark_teal": {
        "bg": "#0f1724",
        "card": "#0b1220",
        "muted": "#94a3b8",
        "accent": "#06b6d4",
        "success": "#10b981",
        "danger": "#ef4444",
        "surface": "#0b1220",
        "text": "#e6eef6"
    },
    "light_blue": {
        "bg": "#f7fbff",
        "card": "#ffffff",
        "muted": "#6b7280",
        "accent": "#0ea5e9",
        "success": "#059669",
        "danger": "#dc2626",
        "surface": "#ffffff",
        "text": "#0b1220"
    }
    ,
    "creative_aurora": {
        "bg": "#060816",
        "card": "#071428",
        "muted": "#9aa7bf",
        "accent": "#7c3aed",
        "accent2": "#06b6d4",
        "success": "#34d399",
        "danger": "#fb7185",
        "surface": "#071428",
        "text": "#e7f0ff"
    }
}


def init_theme(default: str = "creative_aurora"):
    if "theme_mode" not in st.session_state:
        st.session_state.theme_mode = default


def toggle_theme():
    # Cycle between creative and light for simplicity
    current = st.session_state.get("theme_mode", "creative_aurora")
    if current == "creative_aurora":
        st.session_state.theme_mode = "light_blue"
    else:
        st.session_state.theme_mode = "creative_aurora"


def get_palette() -> Dict[str, str]:
    mode = st.session_state.get("theme_mode", "dark_teal")
    return PALETTES.get(mode, PALETTES["dark_teal"])


def inject_base_css():
    p = get_palette()
    css = f"""
    <style>
        :root {{
            --bg: {p['bg']};
            --card: {p['card']};
            --muted: {p['muted']};
            --accent: {p.get('accent','')};
            --accent2: {p.get('accent2','"#06b6d4"')};
            --success: {p['success']};
            --danger: {p['danger']};
            --surface: {p['surface']};
            --text: {p['text']};
        }}
        html, body {{background: linear-gradient(180deg, rgba(10,12,30,1) 0%, rgba(6,8,22,1) 40%);}}
        .stApp {{ background: linear-gradient(120deg, rgba(7,20,40,0.9), rgba(8,10,28,0.95)); color: var(--text) }}
        .tl-card {{
            background: linear-gradient(180deg, rgba(255,255,255,0.02), rgba(255,255,255,0.01));
            border-radius: 14px;
            padding: 18px;
            color: var(--text);
            box-shadow: 0 10px 30px rgba(2,6,23,0.6);
            border: 1px solid rgba(255,255,255,0.03);
            backdrop-filter: blur(6px);
        }}
        .tl-badge {{
            display:inline-block;padding:8px 14px;border-radius:999px;background:linear-gradient(90deg,var(--accent), var(--accent2));color:#fff;font-weight:700;font-size:12px;box-shadow:0 6px 18px rgba(124,58,237,0.18)
        }}
        .tl-metric-title{{color:var(--muted);font-size:12px;text-transform:uppercase;letter-spacing:0.8px}}
        .tl-metric-value{{color:var(--text);font-size:28px;font-weight:800}}
        .tl-section-title{{color:var(--accent);font-weight:800;font-size:16px}}
        .ia-report-pre{{background:rgba(255,255,255,0.02);padding:14px;border-radius:8px;color:var(--text);font-family:ui-monospace, SFMono-Regular, Menlo, Monaco, monospace;white-space:pre-wrap}}
        .highlight-ok{{color:var(--success);font-weight:800}}
        .highlight-bad{{color:var(--danger);font-weight:800}}
        .tl-metric-grid {{display:flex;gap:12px}}
        @media (max-width: 768px) {{ .tl-card {{ padding:12px }} .tl-metric-value{{font-size:20px}} }}
        /* Card header */
        .tl-card-header{{display:flex;justify-content:space-between;align-items:center;margin-bottom:10px}}
        .tl-card-title{{font-size:16px;font-weight:800;color:var(--text)}}
        .tl-card-sub{{color:var(--muted);font-size:12px}}

        /* Buttons */
        .tl-ghost-btn{{background:transparent;border:1px solid rgba(255,255,255,0.06);color:var(--text);padding:8px 12px;border-radius:10px;cursor:pointer;transition:all .16s ease}}
        .tl-ghost-btn:hover{{transform:translateY(-2px);box-shadow:0 8px 20px rgba(2,6,23,0.45)}}
        .tl-primary-btn{{background:linear-gradient(90deg,var(--accent),var(--accent2));border:none;color:#fff;padding:8px 14px;border-radius:10px;cursor:pointer;transition:all .16s ease}}
        .tl-primary-btn:hover{{filter:brightness(1.03);transform:translateY(-2px)}}

        /* subtle animations */
        .tl-card{{transition:transform .2s ease, box-shadow .2s ease}}
        .tl-card:hover{{transform:translateY(-6px);box-shadow:0 20px 45px rgba(2,6,23,0.65)}}

        /* report area scrolling */
        .ia-report-pre{{max-height:360px;overflow:auto;padding:14px}}

        /* small legend */
        .tl-legend{{display:flex;gap:12px;align-items:center;color:var(--muted);font-size:13px}}
        .tl-dot{{width:10px;height:10px;border-radius:10px;display:inline-block}}
        .tl-dot.ok{{background:var(--success)}}
        .tl-dot.warn{{background:#f59e0b}}
        .tl-dot.err{{background:var(--danger)}}
        </style>
    """
    st.markdown(css, unsafe_allow_html=True)
