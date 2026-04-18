"""
Compilateur PM -     : Smart City avec Automates et IA Générative

Main entry point pour l'application.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Setup paths
ROOT_DIR = Path(__file__).parent
sys.path.insert(0, str(ROOT_DIR))

# Load environment
load_dotenv(ROOT_DIR / ".env")

def main():
    """Entrée principale"""
    
    print("""
    ╔════════════════════════════════════════════════════════════════╗
    ║          PM-Compilation     : Smart City Manager            ║
    ║                                                                ║
    ║  Compiler NL→SQL | Automates | IA Générative | Dashboard      ║
    ╚════════════════════════════════════════════════════════════════╝
    """)
    
    print("\n📋 Options disponibles:")
    print("  1. Démarrer le Dashboard (Streamlit)")
    print("  2. Tester le Compilateur")
    print("  3. Gérer les Automates")
    print("  4. Générer un Rapport IA")
    print("  5. Tests unitaires")
    print("  6. Quitter")
    
    choice = input("\nChoisir une option (1-6): ").strip()
    
    if choice == "1":
        print("\n🚀 Démarrage du Dashboard...")
        os.system("streamlit run src/dashboard/app_v3.py")
    
    elif choice == "2":
        print("\n🔤 Testeur Compilateur")
        from src.compiler.compiler import Compiler
        
        compiler = Compiler()
        
        test_queries = [
            "Affiche les 5 zones les plus polluées",
            "Combien de capteurs sont hors service?",
            "Quels citoyens ont un score écologique > 80 ?",
        ]
        
        for query in test_queries:
            print(f"\n  NL: {query}")
            try:
                sql = compiler.compile(query)
                print(f"  SQL: {sql}")
            except Exception as e:
                print(f"  ❌ Erreur: {str(e)}")
    
    elif choice == "3":
        print("\n🤖 Gestionnaire Automates")
        from src.automata.engine import AutomataEngine
        
        engine = AutomataEngine()
        automata = engine.create_sensor_automata("C-001")
        
        print(f"\n  Automate Capteur C-001")
        print(f"  État initial: {automata.get_state()}")
        
        try:
            automata.trigger("installation")
            print(f"  Après installation: {automata.get_state()}")
            
            automata.trigger("detection_anomalie")
            print(f"  Après anomalie: {automata.get_state()}")
        except Exception as e:
            print(f"  ❌ Erreur: {str(e)}")
    
    elif choice == "4":
        print("\n📄 Gestionnaire IA")
        from src.ia.report_generator import AIReportGenerator
        
        ia = AIReportGenerator()
        
        sample_data = {
            "id": "C-001",
            "type": "Qualité Air",
            "statut": "ACTIF",
            "error_rate": 2.5,
            "recent_measurements": [42, 45, 43, 48]
        }
        
        print(f"\n  Génération rapport pour capteur {sample_data['id']}...")
        try:
            report = ia.generate_sensor_report(sample_data)
            print(f"\n  {report}")
        except Exception as e:
            print(f"  ❌ Erreur: {str(e)}")
    
    elif choice == "5":
        print("\n🧪 Exécution des tests...")
        os.system("pytest tests/ -v --cov=src")
    
    elif choice == "6":
        print("\n👋 Au revoir!")
        sys.exit(0)
    
    else:
        print("\n❌ Option invalide")

if __name__ == "__main__":
    main()
