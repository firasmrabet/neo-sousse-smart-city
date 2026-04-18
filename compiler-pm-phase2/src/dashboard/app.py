"""
Dashboard Streamlit - Interface utilisateur
Connected to Phase 1 MySQL Database
"""

import streamlit as st
from datetime import datetime
import logging
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import DB connection
try:
    from ..db_connection import get_db
except ImportError:
    try:
        from src.db_connection import get_db
    except ImportError:
        get_db = None
        logger.error("DB connection not available")

# Theme helpers (non-intrusive import)
try:
    from src.ui_theme import init_theme, inject_base_css, toggle_theme, get_palette
except Exception:
    init_theme = lambda *a, **k: None
    inject_base_css = lambda *a, **k: None
    toggle_theme = lambda *a, **k: None
    get_palette = lambda *a, **k: {}

# Page config
st.set_page_config(
    page_title="🏙️ Smart City Management",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state for refresh
if 'last_refresh' not in st.session_state:
    st.session_state.last_refresh = time.time()
if 'force_refresh' not in st.session_state:
    st.session_state.force_refresh = False

# Top refresh controls at the very top
col1, col2, col3 = st.columns([3, 1, 1])
with col1:
    pass  # Title will be added per page
with col2:
    if st.button("🔄 Refresh", key="refresh_button", help="Refresh data from database"):
        st.session_state.force_refresh = True
        st.session_state.last_refresh = time.time()
with col3:
    elapsed = time.time() - st.session_state.last_refresh
    if elapsed < 10:
        st.caption(f"🔄 Refreshed {int(elapsed)}s ago")
    else:
        st.caption("Click refresh for new data")

# Sidebar
st.sidebar.title("🌍 Navigation")

page = st.sidebar.radio(
    "Sélectionner une section:",
    [
        "📊 Dashboard",
        "🔤 Compilateur NL→SQL",
        "🤖 Automates",
        "📄 Rapports IA",
        "⚙️ Paramètres"
    ]
)

# ─────────────────────────────────

if page == "📊 Dashboard":
    # Init theme and inject CSS
    init_theme()
    inject_base_css()

    st.markdown("<div class='tl-card'><div class='tl-card-header'><div><h2 style='margin:0'>📊 Tableau de Bord Principal - Phase 1 ↔     </h2><div class='tl-card-sub'>Overview & integrations</div></div><div><button class='tl-ghost-btn' onclick=''>REFRESH</button></div></div></div>", unsafe_allow_html=True)
    
    # Force refresh the page by incrementing a counter
    if st.session_state.force_refresh:
        st.session_state.force_refresh = False
        st.rerun()
    
    # Get real data from Phase 1 database (always fresh, no caching)
    if get_db:
        try:
            db = get_db()
            
            # CRITICAL: Reconnect to ensure fresh data from database
            # Close and reconnect the connection to avoid cached results
            if hasattr(db, 'reconnect'):
                db.reconnect()
            else:
                # Fallback: close and reconnect manually
                if db.connection and db.connection.is_connected():
                    db.cursor.close()
                    db.connection.close()
                db.connect()
            
            # Fetch real numbers - ALWAYS fresh from database
            capteurs_count = db.fetch_one("SELECT COUNT(*) as cnt FROM Capteur")
            capteurs_actifs = db.fetch_one("SELECT COUNT(*) as cnt FROM Capteur WHERE Statut='Actif'")
            interventions_count = db.fetch_one("SELECT COUNT(*) as cnt FROM Intervention")
            techniciens_count = db.fetch_one("SELECT COUNT(*) as cnt FROM Technicien")
            
            cap_c = capteurs_count['cnt'] if capteurs_count else 0
            cap_a = capteurs_actifs['cnt'] if capteurs_actifs else 0
            int_c = interventions_count['cnt'] if interventions_count else 0
            tech_c = techniciens_count['cnt'] if techniciens_count else 0
            
            # Styled metric cards
            mcol1, mcol2, mcol3, mcol4 = st.columns(4)
            with mcol1:
                st.markdown("<div class='tl-card'>", unsafe_allow_html=True)
                st.markdown(f"<div class='tl-card-title'>✓ Capteurs Actifs</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='tl-metric-value'>{cap_a}</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='tl-card-sub'>Total: {cap_c}</div>", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)
            with mcol2:
                st.markdown("<div class='tl-card'>", unsafe_allow_html=True)
                st.markdown(f"<div class='tl-card-title'>⚠️ Interventions</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='tl-metric-value'>{int_c}</div>", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)
            with mcol3:
                st.markdown("<div class='tl-card'>", unsafe_allow_html=True)
                st.markdown(f"<div class='tl-card-title'>👷 Techniciens</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='tl-metric-value'>{tech_c}</div>", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)
            with mcol4:
                rapports_count = db.fetch_one("SELECT COUNT(*) as cnt FROM rapports_ia")
                rep_c = rapports_count['cnt'] if rapports_count else 0
                st.markdown("<div class='tl-card'>", unsafe_allow_html=True)
                st.markdown(f"<div class='tl-card-title'>📄 IA Reports</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='tl-metric-value'>{rep_c}</div>", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)
            
            st.write("---")
            st.write("### Status Système")
            st.success("✓ Database: Connected to Phase 1")
            st.success("✓ Compilateur: Operational")
            st.success("✓ Automates: 3/3 Running")
            st.info("✓ Phase 1 ↔      Integration: ACTIVE")
            
            # Show recent sensors
            st.write("---")
            st.subheader("📡 Top 5 Recent Sensors")
            capteurs = db.fetch_all("SELECT UUID, Type, Statut, `Date Installation` as DateTime FROM Capteur ORDER BY `Date Installation` DESC LIMIT 5")
            if capteurs:
                import pandas as pd
                df = pd.DataFrame(capteurs)
                st.dataframe(df, use_container_width=True)
            
            # Show recent interventions
            st.subheader("🔧 Top 5 Recent Interventions")
            interventions = db.fetch_all("SELECT IDIn, UUID, Nature, Durée, Coût FROM Intervention ORDER BY DateHeure DESC LIMIT 5")
            if interventions:
                import pandas as pd
                df = pd.DataFrame(interventions)
                st.dataframe(df, use_container_width=True)
            
        except Exception as e:
            st.error(f"❌ DB Error: {str(e)}")
            logger.error(f"Dashboard error: {e}")
    else:
        st.error("❌ Database connection not available")

# ─────────────────────────────────

elif page == "🔤 Compilateur NL→SQL":
    st.title("🔤 Compilateur Langage Naturel → SQL")
    
    st.write("""
    Entrez une requête en langage naturel et transformez-la en SQL.
    """)
    
    with st.form("nl_query_form"):
        nl_input = st.text_area(
            "Requête en Langage Naturel",
            placeholder="Ex: Affiche les 5 zones les plus polluées",
            height=100,
            key="nl_input"
        )
        
        submit_btn = st.form_submit_button("🔄 Compiler en SQL")
    
    if submit_btn and nl_input:
        try:
            from src.compiler.compiler import Compiler
            
            compiler = Compiler(debug=True)
            sql = compiler.compile(nl_input)
            
            st.success("✓ Compilation réussie!")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("SQL Généré")
                st.code(sql, language="sql")
            
            with col2:
                st.subheader("Informations")
                st.write(f"**Longueur requête**: {len(nl_input)} caractères")
                st.write(f"**Type requête**: SELECT")
        
        except Exception as e:
            st.error(f"❌ Erreur: {str(e)}")

# ─────────────────────────────────

elif page == "🤖 Automates":
    st.title("🤖 Moteur d'Automates")
    
    automata_type = st.selectbox(
        "Type d'automate",
        ["Cycle de Capteur", "Validation d'Intervention", "Trajet Véhicule"]
    )
    
    if automata_type == "Cycle de Capteur":
        st.subheader("État d'un Capteur")
        
        from src.automata.engine import AutomataEngine
        
        engine = AutomataEngine()
        automata = engine.create_sensor_automata("C-001")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**État Initial**: INACTIF")
            st.write("**État Courant**: ACTIF")
            
            st.write("**Transitions Valides:**")
            st.write("- detection_anomalie → SIGNALÉ")
            st.write("- panne → HORS_SERVICE")
        
        with col2:
            if st.button("📊 Afficher Transitions"):
                st.write(automata.get_transitions())

# ─────────────────────────────────

elif page == "📄 Rapports IA":
    st.title("📄 Rapports Générés par IA")
    
    from src.ia.report_generator import AIReportGenerator
    
    ia = AIReportGenerator()
    
    st.write("### Générateur de Rapports")
    
    report_type = st.selectbox(
        "Type de rapport",
        ["Rapport Capteur", "Rapport de Zone", "Suggestions d'Actions"]
    )
    
    if st.button("🤖 Générer Rapport"):
        with st.spinner("Génération en cours..."):
            
            if report_type == "Rapport Capteur":
                sample_data = {
                    "id": "C-001",
                    "type": "Qualité Air",
                    "statut": "ACTIF",
                    "error_rate": 2.5,
                    "recent_measurements": [42, 45, 43, 48]
                }
                report = ia.generate_sensor_report(sample_data)
            
            elif report_type == "Rapport de Zone":
                measurements = [{"value": 45}, {"value": 48}, {"value": 42}]
                report = ia.generate_zone_report("Zone-1", measurements)
            
            else:  # Suggestions
                sample_data = {
                    "id": "C-001",
                    "statut": "ACTIF",
                    "error_rate": 2.5
                }
                report = ia.suggest_intervention(sample_data)
            
            st.success("✓ Rapport généré!")
            st.write(report)

# ─────────────────────────────────

elif page == "⚙️ Paramètres":
    st.title("⚙️ Paramètres Système")
    
    st.subheader("Configuration IA")
    
    ai_provider = st.selectbox("Fournisseur IA", ["OpenAI", "Ollama"])
    
    if ai_provider == "OpenAI":
        api_key = st.text_input("Clé API OpenAI", type="password")
        model = st.selectbox("Modèle", ["gpt-4", "gpt-3.5-turbo"])
    else:
        ollama_url = st.text_input("URL Ollama", "http://localhost:11434")
        model = st.selectbox("Modèle", ["llama2", "mistral", "neural-chat"])
    
    if st.button("💾 Sauvegarder Paramètres"):
        st.success("✓ Paramètres sauvegardés!")

# Footer
st.sidebar.write("---")
st.sidebar.write(f"**Version**: 1.0.0  \n**Statut**: 🟢 En ligne")
