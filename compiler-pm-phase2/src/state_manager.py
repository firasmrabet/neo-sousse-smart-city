#!/usr/bin/env python3
"""
STATE MANAGER -      Workflow Engine
Gère les transitions d'état du workflow d'intervention:
DEMANDE → TECH1_ASSIGNÉ → TECH2_VALIDE → IA_VALIDE → TERMINÉ
"""

import sys
sys.path.insert(0, 'c:\\Users\\Mrabet\\Desktop\\devops\\outils\\ps-main\\projet DB\\SensorLinker\\SensorLinker\\compiler-pm-phase2')

from src.db_connection import get_db
from datetime import datetime
from enum import Enum

class InterventionState(str, Enum):
    """Valid intervention workflow states"""
    DEMANDE = "Demande"
    TECH1_ASSIGNÉ = "Tech1_Assigné"
    TECH2_VALIDE = "Tech2_Valide"
    IA_VALIDE = "IA_Valide"
    TERMINÉE = "Terminée"

class StateManager:
    """
    Manages intervention workflow state transitions and technician assignments
    """
    
    def __init__(self):
        self.db = get_db()
        
    def get_intervention(self, intervention_id):
        """Get intervention details with current workflow state"""
        intervention = self.db.fetch_one("""
            SELECT 
                i.IDIn,
                i.DateHeure,
                i.Nature,
                i.Durée,
                i.Coût,
                i.ImpactCO2,
                i.UUID,
                i.statut,
                i.technicien_1_id,
                i.technicien_2_id,
                i.rapport_tech1,
                i.rapport_tech2,
                t1.Nom as tech1_name,
                t2.Nom as tech2_name
            FROM Intervention i
            LEFT JOIN Technicien t1 ON i.technicien_1_id = t1.IDT
            LEFT JOIN Technicien t2 ON i.technicien_2_id = t2.IDT
            WHERE i.IDIn = %s
        """, (intervention_id,))
        
        return intervention
    
    def assign_technician_1(self, intervention_id, technician_id):
        """
        Assign first technician (Intervenant role)
        Transition: DEMANDE → TECH1_ASSIGNÉ
        """
        try:
            intervention = self.get_intervention(intervention_id)
            
            if not intervention:
                return False, "Intervention not found"
            
            # Check if already at or past TECH1_ASSIGNÉ state
            current_state = intervention['statut']
            if current_state not in [InterventionState.DEMANDE, InterventionState.TECH1_ASSIGNÉ]:
                return False, f"Cannot assign tech1 when intervention is in state: {current_state}"
            
            # Prevent assigning same technician twice
            if intervention['technicien_2_id'] == technician_id:
                return False, "Cannot assign same technician twice (Tech2 already assigned)"
            
            # Update intervention
            success = self.db.execute_query("""
                UPDATE Intervention 
                SET 
                    technicien_1_id = %s,
                    statut = %s
                WHERE IDIn = %s
            """, (technician_id, InterventionState.TECH1_ASSIGNÉ, intervention_id))
            
            if success:
                # Log to audit table
                self._log_state_change(intervention_id, current_state, InterventionState.TECH1_ASSIGNÉ)
                return True, f"Technician 1 assigned successfully"
            else:
                return False, "Failed to update intervention"
                
        except Exception as e:
            return False, f"Error: {str(e)}"
    
    def assign_technician_2(self, intervention_id, technician_id):
        """
        Assign second technician (Validateur role)
        Transition: TECH1_ASSIGNÉ → TECH2_VALIDE
        """
        try:
            intervention = self.get_intervention(intervention_id)
            
            if not intervention:
                return False, "Intervention not found"
            
            # Check prerequisites
            if intervention['statut'] not in [InterventionState.TECH1_ASSIGNÉ, InterventionState.TECH2_VALIDE]:
                return False, f"Tech1 must be assigned first (current: {intervention['statut']})"
            
            if not intervention['technicien_1_id']:
                return False, "Tech1 must be assigned before assigning Tech2"
            
            # Prevent assigning same technician
            if intervention['technicien_1_id'] == technician_id:
                return False, "Cannot assign same technician twice (Tech1 already assigned)"
            
            # Update intervention
            current_state = intervention['statut']
            new_state = InterventionState.TECH2_VALIDE
            
            success = self.db.execute_query("""
                UPDATE Intervention 
                SET 
                    technicien_2_id = %s,
                    statut = %s
                WHERE IDIn = %s
            """, (technician_id, new_state, intervention_id))
            
            if success:
                self._log_state_change(intervention_id, current_state, new_state)
                return True, f"Technician 2 assigned successfully"
            else:
                return False, "Failed to update intervention"
                
        except Exception as e:
            return False, f"Error: {str(e)}"
    
    def submit_report_tech1(self, intervention_id, report_text):
        """
        Tech1 submits report
        """
        try:
            intervention = self.get_intervention(intervention_id)
            
            if not intervention:
                return False, "Intervention not found"
            
            if not intervention['technicien_1_id']:
                return False, "Tech1 not assigned yet"
            
            success = self.db.execute_query("""
                UPDATE Intervention 
                SET rapport_tech1 = %s
                WHERE IDIn = %s
            """, (report_text, intervention_id))
            
            if success:
                return True, "Report 1 submitted successfully"
            else:
                return False, "Failed to save report"
                
        except Exception as e:
            return False, f"Error: {str(e)}"
    
    def submit_report_tech2(self, intervention_id, report_text):
        """
        Tech2 submits report and transitions to IA validation
        Transition: TECH2_VALIDE → IA_VALIDE
        """
        try:
            intervention = self.get_intervention(intervention_id)
            
            if not intervention:
                return False, "Intervention not found"
            
            if intervention['statut'] != InterventionState.TECH2_VALIDE:
                return False, f"Cannot submit tech2 report in state: {intervention['statut']}"
            
            if not intervention['technicien_2_id']:
                return False, "Tech2 not assigned yet"
            
            # Update report and transition to IA validation
            current_state = intervention['statut']
            new_state = InterventionState.IA_VALIDE
            
            success = self.db.execute_query("""
                UPDATE Intervention 
                SET 
                    rapport_tech2 = %s,
                    statut = %s
                WHERE IDIn = %s
            """, (report_text, new_state, intervention_id))
            
            if success:
                self._log_state_change(intervention_id, current_state, new_state)
                return True, "Report 2 submitted - moving to IA validation"
            else:
                return False, "Failed to save report"
                
        except Exception as e:
            return False, f"Error: {str(e)}"
    
    def ia_validate(self, intervention_id, ia_report):
        """
        IA validates intervention and completes it
        Transition: IA_VALIDE → TERMINÉE
        """
        try:
            intervention = self.get_intervention(intervention_id)
            
            if not intervention:
                return False, "Intervention not found"
            
            if intervention['statut'] != InterventionState.IA_VALIDE:
                return False, f"Cannot validate in state: {intervention['statut']}"
            
            if not intervention['rapport_tech1'] or not intervention['rapport_tech2']:
                return False, "Both technician reports required before IA validation"
            
            current_state = intervention['statut']
            new_state = InterventionState.TERMINÉE
            
            # For now, store IA report as comment in rapport_tech1 or create new field
            success = self.db.execute_query("""
                UPDATE Intervention 
                SET statut = %s
                WHERE IDIn = %s
            """, (new_state, intervention_id))
            
            if success:
                self._log_state_change(intervention_id, current_state, new_state)
                return True, "Intervention validated by IA - workflow complete"
            else:
                return False, "Failed to update intervention"
                
        except Exception as e:
            return False, f"Error: {str(e)}"
    
    def reject_to_demande(self, intervention_id):
        """
        Reject intervention and return to DEMANDE state
        Can be called from any state
        """
        try:
            intervention = self.get_intervention(intervention_id)
            
            if not intervention:
                return False, "Intervention not found"
            
            current_state = intervention['statut']
            new_state = InterventionState.DEMANDE
            
            success = self.db.execute_query("""
                UPDATE Intervention 
                SET 
                    statut = %s,
                    technicien_1_id = NULL,
                    technicien_2_id = NULL,
                    rapport_tech1 = NULL,
                    rapport_tech2 = NULL
                WHERE IDIn = %s
            """, (new_state, intervention_id))
            
            if success:
                self._log_state_change(intervention_id, current_state, new_state)
                return True, "Intervention rejected - reset to DEMANDE"
            else:
                return False, "Failed to reset intervention"
                
        except Exception as e:
            return False, f"Error: {str(e)}"
    
    def _log_state_change(self, intervention_id, from_state, to_state):
        """
        Log state change for audit trail
        TODO: Create intervention_state_history table if not exists
        """
        try:
            # For now, just print log
            print(f"[STATE CHANGE] Intervention {intervention_id}: {from_state} → {to_state}")
        except:
            pass
    
    def get_workflow_progress(self, intervention_id):
        """
        Get workflow progress for display
        Returns dict with completion percentage and state info
        """
        intervention = self.get_intervention(intervention_id)
        
        if not intervention:
            return None
        
        states = [
            InterventionState.DEMANDE,
            InterventionState.TECH1_ASSIGNÉ,
            InterventionState.TECH2_VALIDE,
            InterventionState.IA_VALIDE,
            InterventionState.TERMINÉE
        ]
        
        current_state = intervention['statut']
        current_index = states.index(current_state)
        progress = ((current_index + 1) / len(states)) * 100
        
        return {
            'intervention_id': intervention_id,
            'current_state': current_state,
            'progress_percent': int(progress),
            'states': states,
            'current_index': current_index,
            'tech1_id': intervention['technicien_1_id'],
            'tech1_name': intervention['tech1_name'],
            'tech2_id': intervention['technicien_2_id'],
            'tech2_name': intervention['tech2_name'],
            'rapport_tech1': intervention['rapport_tech1'],
            'rapport_tech2': intervention['rapport_tech2']
        }

# Test the StateManager
if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("STATE MANAGER INITIALIZATION TEST")
    print("=" * 80)
    
    try:
        manager = StateManager()
        print("\n✓ StateManager initialized successfully")
        print("✓ Database connection verified")
        
        # Get a sample intervention
        print("\nAvailable methods:")
        print("  • assign_technician_1(intervention_id, technician_id)")
        print("  • assign_technician_2(intervention_id, technician_id)")
        print("  • submit_report_tech1(intervention_id, report_text)")
        print("  • submit_report_tech2(intervention_id, report_text)")
        print("  • ia_validate(intervention_id, ia_report)")
        print("  • reject_to_demande(intervention_id)")
        print("  • get_workflow_progress(intervention_id)")
        print("  • get_intervention(intervention_id)")
        
        print("\n✓ StateManager ready for use in Streamlit dashboard")
        
    except Exception as e:
        print(f"\n✗ Error initializing StateManager: {e}")
    
    print("\n" + "=" * 80 + "\n")
