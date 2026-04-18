"""
Real-Time Data Cache Service
Synchronize data instantly between React, Express, DB and Streamlit
"""

import threading
import time
from datetime import datetime, timedelta
import sys
sys.path.insert(0, 'c:\\Users\\Mrabet\\Desktop\\devops\\outils\\ps-main\\projet DB\\SensorLinker\\SensorLinker\\compiler-pm-phase2')

from src.db_connection import get_db
import json

class RealTimeCache:
    """Cache with automatic refresh for real-time data"""
    
    def __init__(self, refresh_interval=0.5):  # Reduced from 2s to 0.5s for faster sync
        self.db = get_db()
        self.refresh_interval = refresh_interval
        self.last_refresh = {}
        self.cache = {}
        self._lock = threading.Lock()
        self._running = False
    
    def get_capteurs(self, force_refresh=False):
        """Get sensors with auto-refresh"""
        key = 'capteurs'
        
        # Force refresh if requested or if cache is old
        if force_refresh or not self._should_use_cache(key):
            self._refresh_capteurs()
        
        with self._lock:
            return self.cache.get(key, [])
    
    def get_interventions(self, force_refresh=False):
        """Get interventions with auto-refresh"""
        key = 'interventions'
        
        if force_refresh or not self._should_use_cache(key):
            self._refresh_interventions()
        
        with self._lock:
            return self.cache.get(key, [])
    
    def get_techniciens(self, force_refresh=False):
        """Get technicians with auto-refresh"""
        key = 'techniciens'
        
        if force_refresh or not self._should_use_cache(key):
            self._refresh_techniciens()
        
        with self._lock:
            return self.cache.get(key, [])
    
    def get_citoyens(self, force_refresh=False):
        """Get citizens with auto-refresh"""
        key = 'citoyens'
        
        if force_refresh or not self._should_use_cache(key):
            self._refresh_citoyens()
        
        with self._lock:
            return self.cache.get(key, [])
    
    def get_vehicules(self, force_refresh=False):
        """Get vehicles with auto-refresh"""
        key = 'vehicules'
        
        if force_refresh or not self._should_use_cache(key):
            self._refresh_vehicules()
        
        with self._lock:
            return self.cache.get(key, [])
    
    def get_trajets(self, force_refresh=False):
        """Get routes with auto-refresh"""
        key = 'trajets'
        
        if force_refresh or not self._should_use_cache(key):
            self._refresh_trajets()
        
        with self._lock:
            return self.cache.get(key, [])
    
    def get_stats(self, force_refresh=False):
        """Get statistics"""
        key = 'stats'
        
        if force_refresh or not self._should_use_cache(key):
            self._refresh_stats()
        
        with self._lock:
            return self.cache.get(key, {})
    
    def _should_use_cache(self, key):
        """Check if cache is still fresh"""
        if key not in self.last_refresh:
            return False
        
        elapsed = time.time() - self.last_refresh[key]
        return elapsed < self.refresh_interval
    
    def _refresh_capteurs(self):
        """Refresh sensors from database"""
        try:
            data = self.db.fetch_all("""
                SELECT UUID, Type, Latitude, Longitude, Statut, 
                       `Date Installation` as DateInstallation, IDP
                FROM Capteur
                ORDER BY `Date Installation` DESC
            """)
            
            with self._lock:
                self.cache['capteurs'] = data or []
                self.last_refresh['capteurs'] = time.time()
        except Exception as e:
            print(f"Error refreshing capteurs: {e}")
    
    def _refresh_interventions(self):
        """Refresh interventions from database"""
        try:
            data = self.db.fetch_all("""
                SELECT i.IDIn, i.DateHeure, i.Nature, i.`Durée`, i.`Coût`, i.ImpactCO2, i.UUID, 
                       i.statut,
                       GROUP_CONCAT(
                           CONCAT(t.Nom, ' (', s.Rôle, ')')
                           ORDER BY s.Rôle
                           SEPARATOR ' | '
                       ) as Techniciens_Assignés
                FROM Intervention i
                LEFT JOIN Supervision s ON i.IDIn = s.IDIn
                LEFT JOIN Technicien t ON s.IDT = t.IDT
                GROUP BY i.IDIn, i.DateHeure, i.Nature, i.`Durée`, i.`Coût`, i.ImpactCO2, i.UUID, i.statut
                ORDER BY i.DateHeure DESC
            """)
            
            with self._lock:
                self.cache['interventions'] = data or []
                self.last_refresh['interventions'] = time.time()
        except Exception as e:
            print(f"Error refreshing interventions: {e}")
    
    def _refresh_techniciens(self):
        """Refresh technicians from database"""
        try:
            data = self.db.fetch_all("""
                SELECT IDT, Nom, Numero
                FROM Technicien
                ORDER BY Nom
            """)
            
            with self._lock:
                self.cache['techniciens'] = data or []
                self.last_refresh['techniciens'] = time.time()
        except Exception as e:
            print(f"Error refreshing techniciens: {e}")
    
    def _refresh_stats(self):
        """Refresh statistics"""
        try:
            total_capteurs = self.db.fetch_one("SELECT COUNT(*) as cnt FROM Capteur")
            capteurs_actifs = self.db.fetch_one("SELECT COUNT(*) as cnt FROM Capteur WHERE Statut='Actif'")
            total_interventions = self.db.fetch_one("SELECT COUNT(*) as cnt FROM Intervention")
            total_techniciens = self.db.fetch_one("SELECT COUNT(*) as cnt FROM Technicien")
            
            stats = {
                'capteurs_total': total_capteurs['cnt'] if total_capteurs else 0,
                'capteurs_actifs': capteurs_actifs['cnt'] if capteurs_actifs else 0,
                'interventions_total': total_interventions['cnt'] if total_interventions else 0,
                'techniciens_total': total_techniciens['cnt'] if total_techniciens else 0,
                'last_update': datetime.now().isoformat()
            }
            
            with self._lock:
                self.cache['stats'] = stats
                self.last_refresh['stats'] = time.time()
        except Exception as e:
            print(f"Error refreshing stats: {e}")
    
    def _refresh_citoyens(self):
        """Refresh citizens from database"""
        try:
            data = self.db.fetch_all("""
                SELECT * FROM Citoyen LIMIT 100
            """)
            
            with self._lock:
                self.cache['citoyens'] = data or []
                self.last_refresh['citoyens'] = time.time()
        except Exception as e:
            print(f"Error refreshing citoyens: {e}")
    
    def _refresh_vehicules(self):
        """Refresh vehicles from database"""
        try:
            data = self.db.fetch_all("""
                SELECT * FROM Véhicule LIMIT 100
            """)
            
            with self._lock:
                self.cache['vehicules'] = data or []
                self.last_refresh['vehicules'] = time.time()
        except Exception as e:
            print(f"Error refreshing vehicules: {e}")
    
    def _refresh_trajets(self):
        """Refresh routes from database"""
        try:
            data = self.db.fetch_all("""
                SELECT * FROM Trajet LIMIT 100
            """)
            
            with self._lock:
                self.cache['trajets'] = data or []
                self.last_refresh['trajets'] = time.time()
        except Exception as e:
            print(f"Error refreshing trajets: {e}")
    
    def get_interventions_workflow(self, force_refresh=False):
        """Get interventions with workflow status (    )"""
        key = 'interventions_workflow'
        
        if force_refresh or not self._should_use_cache(key):
            self._refresh_interventions_workflow()
        
        with self._lock:
            return self.cache.get(key, [])
    
    def _refresh_interventions_workflow(self):
        """Refresh interventions with technician assignments and workflow state"""
        try:
            data = self.db.fetch_all("""
                SELECT 
                    i.IDIn,
                    i.DateHeure,
                    i.Nature,
                    i.Durée,
                    i.Coût,
                    i.ImpactCO2,
                    i.statut,
                    i.technicien_1_id,
                    i.technicien_2_id,
                    i.rapport_tech1,
                    i.rapport_tech2,
                    t1.Nom as tech1_name,
                    t1.Numero as tech1_numero,
                    t2.Nom as tech2_name,
                    t2.Numero as tech2_numero
                FROM Intervention i
                LEFT JOIN Technicien t1 ON i.technicien_1_id = t1.IDT
                LEFT JOIN Technicien t2 ON i.technicien_2_id = t2.IDT
                ORDER BY i.DateHeure DESC
            """)
            
            with self._lock:
                self.cache['interventions_workflow'] = data or []
                self.last_refresh['interventions_workflow'] = time.time()
        except Exception as e:
            print(f"Error refreshing interventions_workflow: {e}")

# Global cache instance
_cache = None

def get_cache():
    """Get or create global cache"""
    global _cache
    if _cache is None:
        _cache = RealTimeCache(refresh_interval=0.5)
    return _cache

# Test function
if __name__ == "__main__":
    cache = get_cache()
    
    print("Testing Real-Time Cache...")
    print()
    
    # Test stats
    stats = cache.get_stats(force_refresh=True)
    print(f"Stats: {stats}")
    print()
    
    # Test capteurs
    capteurs = cache.get_capteurs(force_refresh=True)
    print(f"Capteurs count: {len(capteurs)}")
    if capteurs:
        print(f"First capteur: {capteurs[0]}")
    print()
    
    # Test interventions
    interventions = cache.get_interventions(force_refresh=True)
    print(f"Interventions count: {len(interventions)}")
    if interventions:
        print(f"First intervention: {interventions[0]}")
    print()
    
    # Test technicians
    techniciens = cache.get_techniciens(force_refresh=True)
    print(f"Techniciens count: {len(techniciens)}")
    if techniciens:
        print(f"First technicien: {techniciens[0]}")
