"""
Rapport PDF — SensorLinker Neo-Sousse Smart City
Part 3: Chapitres 6-9 + Main
"""

def write_chapter6(pdf):
    """Chapitre 6: Dashboard et Interface"""
    pdf.chapter_title("Dashboard et Interface Utilisateur")
    
    pdf.section_title("Dashboard Streamlit")
    pdf.body_text(
        "Le dashboard principal (app_v3.py) est developpe avec Streamlit et offre une "
        "interface complete pour la gestion de la Smart City. Il comprend les pages suivantes :"
    )
    pdf.bullet_list([
        "Accueil : Resume executif avec KPIs en temps reel, statistiques globales",
        "Capteurs IoT : Liste, filtres par type/statut, simulation temps reel des mesures",
        "Interventions : Gestion du workflow d'intervention avec validation IA",
        "Vehicules : Tracking GPS en temps reel avec carte Folium satellite",
        "Citoyens : Engagement citoyen, scores ecologiques, participations",
        "Compilateur NL-SQL : Interface de compilation avec execution SQL",
        "Automates : Visualisation des 3 DFA avec diagrammes Graphviz interactifs",
        "Alertes : Monitoring des alertes automatiques par severite",
        "Rapports IA : Generation de rapports personnalises par IA generative",
    ])
    
    pdf.section_title("Authentification Google OAuth 2.0")
    pdf.body_text(
        "L'authentification utilise exclusivement Google OAuth 2.0 pour un SSO securise. "
        "L'interface de connexion adopte un design Glassmorphism premium avec une carte "
        "professionnelle centree. Le flux OAuth redirige vers localhost:8502 et gere "
        "automatiquement la creation de session Streamlit."
    )
    pdf.code_block(
        "# Flux d'authentification\n"
        "1. Utilisateur clique 'Se connecter avec Google'\n"
        "2. Redirection vers Google OAuth consent screen\n"
        "3. Google renvoie authorization code vers redirect URI\n"
        "4. Backend echange le code contre access token + ID token\n"
        "5. Extraction email/nom depuis ID token (JWT)\n"
        "6. Creation de session Streamlit (st.session_state)\n"
        "7. Redirection vers le dashboard principal",
        "Flux Google OAuth 2.0"
    )
    
    pdf.section_title("Simulation Temps Reel IoT")
    pdf.body_text(
        "Le module realtime_simulator.py execute un thread daemon qui genere des donnees "
        "simulees toutes les 2 secondes :"
    )
    pdf.bullet_list([
        "Capteurs actifs : mesures aleatoires selon le type (temperature, NO2, PM2.5, etc.)",
        "Capteurs en maintenance/HS : valeurs nulles ou erratiques",
        "Vehicules en route : coordonnees GPS dynamiques autour de Sousse",
        "Vehicules stationnes : position fixe avec micro-variations",
    ])
    pdf.body_text(
        "Le simulateur utilise sa propre connexion MySQL dediee pour eviter les conflits "
        "de curseur avec le thread principal de Streamlit. Les donnees sont inserees dans "
        "les tables Mesures1 (capteurs) et mises a jour dans Vehicule (coordonnees GPS)."
    )
    
    pdf.section_title("Dashboard React")
    pdf.body_text(
        "Un dashboard secondaire React/Vite offre une SPA moderne avec visualisations "
        "interactives. Il communique avec la meme base de donnees MySQL via une API backend "
        "et offre des vues complementaires pour les statistiques et le monitoring."
    )


def write_chapter7(pdf):
    """Chapitre 7: Base de Donnees Detaillee"""
    pdf.chapter_title("Base de Donnees Detaillee")
    
    pdf.section_title("Schema Relationnel")
    pdf.body_text(
        "La base de donnees sousse_smart_city_projet_module comprend 17 tables avec des "
        "relations definies par cles etrangeres. Le schema suit les formes normales (3NF) "
        "pour minimiser la redondance."
    )
    
    pdf.body_text("Tables principales et leurs colonnes :")
    
    # Capteur
    pdf.table(
        ["Colonne", "Type", "Contrainte", "Description"],
        [
            ["UUID", "CHAR(36)", "PK", "Identifiant unique"],
            ["Type", "ENUM", "", "Eclairage/Dechets/Trafic/Energie/Air"],
            ["Latitude", "DECIMAL", "", "Position GPS"],
            ["Longitude", "DECIMAL", "", "Position GPS"],
            ["Statut", "ENUM", "", "Actif/En Maint./Hors Service/Signale"],
            ["Date Installation", "DATETIME", "", "Date de deploiement"],
            ["IDP", "INT", "FK->Proprietaire", "Proprietaire du capteur"],
        ],
        [38, 30, 42, 80]
    )
    
    # Intervention
    pdf.table(
        ["Colonne", "Type", "Contrainte", "Description"],
        [
            ["IDIn", "INT", "PK AUTO_INCR", "Identifiant"],
            ["DateHeure", "DATETIME", "", "Date de l'intervention"],
            ["Nature", "ENUM", "", "Predictive/Corrective/Curative"],
            ["Duree", "INT", "", "Duree en minutes"],
            ["Cout", "DECIMAL", "", "Cout de l'intervention"],
            ["ImpactCO2", "DECIMAL", "", "CO2 economise (kg)"],
            ["UUID", "CHAR(36)", "FK->Capteur", "Capteur concerne"],
            ["statut", "ENUM", "", "Workflow automate"],
            ["technicien_1_id", "INT", "FK->Technicien", "Tech assignee"],
            ["technicien_2_id", "INT", "FK->Technicien", "Tech validateur"],
        ],
        [38, 30, 42, 80]
    )
    
    pdf.section_title("Tables et Relations FK")
    pdf.body_text(
        "Le graphe des cles etrangeres permet au SchemaRegistry de resoudre "
        "automatiquement les JOIN entre tables via un algorithme BFS."
    )
    
    pdf.table(
        ["Relation FK", "Table Source", "Table Cible", "Colonnes"],
        [
            ["Capteur->Proprietaire", "capteur", "proprietaire", "IDP->IDP"],
            ["Mesures1->Capteur", "mesures1", "capteur", "UUID->UUID"],
            ["Mesures1->Mesures2", "mesures1", "mesures2", "NomGrandeur->NomGrandeur"],
            ["Intervention->Capteur", "intervention", "capteur", "UUID->UUID"],
            ["Intervention->Tech1", "intervention", "technicien", "tech_1_id->IDT"],
            ["Intervention->Tech2", "intervention", "technicien", "tech_2_id->IDT"],
            ["Consultation->Citoyen", "consultation", "citoyen", "IDCI->IDCI"],
            ["Participation->Citoyen", "participation", "citoyen", "IDCI->IDCI"],
            ["Participation->Consult", "participation", "consultation", "IDCO->IDCO"],
            ["Trajet->Vehicule", "trajet", "vehicule", "Plaque->Plaque"],
            ["Supervision->Interv", "supervision", "intervention", "IDIn->IDIn"],
            ["Supervision->Tech", "supervision", "technicien", "IDT->IDT"],
            ["RapportsIA->Interv", "rapports_ia", "intervention", "interv_id->IDIn"],
        ],
        [40, 38, 38, 74]
    )
    
    pdf.body_text(
        "Les tables d'historique (capteurs_history, interventions_history, vehicles_history) "
        "et la table logs_automata assurent la tracabilite complete de toutes les transitions "
        "d'automates avec horodatage, ancien et nouvel etat, et raison du declenchement."
    )


def write_chapter8(pdf):
    """Chapitre 8: Tests et Validation"""
    pdf.chapter_title("Tests et Validation")
    
    pdf.section_title("Strategie de Test")
    pdf.body_text(
        "La validation du projet couvre l'ensemble des composants a travers plusieurs "
        "niveaux de tests :"
    )
    
    pdf.table(
        ["Niveau", "Composant", "Methode", "Resultat"],
        [
            ["Unitaire", "Lexer", "Tokenisation de 20+ requetes", "OK"],
            ["Unitaire", "Parser", "Parsing de requetes SELECT/COUNT/AVG", "OK"],
            ["Unitaire", "CodeGen", "Generation SQL avec JOIN", "OK"],
            ["Unitaire", "Automates", "Transitions valides et invalides", "OK"],
            ["Integration", "Compilateur E2E", "NL -> SQL -> Execution", "OK"],
            ["Integration", "Automates + BD", "Persistance transitions", "OK"],
            ["Integration", "IA + BD", "Rapports depuis donnees reelles", "OK"],
            ["Systeme", "Dashboard", "Navigation complete", "OK"],
            ["Systeme", "Auth Google", "Flux OAuth complet", "OK"],
            ["Systeme", "Simulation", "Thread daemon + BD", "OK"],
        ],
        [30, 40, 60, 60]
    )
    
    pdf.section_title("Tests du Compilateur")
    pdf.body_text("Exemples de requetes testees avec succes :")
    pdf.code_block(
        "# Test 1: Requete simple\n"
        "NL:  'afficher les capteurs actifs'\n"
        "SQL: SELECT * FROM capteur WHERE Statut = 'Actif'\n\n"
        "# Test 2: Avec agregation\n"
        "NL:  'compter les interventions correctives'\n"
        "SQL: SELECT COUNT(*) FROM intervention WHERE Nature = 'Corrective'\n\n"
        "# Test 3: Avec JOIN automatique\n"
        "NL:  'afficher les mesures du capteur abc-123'\n"
        "SQL: SELECT m.* FROM mesures1 m\n"
        "     JOIN capteur c ON m.UUID = c.UUID\n"
        "     WHERE c.UUID = 'abc-123'\n\n"
        "# Test 4: Multi-tables\n"
        "NL:  'moyenne des valeurs de no2'\n"
        "SQL: SELECT AVG(Valeur) FROM mesures1\n"
        "     WHERE NomGrandeur = 'NO2'",
        "Exemples de tests du compilateur"
    )
    
    pdf.section_title("Tests des Automates")
    pdf.body_text("Verification des sequences valides et invalides :")
    pdf.code_block(
        "# Sequence valide (capteur)\n"
        "events = ['installation', 'detection_anomalie', 'reparation',\n"
        "          'reparation_complete']\n"
        "result = capteur.verify_sequence(events)\n"
        "# -> valid=True, accepted=True, final_state='Actif'\n\n"
        "# Sequence invalide\n"
        "events = ['panne']  # depuis Inactif\n"
        "result = capteur.verify_sequence(events)\n"
        "# -> valid=False, error: delta(Inactif, panne) = vide",
        "Tests de verification de sequences"
    )


def write_chapter9(pdf):
    """Chapitre 9: Conclusion"""
    pdf.chapter_title("Conclusion et Perspectives")
    
    pdf.section_title("Bilan du Projet")
    pdf.body_text(
        "Le projet SensorLinker a permis de mettre en pratique les concepts fondamentaux "
        "de la theorie des langages et de la compilation dans un contexte applicatif concret "
        "et innovant : la gestion d'une ville intelligente."
    )
    pdf.body_text("Realisations principales :")
    pdf.bullet_list([
        "Compilateur NL-SQL complet : Pipeline en 4 phases (Lexer, Parser, Semantic, CodeGen) "
        "capable de traduire des requetes en francais naturel vers du SQL executable avec "
        "resolution automatique des JOIN via BFS",
        "3 Automates DFA : Modelisation formelle des cycles de vie (Capteur, Intervention, "
        "Vehicule) avec persistance BD, diagrammes Graphviz et verification de sequences",
        "IA Generative : Integration Ollama Cloud API pour rapports intelligents, validation "
        "d'interventions avec diagnostic et 3 solutions, et rapports personnalises",
        "Dashboard temps reel : Simulation IoT avec mesures et tracking GPS en temps reel, "
        "interface professionnelle avec authentification Google OAuth 2.0",
        "Base de donnees : Schema relationnel de 17 tables avec SchemaRegistry centralise "
        "et graphe FK pour resolution automatique des jointures",
        "Moteur d'alertes : Surveillance automatique avec 4 niveaux de severite et actions "
        "correctives recommandees",
    ])
    
    pdf.section_title("Perspectives")
    pdf.body_text("Plusieurs axes d'amelioration sont envisageables :")
    pdf.bullet_list([
        "Extension du compilateur : Support des requetes UPDATE, sous-requetes, et "
        "expressions complexes (HAVING, CASE WHEN)",
        "Automates NFA : Extension vers les automates non-deterministes pour modeliser "
        "des processus plus complexes avec epsilon-transitions",
        "IA avancee : Fine-tuning d'un modele specialise Smart City, et integration "
        "de graphes de connaissances pour ameliorer la pertinence des rapports",
        "Deploiement cloud : Migration vers une infrastructure cloud (GCP/Firebase) "
        "avec CI/CD et monitoring de production",
        "Capteurs reels : Integration de capteurs physiques via protocole MQTT pour "
        "remplacer la simulation par des donnees reelles",
        "Application mobile : Developpement d'une app React Native pour le monitoring "
        "en mobilite et les notifications push d'alertes",
    ])
    
    pdf.body_text(
        "Ce projet demontre que les fondements theoriques de la compilation et de la "
        "theorie des automates trouvent des applications directes et concretes dans le "
        "developpement de systemes intelligents modernes. La synergie entre compilation, "
        "automates et IA generative ouvre des perspectives prometteuses pour la gestion "
        "urbaine de demain."
    )
    
    # Page de references
    pdf.add_page()
    pdf.set_font('Helvetica', 'B', 18)
    pdf.set_text_color(0, 51, 102)
    pdf.cell(0, 12, 'References', 0, 1, 'L')
    pdf.ln(5)
    
    refs = [
        "A. Aho, M. Lam, R. Sethi, J. Ullman - Compilers: Principles, Techniques, and Tools (Dragon Book), 2nd Ed., Pearson, 2006",
        "J.E. Hopcroft, R. Motwani, J.D. Ullman - Introduction to Automata Theory, Languages, and Computation, 3rd Ed., Pearson, 2006",
        "Cours 3_AutomatesAEtatsFinis TL - Support de cours du module TLC, ISATSo 2025-2026",
        "Enonce PM-Compilation-25-26 - Cahier des charges du projet, ISATSo",
        "Streamlit Documentation - https://docs.streamlit.io/",
        "Ollama API Documentation - https://ollama.com/docs/api",
        "MySQL 8.0 Reference Manual - https://dev.mysql.com/doc/refman/8.0/",
        "Google OAuth 2.0 Documentation - https://developers.google.com/identity/protocols/oauth2",
        "Graphviz DOT Language - https://graphviz.org/doc/info/lang.html",
        "Plotly Python Documentation - https://plotly.com/python/",
    ]
    
    pdf.set_font('Helvetica', '', 9)
    pdf.set_text_color(40, 40, 40)
    for i, ref in enumerate(refs, 1):
        pdf.multi_cell(0, 5, f"[{i}] {ref}")
        pdf.ln(2)


def generate_full_report():
    """Point d'entree principal : genere le rapport complet"""
    import os, sys
    
    # Add parent to path for imports
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    
    from generate_report_part1 import SmartCityPDF
    from generate_report_part2 import write_chapter1, write_chapter2, write_chapter3, write_chapter4, write_chapter5
    
    print("=" * 60)
    print("  SensorLinker - Generation du Rapport PDF")
    print("=" * 60)
    
    pdf = SmartCityPDF()
    
    # Page de garde
    print("[1/9] Page de garde...")
    pdf.cover_page()
    
    # Table des matieres
    print("[2/9] Table des matieres...")
    pdf.add_toc()
    
    # Chapitres 1-5
    print("[3/9] Chapitre 1 : Introduction...")
    write_chapter1(pdf)
    
    print("[4/9] Chapitre 2 : Architecture...")
    write_chapter2(pdf)
    
    print("[5/9] Chapitre 3 : Compilateur...")
    write_chapter3(pdf)
    
    print("[6/9] Chapitre 4 : Automates...")
    write_chapter4(pdf)
    
    print("[7/9] Chapitre 5 : IA...")
    write_chapter5(pdf)
    
    # Chapitres 6-9
    print("[8/9] Chapitres 6-8 : Dashboard, BD, Tests...")
    write_chapter6(pdf)
    write_chapter7(pdf)
    write_chapter8(pdf)
    
    print("[9/9] Chapitre 9 : Conclusion...")
    write_chapter9(pdf)
    
    # Sauvegarder
    output_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(output_dir, "Rapport_SensorLinker_TLC_2025_2026.pdf")
    pdf.output(output_path)
    
    print(f"\n{'=' * 60}")
    print(f"  Rapport genere avec succes !")
    print(f"  Fichier : {output_path}")
    print(f"  Pages   : {pdf.page_no()}")
    print(f"{'=' * 60}")
    
    return output_path


if __name__ == "__main__":
    generate_full_report()
