"""
Interventions Workflow Page Handler
Manages the new      Interventions Workflow UI
"""

import sys
import streamlit as st
import pandas as pd
from datetime import datetime

sys.path.insert(0, 'c:\\Users\\Mrabet\\Desktop\\devops\\outils\\ps-main\\projet DB\\SensorLinker\\SensorLinker\\compiler-pm-phase2')

from src.state_manager import StateManager, InterventionState
from src.realtime_cache import get_cache
from src.db_connection import get_db

def render_interventions_workflow_page():
    """Render the Interventions Workflow Management page"""
    
    st.title("🔄 Interventions Workflow Management -     ")
    st.write("Real-time intervention state management with technician assignment and validation")
    
    # Initialize components
    cache = get_cache()
    db = get_db()
    state_manager = StateManager()
    
    # ═══════════════════════════════════════════════════════════════════════════
    # WORKFLOW STATUS COLOR MAPPING
    # ═══════════════════════════════════════════════════════════════════════════
    
    status_colors = {
        'Demande': '🔴',           # Red - Initial request
        'Tech1_Assigné': '🟡',     # Yellow - Technician 1 assigned
        'Tech2_Valide': '🟠',      # Orange - Technician 2 assigned
        'IA_Valide': '🟢',         # Green - IA validated
        'Terminée': '✅'           # Checkmark - Complete
    }
    
    # ═══════════════════════════════════════════════════════════════════════════
    # REFRESH AND DATA LOADING
    # ═══════════════════════════════════════════════════════════════════════════
    
    col1, col2, col3 = st.columns([3, 1, 1])
    
    with col3:
        if st.button("🔄 Refresh Data", use_container_width=True):
            st.rerun()
    
    # Get interventions with workflow data
    interventions_workflow = cache.get_interventions_workflow(force_refresh=True)
    
    if not interventions_workflow:
        st.warning("No interventions found in the system")
        return
    
    # ═══════════════════════════════════════════════════════════════════════════
    # WORKFLOW STATISTICS
    # ═══════════════════════════════════════════════════════════════════════════
    
    st.subheader("Workflow Statistics")
    
    stats_col1, stats_col2, stats_col3, stats_col4, stats_col5 = st.columns(5)
    
    with stats_col1:
        demandes = len([i for i in interventions_workflow if i['statut'] == 'Demande'])
        st.metric("🔴 Demandes", demandes)
    
    with stats_col2:
        tech1_assigned = len([i for i in interventions_workflow if i['statut'] == 'Tech1_Assigné'])
        st.metric("🟡 Tech1 Assigned", tech1_assigned)
    
    with stats_col3:
        tech2_assigned = len([i for i in interventions_workflow if i['statut'] == 'Tech2_Valide'])
        st.metric("🟠 Tech2 Assigned", tech2_assigned)
    
    with stats_col4:
        ia_validated = len([i for i in interventions_workflow if i['statut'] == 'IA_Valide'])
        st.metric("🟢 IA Validated", ia_validated)
    
    with stats_col5:
        completed = len([i for i in interventions_workflow if i['statut'] == 'Terminée'])
        st.metric("✅ Completed", completed)
    
    # ═══════════════════════════════════════════════════════════════════════════
    # INTERVENTIONS LIST WITH WORKFLOW STATUS
    # ═══════════════════════════════════════════════════════════════════════════
    
    st.subheader("All Interventions")
    
    # Create display dataframe
    display_data = []
    for i in interventions_workflow:
        status_emoji = status_colors.get(i['statut'], '❓')
        
        # Format date (handle both string and datetime objects)
        date_str = i['DateHeure']
        if hasattr(date_str, 'strftime'):
            date_str = date_str.strftime('%Y-%m-%d %H:%M')
        elif isinstance(date_str, str) and len(date_str) > 10:
            date_str = date_str[:16]  # YYYY-MM-DD HH:MM
        
        display_data.append({
            'ID': i['IDIn'],
            'Date': date_str,
            'Type': i['Nature'],
            'Duration (h)': i.get('Durée', 0),
            'Status': f"{status_emoji} {i['statut']}",
            'Tech 1': i.get('tech1_name', '—'),
            'Tech 2': i.get('tech2_name', '—')
        })
    
    df_display = pd.DataFrame(display_data)
    st.dataframe(df_display, use_container_width=True, hide_index=True)
    
    st.write(f"Showing {len(interventions_workflow)} total interventions")
    
    # ═══════════════════════════════════════════════════════════════════════════
    # INTERVENTION DETAIL VIEW & MANAGEMENT
    # ═══════════════════════════════════════════════════════════════════════════
    
    st.subheader("Intervention Management")
    
    # Select intervention
    intervention_options = {f"ID {i['IDIn']} - {i['Nature']}" : i['IDIn'] for i in interventions_workflow}
    selected_display = st.selectbox("Select an Intervention", list(intervention_options.keys()))
    selected_id = intervention_options[selected_display]
    
    # Get selected intervention details
    selected = next((i for i in interventions_workflow if i['IDIn'] == selected_id), None)
    
    if selected:
        # Progress display
        progress_steps = {
            'Demande': 0,
            'Tech1_Assigné': 1,
            'Tech2_Valide': 2,
            'IA_Valide': 3,
            'Terminée': 4
        }
        
        current_step = progress_steps.get(selected['statut'], 0)
        progress = current_step / 4
        
        st.progress(progress)
        
        progress_text = f"Step {current_step + 1}/5: {selected['statut']}"
        st.caption(progress_text)
        
        # Details tabs
        tab1, tab2, tab3 = st.tabs(["📋 Details", "👥 Assignment", "📝 Reports"])
        
        # ═════════════════════════════════════════════════════════════════════
        # TAB 1: DETAILS
        # ═════════════════════════════════════════════════════════════════════
        
        with tab1:
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**Intervention ID:** {selected['IDIn']}")
                # Format date for display
                date_display = selected['DateHeure']
                if hasattr(date_display, 'strftime'):
                    date_display = date_display.strftime('%Y-%m-%d %H:%M:%S')
                st.write(f"**Date/Time:** {date_display}")
                st.write(f"**Type:** {selected['Nature']}")
            
            with col2:
                st.write(f"**Duration:** {selected.get('Durée', 0)} hours")
                st.write(f"**Status:** {status_colors.get(selected['statut'], '❓')} {selected['statut']}")
        
        # ═════════════════════════════════════════════════════════════════════
        # TAB 2: ASSIGNMENT
        # ═════════════════════════════════════════════════════════════════════
        
        with tab2:
            st.write("**Technician Assignment Process**")
            
            col1, col2 = st.columns(2)
            
            # Tech 1 Assignment
            with col1:
                st.write("**Technician 1 (Intervenant)**")
                
                if selected['technicien_1_id']:
                    st.success(f"✓ Assigned: {selected.get('tech1_name', 'Unknown')}")
                else:
                    techs = db.fetch_all("SELECT IDT, Nom FROM Technicien ORDER BY Nom")
                    if techs:
                        tech_dict = {t['Nom']: t['IDT'] for t in techs}
                        selected_tech1 = st.selectbox(
                            "Select Technician 1",
                            options=list(tech_dict.keys()),
                            key="tech1_select"
                        )
                        
                        if st.button("✓ Assign Tech 1", key="assign_tech1"):
                            success, message = state_manager.assign_technician_1(selected_id, tech_dict[selected_tech1])
                            if success:
                                st.success(f"✓ {message}")
                                st.rerun()
                            else:
                                st.error(f"✗ {message}")
            
            # Tech 2 Assignment
            with col2:
                st.write("**Technician 2 (Validateur)**")
                
                if selected['technicien_2_id']:
                    st.success(f"✓ Assigned: {selected.get('tech2_name', 'Unknown')}")
                else:
                    if not selected['technicien_1_id']:
                        st.info("⚠️ Assign Tech 1 first")
                    else:
                        techs = db.fetch_all(f"SELECT IDT, Nom FROM Technicien WHERE IDT != {selected['technicien_1_id']} ORDER BY Nom")
                        if techs:
                            tech_dict = {t['Nom']: t['IDT'] for t in techs}
                            selected_tech2 = st.selectbox(
                                "Select Technician 2",
                                options=list(tech_dict.keys()),
                                key="tech2_select"
                            )
                            
                            if st.button("✓ Assign Tech 2", key="assign_tech2"):
                                success, message = state_manager.assign_technician_2(selected_id, tech_dict[selected_tech2])
                                if success:
                                    st.success(f"✓ {message}")
                                    st.rerun()
                                else:
                                    st.error(f"✗ {message}")
        
        # ═════════════════════════════════════════════════════════════════════
        # TAB 3: REPORTS
        # ═════════════════════════════════════════════════════════════════════
        
        with tab3:
            st.write("**Report Submission**")
            
            col1, col2 = st.columns(2)
            
            # Tech 1 Report
            with col1:
                st.write("**Technician 1 Report**")
                
                current_report = selected.get('rapport_tech1', '')
                if current_report:
                    st.success(f"✓ Report submitted")
                    with st.expander("View Report"):
                        st.text(current_report)
                else:
                    if selected['technicien_1_id']:
                        report_text = st.text_area(
                            "Write Tech 1 Report",
                            height=150,
                            key="tech1_report"
                        )
                        
                        if st.button("📤 Submit Tech 1 Report", key="submit_tech1"):
                            if report_text.strip():
                                success, message = state_manager.submit_report_tech1(selected_id, report_text)
                                if success:
                                    st.success(f"✓ {message}")
                                    st.rerun()
                                else:
                                    st.error(f"✗ {message}")
                            else:
                                st.warning("Report cannot be empty")
                    else:
                        st.info("⚠️ Assign Tech 1 first")
            
            # Tech 2 Report
            with col2:
                st.write("**Technician 2 Report**")
                
                current_report = selected.get('rapport_tech2', '')
                if current_report:
                    st.success(f"✓ Report submitted")
                    with st.expander("View Report"):
                        st.text(current_report)
                else:
                    if selected['technicien_2_id']:
                        report_text = st.text_area(
                            "Write Tech 2 Report",
                            height=150,
                            key="tech2_report"
                        )
                        
                        if st.button("📤 Submit Tech 2 Report", key="submit_tech2"):
                            if report_text.strip():
                                success, message = state_manager.submit_report_tech2(selected_id, report_text)
                                if success:
                                    st.success(f"✓ {message}")
                                    st.rerun()
                                else:
                                    st.error(f"✗ {message}")
                            else:
                                st.warning("Report cannot be empty")
                    else:
                        st.info("⚠️ Assign Tech 2 first")
        
        # ═════════════════════════════════════════════════════════════════════
        # IA VALIDATION SECTION
        # ═════════════════════════════════════════════════════════════════════
        
        if selected['statut'] == 'IA_Valide':
            st.divider()
            st.subheader("🤖 IA Validation & Completion")
            
            # Check if both reports are submitted
            if selected.get('rapport_tech1') and selected.get('rapport_tech2'):
                st.success("✓ Both technician reports received")
                
                # IA validation input
                ia_report = st.text_area(
                    "IA Validation Report (Auto-generated summary)",
                    value=f"""Intervention ID: {selected['IDIn']}
Type: {selected['Nature']}
Duration: {selected.get('Durée', 0)} hours

TECHNICIAN 1 FINDINGS:
{selected.get('rapport_tech1', 'N/A')}

TECHNICIAN 2 VALIDATION:
{selected.get('rapport_tech2', 'N/A')}

IA SUMMARY:
Both technicians have completed their assessments and validation.
The intervention is ready for completion.""",
                    height=200,
                    disabled=False,
                    key="ia_report"
                )
                
                if st.button("✅ Complete Intervention (IA Validate)", key="complete_intervention"):
                    if ia_report.strip():
                        success, message = state_manager.ia_validate(selected_id, ia_report)
                        if success:
                            st.success(f"✓ {message}")
                            st.success("🎉 Intervention completed! Step 5/5: Terminée")
                            st.rerun()
                        else:
                            st.error(f"✗ {message}")
                    else:
                        st.warning("IA Report cannot be empty")
            else:
                st.warning("⚠️ Both technician reports must be submitted first")
        
        elif selected['statut'] == 'Terminée':
            st.divider()
            st.subheader("✅ Intervention Completed")
            st.success("This intervention has been completed and validated by IA")
