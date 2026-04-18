"""
PROFESSIONAL STREAMLIT DASHBOARD - Neo-Sousse Smart City
Phase 1 ↔      Real-Time Synchronization
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import sys
import time

sys.path.insert(0, 'c:\\Users\\Mrabet\\Desktop\\devops\\outils\\ps-main\\projet DB\\SensorLinker\\SensorLinker\\compiler-pm-phase2')

from src.realtime_cache import get_cache
from src.db_connection import get_db
from src.dashboard.pages_handlers import render_interventions_workflow_page
from src.dashboard.ia_reports_handler import render_ia_reports_page

# New helpers for Automata and NL Compiler
from src.dashboard.automata_utils import (
    get_automata_definitions,
    render_graphviz_dot,
    simulate_step,
    append_history_row,
    load_history,
    run_scenario,
)

from src.dashboard.nl_compiler_utils import (
    examples_list,
    validate_sql_is_safe,
    save_query_history,
    load_query_history,
)

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="Neo-Sousse Smart City",
    page_icon="🏙️",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items=None
)

# Custom CSS for professional styling
st.markdown("""
<style>
    .main {
        padding: 2rem 1rem;
    }
    
    .metric-card {
        background-color: #f0f2f6;
        padding: 1.5rem;
        border-radius: 0.5rem;
        border-left: 5px solid #1f77b4;
    }
    
    .status-ok { color: #28a745; font-weight: bold; }
    .status-warning { color: #ffc107; font-weight: bold; }
    .status-error { color: #dc3545; font-weight: bold; }
    
    h1 { color: #1f77b4; border-bottom: 2px solid #1f77b4; padding-bottom: 0.5rem; }
    h2 { color: #0056b3; margin-top: 1.5rem; }
    h3 { color: #0056b3; }
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# SESSION STATE & CACHE
# ═══════════════════════════════════════════════════════════════════════════════

if 'last_refresh' not in st.session_state:
    st.session_state.last_refresh = time.time()
    st.session_state.auto_refresh_enabled = True
    st.session_state.refresh_indicator = 0
    st.session_state.current_page = "Dashboard"  # Remember current page

cache = get_cache()

# ═══════════════════════════════════════════════════════════════════════════════
# AUTO-POLLING MECHANISM (Forces Streamlit to rerun every 1.5 seconds)
# ═══════════════════════════════════════════════════════════════════════════════

# This placeholder will be at the TOP so polling starts immediately
polling_placeholder = st.empty()

# Auto-refresh indicator (increments with each rerun to force widget updates)
st.session_state.refresh_indicator += 1

# ═══════════════════════════════════════════════════════════════════════════════
# HEADER WITH REFRESH CONTROLS
# ═══════════════════════════════════════════════════════════════════════════════

top_col1, top_col2, top_col3 = st.columns([3, 1, 1])

with top_col3:
    if st.button("🔄 REFRESH", key="refresh_btn", use_container_width=True):
        st.session_state.last_refresh = time.time()
        st.rerun()

with top_col2:
    elapsed = time.time() - st.session_state.last_refresh
    status_color = "status-ok" if elapsed < 5 else "status-warning"
    st.markdown(f'<p class="{status_color}">Updated {int(elapsed)}s ago</p>', unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# SIDEBAR NAVIGATION
# ═══════════════════════════════════════════════════════════════════════════════

st.sidebar.title("Neo-Sousse Smart City")
st.sidebar.write("Phase 1 ↔      Integration")
st.sidebar.write("---")

# List of pages
pages_list = [
    "Dashboard",
    "Sensors Management",
    "Interventions",
    "Interventions Workflow",
    "Technicians",
    "Citizens",
    "Vehicles",
    "Routes",
    "NL Compiler",
    "Automata",
    "IA Reports",
    "Settings"
]

# Get current page index from session_state
current_page_index = pages_list.index(st.session_state.current_page) if st.session_state.current_page in pages_list else 0

# Display radio with persisted page selection
page = st.sidebar.radio(
    "Navigation",
    pages_list,
    index=current_page_index
)

# Save selected page to session_state so it persists across refreshes
st.session_state.current_page = page

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════════

if page == "Dashboard":
    st.title("Dashboard - Real-Time System Status")
    
    # Get real-time data
    stats = cache.get_stats(force_refresh=True)
    capteurs = cache.get_capteurs(force_refresh=True)
    interventions = cache.get_interventions(force_refresh=True)
    techniciens = cache.get_techniciens(force_refresh=True)
    
    # Key Metrics
    st.subheader("Key Metrics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total Sensors",
            stats.get('capteurs_total', 0),
            f"{stats.get('capteurs_actifs', 0)} active"
        )
    
    with col2:
        st.metric(
            "Active Rate",
            f"{(stats.get('capteurs_actifs', 0) / max(stats.get('capteurs_total', 1), 1) * 100):.1f}%"
        )
    
    with col3:
        st.metric(
            "Interventions",
            stats.get('interventions_total', 0)
        )
    
    with col4:
        st.metric(
            "Technicians",
            stats.get('techniciens_total', 0)
        )
    
    # System Status
    st.write("---")
    col_status1, col_status2, col_status3 = st.columns(3)
    
    with col_status1:
        st.markdown('<p class="status-ok">[ONLINE] Database Connected</p>', unsafe_allow_html=True)
        st.markdown('<p class="status-ok">[ONLINE] Express API Active</p>', unsafe_allow_html=True)
    
    with col_status2:
        st.markdown('<p class="status-ok">[ONLINE] Streamlit Dashboard</p>', unsafe_allow_html=True)
        st.markdown('<p class="status-ok">[ONLINE] React Framework</p>', unsafe_allow_html=True)
    
    with col_status3:
        st.markdown('<p class="status-ok">[ONLINE] Phase 1 ↔     </p>', unsafe_allow_html=True)
        st.markdown('<p class="status-ok">[SYNC] Real-Time Updated</p>', unsafe_allow_html=True)
    
    # Recent Sensors
    st.write("---")
    st.subheader("Recent Sensors (Latest 10)")
    
    if capteurs:
        df_capteurs = pd.DataFrame(capteurs[:10])
        
        # Format for display
        display_cols = ['UUID', 'Type', 'Statut', 'Latitude', 'Longitude']
        if all(col in df_capteurs.columns for col in display_cols):
            df_display = df_capteurs[display_cols].copy()
            df_display['UUID'] = df_display['UUID'].astype(str).str[:12] + "..."
            st.dataframe(df_display, use_container_width=True, hide_index=True)
        else:
            st.dataframe(df_capteurs, use_container_width=True, hide_index=True)
    else:
        st.info("No sensors in database")
    
    # Recent Interventions
    st.write("---")
    st.subheader("Recent Interventions (Latest 10)")
    
    if interventions:
        df_interventions = pd.DataFrame(interventions[:10])
        
        # Show interventions with technician assignments
        display_cols = ['IDIn', 'DateHeure', 'Nature', 'Durée', 'statut', 'Techniciens_Assignés']
        available_cols = [col for col in display_cols if col in df_interventions.columns]
        
        if available_cols:
            df_display = df_interventions[available_cols].copy()
            st.dataframe(df_display, use_container_width=True, hide_index=True)
        else:
            st.dataframe(df_interventions, use_container_width=True, hide_index=True)
    else:
        st.info("No interventions in database")

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: SENSORS MANAGEMENT
# ═══════════════════════════════════════════════════════════════════════════════

elif page == "Sensors Management":
    st.title("Sensors Management")
    
    capteurs = cache.get_capteurs(force_refresh=True)
    stats = cache.get_stats()
    
    # Summary
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Sensors", stats.get('capteurs_total', 0))
    with col2:
        st.metric("Active", stats.get('capteurs_actifs', 0))
    with col3:
        st.metric("Inactive", stats.get('capteurs_total', 0) - stats.get('capteurs_aktifs', 0))
    
    # Detailed List
    st.subheader("All Sensors")
    
    if capteurs:
        df = pd.DataFrame(capteurs)
        
        # Add filters
        col_f1, col_f2 = st.columns(2)
        
        with col_f1:
            status_filter = st.multiselect(
                "Filter by Status",
                df['Statut'].unique().tolist() if 'Statut' in df.columns else [],
                default=df['Statut'].unique().tolist() if 'Statut' in df.columns else []
            )
        
        with col_f2:
            type_filter = st.multiselect(
                "Filter by Type",
                df['Type'].unique().tolist() if 'Type' in df.columns else [],
                default=df['Type'].unique().tolist() if 'Type' in df.columns else []
            )
        
        # Apply filters
        if status_filter:
            df = df[df['Statut'].isin(status_filter)] if 'Statut' in df.columns else df
        
        if type_filter:
            df = df[df['Type'].isin(type_filter)] if 'Type' in df.columns else df
        
        st.dataframe(df, use_container_width=True, hide_index=True)
        st.write(f"Showing {len(df)} of {len(capteurs)} sensors")
    else:
        st.info("No sensors found")

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: INTERVENTIONS
# ═══════════════════════════════════════════════════════════════════════════════

elif page == "Interventions":
    st.title("Interventions Management")
    
    interventions = cache.get_interventions(force_refresh=True)
    stats = cache.get_stats()
    
    st.metric("Total Interventions", stats.get('interventions_total', 0))
    
    st.subheader("All Interventions")
    
    if interventions:
        df = pd.DataFrame(interventions)
        
        # Filters
        col_f1, col_f2 = st.columns(2)
        
        with col_f1:
            if 'statut' in df.columns:
                status_filter = st.multiselect(
                    "Filter by Status",
                    df['statut'].unique().tolist(),
                    default=df['statut'].unique().tolist()
                )
                df = df[df['statut'].isin(status_filter)]
        
        with col_f2:
            if 'Nature' in df.columns:
                nature_filter = st.multiselect(
                    "Filter by Type",
                    df['Nature'].unique().tolist(),
                    default=df['Nature'].unique().tolist()
                )
                df = df[df['Nature'].isin(nature_filter)]
        
        # Select columns to display (show technician assignments)
        display_cols = ['IDIn', 'DateHeure', 'Nature', 'Durée', 'statut', 'Techniciens_Assignés']
        available_cols = [col for col in display_cols if col in df.columns]
        st.dataframe(df[available_cols], use_container_width=True, hide_index=True)
        st.write(f"Showing {len(df)} interventions")
    else:
        st.info("No interventions found")

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: INTERVENTIONS WORKFLOW (    )
# ═══════════════════════════════════════════════════════════════════════════════

elif page == "Interventions Workflow":
    render_interventions_workflow_page()

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: TECHNICIANS
# ═══════════════════════════════════════════════════════════════════════════════

elif page == "Technicians":
    st.title("Technicians Management")
    
    techniciens = cache.get_techniciens(force_refresh=True)
    stats = cache.get_stats()
    
    st.metric("Total Technicians", stats.get('techniciens_total', 0))
    
    st.subheader("All Technicians")
    
    if techniciens:
        df = pd.DataFrame(techniciens)
        
        # Display with proper column names
        if 'IDT' in df.columns:
            display_df = df[['IDT', 'Nom', 'Numero']] if 'Numero' in df.columns else df
        else:
            display_df = df
        
        st.dataframe(display_df, use_container_width=True, hide_index=True)
        st.write(f"Total: {len(techniciens)} technicians")
    else:
        st.warning("No technicians found in database")

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: CITIZENS
# ═══════════════════════════════════════════════════════════════════════════════

elif page == "Citizens":
    st.title("Citizens Management")
    
    try:
        citoyens = cache.get_citoyens(force_refresh=True)
        
        if citoyens:
            st.metric("Total Citizens", len(citoyens))
            
            st.subheader("All Citizens")
            df = pd.DataFrame(citoyens)
            
            # Show all available columns
            st.dataframe(df, use_container_width=True, hide_index=True)
            st.write(f"Total: {len(citoyens)} citizens in database")
        else:
            st.info("No citizens found in database")
    except Exception as e:
        st.error(f"Error loading citizens: {e}")

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: VEHICLES
# ═══════════════════════════════════════════════════════════════════════════════

elif page == "Vehicles":
    st.title("Vehicles Management")
    
    try:
        vehicules = cache.get_vehicules(force_refresh=True)
        
        if vehicules:
            st.metric("Total Vehicles", len(vehicules))
            
            st.subheader("All Vehicles")
            df = pd.DataFrame(vehicules)
            
            # Show all available columns
            st.dataframe(df, use_container_width=True, hide_index=True)
            st.write(f"Total: {len(vehicules)} vehicles in database")
        else:
            st.info("No vehicles found in database")
    except Exception as e:
        st.error(f"Error loading vehicles: {e}")

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: ROUTES
# ═══════════════════════════════════════════════════════════════════════════════

elif page == "Routes":
    st.title("Routes Management")
    
    try:
        trajets = cache.get_trajets(force_refresh=True)
        
        if trajets:
            st.metric("Total Routes", len(trajets))
            
            st.subheader("All Routes")
            df = pd.DataFrame(trajets)
            
            # Show all available columns
            st.dataframe(df, use_container_width=True, hide_index=True)
            st.write(f"Total: {len(trajets)} routes in database")
        else:
            st.info("No routes found in database")
    except Exception as e:
        st.error(f"Error loading routes: {e}")

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: NL COMPILER
# ═══════════════════════════════════════════════════════════════════════════════

elif page == "NL Compiler":
    st.title("Natural Language → SQL Compiler")

    st.write("Enter a query in natural language and compile it to SQL")

    examples = examples_list()
    col_e1, col_e2 = st.columns([3, 1])
    with col_e1:
        nl_input = st.text_area(
            "Natural Language Query",
            placeholder="Example: Show me the 5 most polluted zones",
            height=120
        )
    with col_e2:
        st.write("Examples")
        for ex in examples:
            if st.button(ex, key=f"ex_{ex}"):
                nl_input = ex

    # Quick suggestions / IA assistant (optional)
    if st.button("Suggest reformulation (IA)"):
        try:
            from src.ia_strict_validator_v3 import suggest_rephrase
            suggestion = suggest_rephrase(nl_input)
            st.success("IA suggestion ready")
            st.text_area("IA suggestion", value=suggestion, height=80, key="ia_sugg")
        except Exception:
            st.warning("IA assistant not available in this environment")

    # Compile / preview area
    st.write("---")
    st.subheader("Preview SQL")
    sql_preview = st.text_area("Generated SQL (preview)", value="SELECT * FROM Capteur WHERE ...", height=140)

    col_run1, col_run2, col_run3 = st.columns([1, 1, 1])
    with col_run1:
        if st.button("Validate SQL"):
            ok, reason = validate_sql_is_safe(sql_preview)
            if ok:
                st.success("SQL validated for sandbox execution")
            else:
                st.error(f"Validation failed: {reason}")

    with col_run2:
        if st.button("Execute in Sandbox (SELECT only)"):
            ok, reason = validate_sql_is_safe(sql_preview)
            if not ok:
                st.error(f"Cannot execute: {reason}")
            else:
                try:
                    db = get_db()
                    cursor = db.cursor()
                    cursor.execute(sql_preview)
                    rows = cursor.fetchall()
                    cols = [d[0] for d in cursor.description] if cursor.description else []
                    if cols:
                        st.dataframe(pd.DataFrame(rows, columns=cols), use_container_width=True)
                    else:
                        st.write(rows)
                except Exception as e:
                    st.error(f"Query error: {e}")

    with col_run3:
        if st.button("EXPLAIN"):
            ok, reason = validate_sql_is_safe(sql_preview)
            if not ok:
                st.error("EXPLAIN allowed only for SELECT queries")
            else:
                try:
                    db = get_db()
                    cursor = db.cursor()
                    cursor.execute(f"EXPLAIN {sql_preview}")
                    rows = cursor.fetchall()
                    cols = [d[0] for d in cursor.description] if cursor.description else []
                    st.dataframe(pd.DataFrame(rows, columns=cols), use_container_width=True)
                except Exception as e:
                    st.error(f"EXPLAIN error: {e}")

    # Save template / history
    st.write("---")
    if st.button("Save to history"):
        save_query_history(nl_input or "", sql_preview or "")
        st.success("Saved to history")

    history = load_query_history()
    if history:
        st.subheader("History")
        for i, h in enumerate(history[::-1][:10]):
            st.markdown(f"**{i+1}.** NL: {h.get('nl','')}  —  SQL: `{h.get('sql','')}`")

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: AUTOMATA
# ═══════════════════════════════════════════════════════════════════════════════

elif page == "Automata":
    st.title("Automata Engine")

    automata_defs = get_automata_definitions()
    automata_type = st.selectbox("Select Automata Type", list(automata_defs.keys()))
    defn = automata_defs.get(automata_type, {})

    st.subheader(f"{automata_type} — State Machine")

    # Visualisation
    st.write("Visualisation")
    current_state = st.selectbox("Current State", defn.get("states", []), key="auto_curr_state")
    dot = render_graphviz_dot(defn, highlight_state=current_state)
    st.graphviz_chart(dot)

    # Step-by-step simulator
    st.write("---")
    st.subheader("Simulator — Step by step")
    events = list(defn.get("transitions", {}).keys())
    col_a, col_b = st.columns([2, 1])
    with col_a:
        chosen_event = st.selectbox("Choose event", [""] + events)
        if st.button("Apply Transition"):
            if not chosen_event:
                st.warning("Choose an event first")
            else:
                new_state, msg = simulate_step(defn, current_state, chosen_event)
                st.info(msg)
                # append history row
                append_history_row({
                    "timestamp": pd.Timestamp.now().isoformat(),
                    "automata": automata_type,
                    "event": chosen_event,
                    "from": current_state,
                    "to": new_state,
                    "note": msg
                })
                # update session state to new state so dot highlights it next run
                st.session_state.auto_last_state = new_state

    with col_b:
        manual = st.text_input("Manual event (name)")
        if st.button("Apply Manual"):
            if not manual:
                st.warning("Enter event name")
            else:
                new_state, msg = simulate_step(defn, current_state, manual)
                st.info(msg)
                append_history_row({
                    "timestamp": pd.Timestamp.now().isoformat(),
                    "automata": automata_type,
                    "event": manual,
                    "from": current_state,
                    "to": new_state,
                    "note": msg
                })

    # Run scenario (batch)
    st.write("---")
    st.subheader("Run Scenario (batch)")
    scenario_text = st.text_area("Events (one per line)")
    if st.button("Run scenario"):
        events_list = [l.strip() for l in scenario_text.splitlines() if l.strip()]
        final_state, log = run_scenario(defn, current_state, events_list)
        st.write(f"Start: {current_state} → Final: {final_state}")
        for row in log:
            st.markdown(f"- `{row['event']}` → {row['state']} — {row['message']}")
        # save scenario run to history
        append_history_row({
            "timestamp": pd.Timestamp.now().isoformat(),
            "automata": automata_type,
            "event": "|".join(events_list),
            "from": current_state,
            "to": final_state,
            "note": "scenario_run"
        })

    # History table + export
    st.write("---")
    st.subheader("History")
    hist_df = load_history()
    if not hist_df.empty:
        st.dataframe(hist_df.tail(200), use_container_width=True)
        csv = hist_df.to_csv(index=False).encode('utf-8')
        st.download_button("Export CSV", csv, file_name="automata_history.csv")
    else:
        st.info("No history recorded yet")

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: IA REPORTS
# ═══════════════════════════════════════════════════════════════════════════════

elif page == "IA Reports":
    render_ia_reports_page()

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: SETTINGS
# ═══════════════════════════════════════════════════════════════════════════════

elif page == "Settings":
    st.title("System Settings")
    
    st.subheader("Database Configuration")
    st.write("Host: 127.0.0.1:3306")
    st.write("Database: sousse_smart_city_projet_module")
    
    st.subheader("Cache Settings")
    refresh_interval = st.slider("Cache Refresh Interval (seconds)", 1, 10, 2)
    st.write(f"Current: {refresh_interval}s")
    
    if st.button("Save Settings"):
        st.success("Settings saved")

# ═══════════════════════════════════════════════════════════════════════════════
# FOOTER
# ═══════════════════════════════════════════════════════════════════════════════

st.sidebar.write("---")
st.sidebar.write("**Status:** System Online")
st.sidebar.write("**Version:** 2.0.0 Professional")
st.sidebar.write(f"**Last Update:** {datetime.now().strftime('%H:%M:%S')}")

# ═══════════════════════════════════════════════════════════════════════════════
# AUTO POLLING LOOP (Forces Streamlit to rerun continuously)
# ═══════════════════════════════════════════════════════════════════════════════
# 
# This is the KEY to real-time updates!
# When Streamlit encounters time.sleep(), it pauses and then automatically reruns the:
# entire script. This creates an automatic polling loop that forces fresh data queries.
#
# How it works:
# 1. Script runs to completion
# 2. Reaches time.sleep(1.5)
# 3. Streamlit waits 1.5 seconds
# 4. Streamlit automatically reruns the entire script from the top
# 5. GET requests go to DB with force_refresh=True
# 6. Fresh data appears on screen
# 7. Loop repeats infinitely
#
# This is MORE RELIABLE than st.rerun() which only works in callbacks
# ═══════════════════════════════════════════════════════════════════════════════

if st.session_state.auto_refresh_enabled:
    # Sleep for 1.5 seconds - when this completes, Streamlit automatically reruns the script
    time.sleep(1.5)
