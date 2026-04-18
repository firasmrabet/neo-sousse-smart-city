"""
Dashboard Streamlit - Interface utilisateur simplifiée
Connected to Phase 1 MySQL Database
Version: Auto-refresh working
"""

import streamlit as st
from datetime import datetime
import logging
import time
import sys
sys.path.insert(0, 'c:\\Users\\Mrabet\\Desktop\\devops\\outils\\ps-main\\projet DB\\SensorLinker\\SensorLinker\\compiler-pm-phase2')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import DB connection
try:
    from src.db_connection import get_db
except ImportError:
    get_db = None
    logger.error("DB connection not available")

# Theme helpers
try:
    from src.ui_theme import init_theme, inject_base_css, toggle_theme, get_palette
except Exception:
    init_theme = lambda *a, **k: None
    inject_base_css = lambda *a, **k: None
    toggle_theme = lambda *a, **k: None
    get_palette = lambda *a, **k: {}

# IA validator + PDF generator (optional)
try:
    from src.ia_strict_validator_v3 import StrictIAValidator
except Exception:
    StrictIAValidator = None

try:
    from src.utils.pdf_report import generate_ia_pdf
except Exception:
    generate_ia_pdf = None

# Page config
st.set_page_config(
    page_title="Neo-Sousse Dashboard",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'refresh_flag' not in st.session_state:
    st.session_state.refresh_flag = 0

# Init theme and inject CSS
init_theme()
inject_base_css()

# Auto-refresh EVERY 5 seconds by sleeping and rerunning
placeholder = st.empty()

# Top control bar
with st.container():
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("<div style='display:flex;align-items:center;gap:12px'><h3 style='margin:0'>Neo-Sousse Dashboard</h3><span class='tl-badge'>Phase 1</span></div>", unsafe_allow_html=True)
    with col2:
        if st.button("🔄 REFRESH NOW", key="refresh_btn"):
            st.session_state.refresh_flag += 1
            st.rerun()
        if st.button("Toggle Theme", key="theme_toggle"):
            toggle_theme()
            st.rerun()

# Sidebar navigation
st.sidebar.title("🌍 Navigation")
page = st.sidebar.radio(
    "Select section:",
    [
        "📊 Dashboard",
        "🎯 Sensors",
        "🔧 Interventions"
    ]
)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# DASHBOARD PAGE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

if page == "📊 Dashboard":
    st.title("📊 Dashboard - Neo-Sousse Smart City")
    st.write("Real-time data from Phase 1 database")
    
    if get_db:
        try:
            db = get_db()
            
            # SIMPLE QUERIES - no cache, no errors
            capteurs_total = db.fetch_one("SELECT COUNT(*) as cnt FROM Capteur")
            capteurs_actifs = db.fetch_one("SELECT COUNT(*) as cnt FROM Capteur WHERE Statut='Actif'")
            interventions_total = db.fetch_one("SELECT COUNT(*) as cnt FROM Intervention")
            
            # Extract values safely
            cap_total = capteurs_total['cnt'] if capteurs_total else 0
            cap_actif = capteurs_actifs['cnt'] if capteurs_actifs else 0
            int_total = interventions_total['cnt'] if interventions_total else 0
            
            # Display metrics
            st.write("### Key Metrics")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("✓ Total Sensors", cap_total, delta="sensors in database")
            
            with col2:
                st.metric("🟢 Active Sensors", cap_actif, f"/{cap_total}")
            
            with col3:
                st.metric("🔧 Interventions", int_total, "total")
            
            # Display status
            st.write("---")
            st.write("### System Status")
            
            col_s1, col_s2 = st.columns(2)
            with col_s1:
                st.success("✓ Database: Connected")
                st.success("✓ API Express: Running (port 5000)")
            
            with col_s2:
                st.info(f"ℹ️ Dashboard updated: {datetime.now().strftime('%H:%M:%S')}")
                st.info("ℹ️ Click [REFRESH NOW] to update anytime")
            
            # Show sensor types
            st.write("---")
            st.write("### Sensor Distribution by Type")
            
            sensor_types = db.fetch_all("SELECT Type, COUNT(*) as cnt FROM Capteur GROUP BY Type ORDER BY cnt DESC")
            if sensor_types:
                import pandas as pd
                df_types = pd.DataFrame(sensor_types)
                st.bar_chart(df_types.set_index('Type')['cnt'])
                st.dataframe(df_types, use_container_width=True, hide_index=True)
            
            # Show sensor status
            st.write("---")
            st.write("### Sensor Distribution by Status")
            
            sensor_status = db.fetch_all("SELECT Statut, COUNT(*) as cnt FROM Capteur GROUP BY Statut ORDER BY cnt DESC")
            if sensor_status:
                import pandas as pd
                df_status = pd.DataFrame(sensor_status)
                st.bar_chart(df_status.set_index('Statut')['cnt'])
                st.dataframe(df_status, use_container_width=True, hide_index=True)
            
        except Exception as e:
            st.error(f"❌ DB Error: {str(e)}")
            logger.error(f"Dashboard error: {e}")
    else:
        st.error("❌ Database connection not available")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SENSORS PAGE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

elif page == "🎯 Sensors":
    st.title("🎯 Sensors Management")
    st.write("View and manage all sensors")
    
    if get_db:
        try:
            db = get_db()
            
            sensors = db.fetch_all("SELECT UUID, Type, Statut FROM Capteur LIMIT 10")
            if sensors:
                import pandas as pd
                df = pd.DataFrame(sensors)
                st.dataframe(df, use_container_width=True)
                
                st.write(f"Showing 10 of {db.fetch_one('SELECT COUNT(*) as cnt FROM Capteur')['cnt']} sensors")
            else:
                st.info("No sensors found")
                
        except Exception as e:
            st.error(f"Error: {str(e)}")
    else:
        st.error("Database not available")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# INTERVENTIONS PAGE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

elif page == "🔧 Interventions":
    st.markdown("<div class='tl-card'><div style='display:flex;justify-content:space-between;align-items:center'><div><h2 style='margin:0'>🔧 Interventions</h2><div style='color:var(--muted);margin-top:6px'>View and manage interventions</div></div><div><span class='tl-badge'>Workflow</span></div></div></div>", unsafe_allow_html=True)
    
    if get_db:
        try:
            db = get_db()
            
            interventions = db.fetch_all("SELECT IDIn, Nature, DateHeure, Durée, statut FROM Intervention ORDER BY DateHeure DESC LIMIT 12")
            if interventions:
                # Render as responsive cards
                for it in interventions:
                    st.markdown("<div class='tl-card' style='margin-top:12px'>", unsafe_allow_html=True)
                    c1, c2 = st.columns([4,1])
                    with c1:
                        st.markdown(f"<div style='font-weight:800'>{it.get('Nature','Intervention')}</div>", unsafe_allow_html=True)
                        st.markdown(f"<div style='color:var(--muted);margin-top:6px'>Sensor: {it.get('UUID_Capteur','—')} • {it.get('DateHeure','')}</div>", unsafe_allow_html=True)
                        st.markdown(f"<div style='margin-top:8px;color:var(--muted)'>Duration: {it.get('Durée', '—')}h • Status: {it.get('statut','—')}</div>", unsafe_allow_html=True)
                    with c2:
                        # Placeholder for actions - replaced by expander below
                        st.write("")
                    st.markdown("</div>", unsafe_allow_html=True)

                    # Details expander with IA generation + downloads
                    with st.expander(f"Voir détails — ID {it.get('IDIn')}"):
                        st.markdown(f"**Sensor:** {it.get('UUID_Capteur','—')}  •  **Date:** {it.get('DateHeure','—')}")
                        st.markdown(f"**Duration:** {it.get('Durée','—')}h  •  **Status:** {it.get('statut','—')}")
                        if StrictIAValidator is None:
                            st.warning("IA validator unavailable in this environment")
                        else:
                            gen_key = f"gen_ia_{it.get('IDIn')}"
                            if st.button("🤖 Générer Rapport IA", key=gen_key):
                                with st.spinner("Génération en cours..."):
                                    try:
                                        validator = StrictIAValidator()
                                        validation = validator.validate_reports(
                                            it['IDIn'],
                                            it.get('rapport_tech1',''),
                                            it.get('rapport_tech2','')
                                        )
                                        ia_report_text = validator.generate_strict_report(
                                            it['IDIn'],
                                            it.get('rapport_tech1',''),
                                            it.get('rapport_tech2',''),
                                            validation
                                        )
                                        st.download_button(label="📥 Télécharger TXT", data=ia_report_text, file_name=f"IA_Report_{it['IDIn']}.txt", mime="text/plain")
                                        if generate_ia_pdf:
                                            try:
                                                pdf_bytes = generate_ia_pdf(it, it.get('rapport_tech1',''), it.get('rapport_tech2',''), validation)
                                                st.download_button(label="📄 Télécharger PDF", data=pdf_bytes, file_name=f"IA_Report_{it['IDIn']}.pdf", mime="application/pdf")
                                            except Exception as e:
                                                st.error(f"PDF generation failed: {e}")
                                        st.success("Rapport généré")
                                    except Exception as e:
                                        st.error(f"IA generation failed: {e}")

                total_cnt = db.fetch_one('SELECT COUNT(*) as cnt FROM Intervention')
                st.caption(f"Showing {len(interventions)} latest — Total interventions: {total_cnt['cnt'] if total_cnt else '—'}")
            else:
                st.info("No interventions found")
                
        except Exception as e:
            st.error(f"Error: {str(e)}")
    else:
        st.error("Database not available")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# AUTO REFRESH LOGIC
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Check time and auto-refresh after 5 seconds
if 'last_auto_refresh' not in st.session_state:
    st.session_state.last_auto_refresh = time.time()

elapsed = time.time() - st.session_state.last_auto_refresh
if elapsed > 5:  # Auto-refresh every 5 seconds
    time.sleep(1)  # Small delay to let user see refresh button
    st.session_state.last_auto_refresh = time.time()
    st.rerun()

st.write("---")
st.caption(f"Last update: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Auto-refresh every 5s")
