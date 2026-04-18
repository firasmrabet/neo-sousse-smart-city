"""
Rapport PDF — SensorLinker Neo-Sousse Smart City
Part 2: Contenu des chapitres 1-5
"""

def write_chapter1(pdf):
    """Chapitre 1: Introduction Generale"""
    pdf.chapter_title("Introduction Generale")
    
    pdf.section_title("Contexte du Projet")
    pdf.body_text(
        "Le projet SensorLinker s'inscrit dans le cadre du module Theorie des Langages "
        "et Compilation (TLC) de l'annee universitaire 2025-2026. Il repond a la vision Neo-Sousse 2030 "
        "visant a transformer la ville de Sousse en Smart City a travers le deploiement massif de "
        "capteurs IoT, la gestion intelligente des interventions techniques et la mobilite durable."
    )
    pdf.body_text(
        "La plateforme SensorLinker constitue un systeme complet integrant un compilateur "
        "de langage naturel vers SQL, des automates a etats finis pour la gestion du cycle de vie "
        "des entites urbaines, et un module d'intelligence artificielle generative pour l'aide "
        "a la decision. Le tout est orchestre par un dashboard interactif temps reel."
    )
    
    pdf.section_title("Objectifs du Projet")
    pdf.body_text("Le projet poursuit les objectifs pedagogiques et techniques suivants :")
    pdf.bullet_list([
        "Concevoir un compilateur complet (Lexer, Parser, Semantic Analyzer, Code Generator) "
        "transformant des requetes en francais naturel en SQL executable",
        "Implementer trois automates DFA conformes au formalisme A = (Q, Sigma, delta, q0, F) "
        "pour modeliser les cycles de vie des capteurs, interventions et vehicules",
        "Integrer un module IA generative (Ollama/OpenAI) pour la generation de rapports "
        "intelligents et la validation automatique des interventions",
        "Developper un dashboard temps reel avec simulation IoT et tracking GPS",
        "Mettre en oeuvre une base de donnees relationnelle MySQL (17 tables) avec un "
        "registre de schema centralise",
        "Deployer un moteur d'alertes automatiques conforme aux exigences du cahier des charges",
    ])
    
    pdf.section_title("Technologies Utilisees")
    pdf.table(
        ["Composant", "Technologie", "Role"],
        [
            ["Backend Compilateur", "Python 3.11", "Lexer, Parser, CodeGen"],
            ["Dashboard Principal", "Streamlit", "Interface utilisateur"],
            ["Dashboard Secondaire", "React + Vite", "SPA moderne"],
            ["Base de Donnees", "MySQL 8.0", "Persistance"],
            ["IA Generative", "Ollama Cloud API", "Rapports intelligents"],
            ["Authentification", "Google OAuth 2.0", "SSO securise"],
            ["Visualisation", "Plotly, Folium", "Graphiques, cartes GPS"],
            ["Automates", "Graphviz DOT", "Diagrammes de transition"],
            ["Simulation", "Threading Python", "Donnees temps reel"],
        ],
        [50, 50, 90]
    )


def write_chapter2(pdf):
    """Chapitre 2: Architecture du Systeme"""
    pdf.chapter_title("Architecture du Systeme")
    
    pdf.section_title("Architecture Globale")
    pdf.body_text(
        "SensorLinker adopte une architecture modulaire en couches, separant clairement "
        "les preoccupations entre la couche de presentation (dashboards), la couche metier "
        "(compilateur, automates, IA) et la couche de donnees (MySQL). Cette architecture "
        "garantit la maintenabilite, l'extensibilite et la testabilite du systeme."
    )
    
    pdf.info_box(
        "Architecture en Couches",
        "Presentation (Streamlit/React) -> Metier (Compilateur/Automates/IA) -> Donnees (MySQL 17 tables)"
    )
    
    pdf.body_text(
        "Couche Presentation : Deux dashboards complementaires. Streamlit pour le monitoring IoT "
        "avance avec simulation temps reel, compilation NL-SQL et gestion des automates. "
        "React/Vite pour une SPA moderne avec visualisations interactives."
    )
    pdf.body_text(
        "Couche Metier : Le compilateur NL-SQL transforme les requetes en francais en SQL via "
        "un pipeline Lexer -> Parser -> Semantic Analyzer -> Code Generator. Les automates DFA "
        "modelisent les cycles de vie. Le module IA (Ollama Cloud) genere des rapports et valide "
        "les interventions avec un taux de confiance."
    )
    pdf.body_text(
        "Couche Donnees : MySQL 8.0 avec 17 tables interconnectees. Le SchemaRegistry centralise "
        "la connaissance du schema et sert de source unique de verite pour le compilateur."
    )
    
    pdf.section_title("Structure du Projet")
    pdf.code_block(
        "SensorLinker/\n"
        "  compiler-pm-phase2/\n"
        "    src/\n"
        "      compiler/           # Pipeline de compilation NL -> SQL\n"
        "        lexer.py          # Analyse lexicale (tokenisation)\n"
        "        parser.py         # Analyse syntaxique (AST)\n"
        "        semantic_analyzer.py  # Analyse semantique\n"
        "        codegen.py        # Generation de code SQL\n"
        "        schema_registry.py    # Registre du schema BD\n"
        "      automata/           # Automates a etats finis\n"
        "        base.py           # Classe abstraite DFA\n"
        "        automata.py       # 3 automates concrets\n"
        "        alert_engine.py   # Moteur d'alertes\n"
        "      dashboard/          # Interface utilisateur\n"
        "        app_v3.py         # Dashboard Streamlit principal\n"
        "        auth.py           # Auth Google OAuth 2.0\n"
        "      ia/                 # Intelligence Artificielle\n"
        "        report_generator.py   # Rapports IA + Validation\n"
        "      realtime_simulator.py   # Simulation IoT temps reel\n"
        "      db_connection.py    # Connexion MySQL singleton\n"
        "  frontend/              # Dashboard React/Vite\n"
        "  SQL_QUERIES.sql        # Requetes SQL de reference",
        "Arborescence du projet"
    )
    
    pdf.section_title("Base de Donnees - Vue d'Ensemble")
    pdf.body_text(
        "La base de donnees sousse_smart_city_projet_module comprend 17 tables "
        "organisees en 4 domaines fonctionnels : IoT et Capteurs, Interventions Techniques, "
        "Mobilite Durable, et Engagement Citoyen. Les tables d'historique et de logs "
        "assurent la tracabilite complete des transitions d'automates."
    )
    pdf.table(
        ["Domaine", "Tables", "Description"],
        [
            ["IoT", "Capteur, Mesures1, Mesures2, Proprietaire", "Capteurs et mesures"],
            ["Interventions", "Intervention, Technicien, Supervision", "Maintenance"],
            ["Mobilite", "Vehicule, Trajet", "Vehicules autonomes"],
            ["Citoyens", "Citoyen, Consultation, Participation", "Engagement"],
            ["Historique", "capteurs_history, interventions_history, vehicles_history", "Tracabilite"],
            ["Systeme", "logs_automata, rapports_ia", "Logs et IA"],
        ],
        [35, 85, 70]
    )


def write_chapter3(pdf):
    """Chapitre 3: Compilateur NL vers SQL"""
    pdf.chapter_title("Compilateur NL vers SQL")
    
    pdf.body_text(
        "Le compilateur SensorLinker transforme des requetes en langage naturel francais en "
        "requetes SQL executables. Il suit le pipeline classique de compilation en quatre phases : "
        "analyse lexicale, analyse syntaxique, analyse semantique et generation de code."
    )
    
    pdf.info_box(
        "Pipeline de Compilation",
        "Texte Francais -> [Lexer] -> Tokens -> [Parser] -> AST -> [Semantic] -> AST valide -> [CodeGen] -> SQL"
    )
    
    # Section 3.1: Lexer
    pdf.section_title("Analyse Lexicale (Lexer)")
    pdf.body_text(
        "Le Lexer (lexer.py, ~600 lignes) decompose le texte en francais en une sequence de "
        "tokens types. Il utilise une approche par machine a etats avec des expressions regulieres "
        "pour identifier les differentes categories lexicales."
    )
    
    pdf.body_text("Categories de tokens reconnues :")
    pdf.bullet_list([
        "SELECT_KW : 'afficher', 'montrer', 'lister', 'donner', 'voir', 'quels', 'quelles'",
        "COUNT_KW : 'compter', 'nombre', 'combien', 'total'",
        "AVG_KW : 'moyenne', 'avg', 'moyen'",
        "MAX_KW / MIN_KW / SUM_KW : agregations (max, min, somme)",
        "WHERE_KW : 'ou', 'dont', 'avec', 'ayant', 'qui', 'pour'",
        "TABLE_REF : nom de table resolu via SchemaRegistry",
        "COLUMN_REF : nom de colonne resolu via synonymes",
        "VALUE : valeurs litterales (chaines, nombres, enums)",
        "OPERATOR : '=', '>', '<', '>=', '<=', '<>', 'entre'",
        "LOGIC : 'et', 'ou' (operateurs logiques)",
        "ORDER_KW : 'trier', 'ordonner', 'classer'",
        "GROUP_KW : 'grouper', 'par', 'regrouper'",
        "LIMIT_KW : 'limiter', 'premiers', 'top'",
    ])
    
    pdf.code_block(
        "# Exemple de tokenisation\n"
        "Input:  'afficher les capteurs actifs'\n"
        "Output: [\n"
        "  Token(SELECT_KW, 'afficher'),\n"
        "  Token(TABLE_REF, 'capteur'),\n"
        "  Token(VALUE, 'Actif')   # resolu via _status_synonyms\n"
        "]",
        "Exemple : Tokenisation d'une requete simple"
    )
    
    pdf.code_block(
        "class Lexer:\n"
        "    def tokenize(self, text: str) -> List[Token]:\n"
        "        words = self._split_text(text)\n"
        "        tokens = []\n"
        "        for word in words:\n"
        "            token = self._classify_word(word)\n"
        "            tokens.append(token)\n"
        "        return self._post_process(tokens)",
        "Structure du Lexer (simplifie)"
    )
    
    # Section 3.2: Parser
    pdf.section_title("Analyse Syntaxique (Parser)")
    pdf.body_text(
        "Le Parser (parser.py, ~800 lignes) implemente un analyseur syntaxique descendant "
        "recursif (Recursive Descent Parser). Il transforme la sequence de tokens en un Arbre "
        "Syntaxique Abstrait (AST) representant la structure logique de la requete."
    )
    
    pdf.body_text("Grammaire formelle (simplifiee) :")
    pdf.code_block(
        "Query      -> SelectQuery | CountQuery | AvgQuery | InsertQuery | DeleteQuery\n"
        "SelectQuery -> SELECT_KW Columns FROM_TABLE [WhereClause] [OrderClause] [LimitClause]\n"
        "Columns    -> '*' | ColumnList\n"
        "ColumnList -> Column (',' Column)*\n"
        "WhereClause-> WHERE_KW Condition (LOGIC Condition)*\n"
        "Condition  -> Column OPERATOR Value\n"
        "OrderClause-> ORDER_KW Column [ASC|DESC]\n"
        "LimitClause-> LIMIT_KW NUMBER",
        "Grammaire BNF du langage"
    )
    
    pdf.body_text("Structure de l'AST :")
    pdf.code_block(
        "ASTNode:\n"
        "  query_type: str          # 'SELECT', 'COUNT', 'AVG', etc.\n"
        "  tables: List[str]        # Tables impliquees\n"
        "  columns: List[str]       # Colonnes selectionnees\n"
        "  conditions: List[dict]   # Clauses WHERE\n"
        "  order_by: str            # Tri\n"
        "  limit: int               # Limite\n"
        "  aggregation: str         # Fonction d'agregation",
        "Structure du noeud AST"
    )
    
    # Section 3.3: Semantic Analyzer
    pdf.section_title("Analyse Semantique")
    pdf.body_text(
        "L'analyseur semantique (semantic_analyzer.py, 174 lignes) valide l'AST produit par "
        "le Parser en verifiant la coherence avec le schema de la base de donnees. Il detecte "
        "les erreurs de type, les references invalides et propose des reformulations."
    )
    pdf.bullet_list([
        "Verification de l'existence des tables referencees dans le SchemaRegistry",
        "Validation des colonnes par rapport aux tables (resolution de synonymes)",
        "Verification de la compatibilite des types pour les comparaisons",
        "Detection des valeurs d'enum invalides et suggestion de corrections",
        "Proposition de reformulations en cas d'ambiguite",
    ])
    
    # Section 3.4: Code Generator
    pdf.section_title("Generation de Code SQL")
    pdf.body_text(
        "Le generateur de code (codegen.py, 333 lignes) transforme l'AST valide en requetes "
        "SQL executables. Il gere automatiquement les JOIN via le graphe de relations du "
        "SchemaRegistry (algorithme BFS pour le chemin le plus court entre tables)."
    )
    
    pdf.code_block(
        "# Requete naturelle:\n"
        "'afficher les capteurs actifs avec leurs mesures'\n\n"
        "# SQL genere:\n"
        "SELECT c.UUID, c.Type, c.Statut, m.NomGrandeur, m.Valeur\n"
        "FROM capteur c\n"
        "JOIN mesures1 m ON c.UUID = m.UUID\n"
        "WHERE c.Statut = 'Actif'",
        "Exemple complet : NL -> SQL avec JOIN automatique"
    )
    
    pdf.body_text(
        "Le Code Generator resout automatiquement les backticks pour les colonnes contenant "
        "des espaces ou caracteres speciaux (ex: `Date Installation`, `Energie Utilisee`)."
    )
    
    # Section 3.5: Schema Registry
    pdf.section_title("Schema Registry")
    pdf.body_text(
        "Le SchemaRegistry (schema_registry.py, 724 lignes) est la source unique de verite "
        "pour la structure de la base de donnees. Il centralise :"
    )
    pdf.bullet_list([
        "17 tables avec leurs colonnes, types, cles primaires et etrangeres",
        "Graphe d'adjacence FK pour resolution automatique des JOIN via BFS",
        "Dictionnaire exhaustif de synonymes francais (200+ mots -> tables/colonnes)",
        "Valeurs d'enum connues pour chaque colonne (statuts, types, natures)",
        "Resolution de grandeurs physiques (NO2, PM2.5, Luminosite, etc.)",
    ])
    
    pdf.code_block(
        "class SchemaRegistry:    # Singleton\n"
        "    tables: Dict[str, TableDef]        # 17 tables\n"
        "    _adjacency: Dict[str, Dict]         # Graphe FK\n"
        "    _word_to_tables: Dict[str, List]     # Synonymes -> tables\n"
        "    _word_to_columns: Dict[str, List]    # Synonymes -> colonnes\n\n"
        "    def find_join_path(tables) -> List[Join]:  # BFS sur graphe FK\n"
        "    def resolve_table_name(word) -> str:       # 'voiture' -> 'vehicule'\n"
        "    def resolve_status(word) -> str:            # 'hs' -> 'Hors Service'",
        "API du SchemaRegistry"
    )


def write_chapter4(pdf):
    """Chapitre 4: Automates a Etats Finis"""
    pdf.chapter_title("Automates a Etats Finis")
    
    pdf.section_title("Formalisme DFA")
    pdf.body_text(
        "Conformement au cours de Theorie des Langages, chaque automate est defini "
        "formellement comme un quintuplet A = (Q, Sigma, delta, q0, F) ou :"
    )
    pdf.bullet_list([
        "Q : Ensemble fini d'etats",
        "Sigma : Alphabet (ensemble des evenements/symboles d'entree)",
        "delta : Fonction de transition  delta: Q x Sigma -> Q",
        "q0 : Etat initial (q0 appartient a Q)",
        "F : Ensemble des etats finaux (F inclus dans Q)",
    ])
    
    pdf.body_text(
        "La classe abstraite AutomataBase (base.py, 349 lignes) implemente ce formalisme "
        "avec : generation de la definition formelle, table de transition, verification de "
        "sequences, generation de diagrammes Graphviz DOT, et historique des transitions."
    )
    
    pdf.code_block(
        "class AutomataBase(ABC):   # A = (Q, Sigma, delta, q0, F)\n"
        "    def get_states() -> List[Enum]:       # Q\n"
        "    def get_alphabet() -> Set[str]:        # Sigma\n"
        "    def get_transitions() -> Dict:         # delta\n"
        "    def get_initial_state() -> Enum:       # q0\n"
        "    def get_final_states() -> List[Enum]:  # F\n"
        "    def trigger(event, actor) -> Enum:     # Executer delta(q, a)\n"
        "    def verify_sequence(events) -> Dict:   # Verifier w dans Sigma*\n"
        "    def to_graphviz_dot() -> str:          # Diagramme de transition",
        "Classe abstraite AutomataBase"
    )
    
    # Automate Capteur
    pdf.section_title("Automate 1 : Cycle de Vie d'un Capteur IoT")
    pdf.body_text("Definition formelle :")
    pdf.code_block(
        "A_capteur = (Q, Sigma, delta, q0, F)\n"
        "Q = {Inactif, Actif, Signale, En Maintenance, Hors Service}\n"
        "Sigma = {installation, detection_anomalie, reparation, reparation_complete,\n"
        "         panne, remplacement, reactivation, fausse_alerte}\n"
        "q0 = Inactif\n"
        "F = {Actif}",
        "Definition formelle de l'automate Capteur"
    )
    
    pdf.body_text("Table de transition delta :")
    pdf.table(
        ["Etat", "installation", "detection_anomalie", "reparation", "panne", "fausse_alerte"],
        [
            ["-> Inactif", "Actif", "-", "-", "-", "-"],
            ["* Actif", "-", "Signale", "-", "Hors Service", "-"],
            ["Signale", "-", "-", "En Maint.", "Hors Service", "Actif"],
            ["En Maint.", "-", "-", "-", "Hors Service", "-"],
            ["Hors Serv.", "-", "-", "-", "-", "-"],
        ],
        [30, 28, 38, 28, 34, 32]
    )
    
    # Automate Intervention
    pdf.section_title("Automate 2 : Validation d'Intervention")
    pdf.body_text("Cet automate modelise le workflow de validation impliquant 2 techniciens et l'IA :")
    pdf.code_block(
        "A_intervention = (Q, Sigma, delta, q0, F)\n"
        "Q = {Demande, Tech1_Assigne, Tech2_Valide, IA_Valide, Terminee, Rejetee}\n"
        "Sigma = {assigner_tech1, rapport_tech1, valider_ia, completer, rejeter, reinitialiser}\n"
        "q0 = Demande\n"
        "F = {Terminee}",
        "Definition formelle de l'automate Intervention"
    )
    
    pdf.table(
        ["Etat", "assigner_tech1", "rapport_tech1", "valider_ia", "completer", "rejeter"],
        [
            ["-> Demande", "Tech1_Assigne", "-", "-", "-", "Rejetee"],
            ["Tech1_Assigne", "-", "Tech2_Valide", "-", "-", "Rejetee"],
            ["Tech2_Valide", "-", "-", "IA_Valide", "-", "Rejetee"],
            ["IA_Valide", "-", "-", "-", "Terminee", "Rejetee"],
            ["* Terminee", "-", "-", "-", "-", "-"],
            ["Rejetee", "-", "-", "-", "-", "-"],
        ],
        [30, 32, 32, 32, 32, 32]
    )
    
    # Automate Vehicule
    pdf.section_title("Automate 3 : Trajet d'un Vehicule Autonome")
    pdf.code_block(
        "A_vehicule = (Q, Sigma, delta, q0, F)\n"
        "Q = {Stationne, En Route, En Panne, Arrive}\n"
        "Sigma = {demarrage, destination_atteinte, panne_detectee,\n"
        "         reparation_complete, remorquage, stationnement, redemarrage}\n"
        "q0 = Stationne\n"
        "F = {Arrive, Stationne}",
        "Definition formelle de l'automate Vehicule"
    )
    
    pdf.table(
        ["Etat", "demarrage", "dest_atteinte", "panne_detectee", "reparation", "remorquage"],
        [
            ["->* Stationne", "En Route", "-", "-", "-", "-"],
            ["En Route", "-", "Arrive", "En Panne", "-", "-"],
            ["En Panne", "-", "-", "-", "En Route", "Stationne"],
            ["* Arrive", "-", "-", "-", "-", "-"],
        ],
        [32, 30, 32, 34, 30, 32]
    )
    
    # Moteur d'alertes
    pdf.section_title("Moteur d'Alertes Automatiques")
    pdf.body_text(
        "Le moteur d'alertes (alert_engine.py, 350 lignes) surveille continuellement la base "
        "de donnees et declenche des alertes automatiques selon les regles definies dans "
        "l'enonce (section 2.2) :"
    )
    pdf.bullet_list([
        "CRITIQUE : Capteur hors service (seuil : 24h)",
        "HAUTE : Intervention en attente > 48h",
        "MOYENNE : Capteur en maintenance prolongee > 72h",
        "BASSE : Capteur actif sans donnees (aucune mesure enregistree)",
    ])
    
    pdf.body_text(
        "Chaque alerte comprend : un identifiant unique, un niveau de severite, le type "
        "d'entite concernee, un message descriptif et une action corrective recommandee. "
        "Les alertes sont triees par severite (CRITIQUE en premier) et archivees dans "
        "l'historique pour analyse."
    )


def write_chapter5(pdf):
    """Chapitre 5: Intelligence Artificielle"""
    pdf.chapter_title("Intelligence Artificielle Generative")
    
    pdf.section_title("Architecture IA")
    pdf.body_text(
        "Le module IA (report_generator.py, 734 lignes) integre un systeme multi-provider "
        "pour la generation de rapports intelligents. L'architecture supporte trois backends :"
    )
    pdf.bullet_list([
        "Ollama Cloud API (principal) : REST API avec Bearer token, modele llama3.2:3b",
        "Ollama Local : Instance locale pour le developpement hors-ligne",
        "OpenAI : Backend alternatif via OPENAI_API_KEY",
        "Fallback : Generation par templates quand aucun LLM n'est disponible",
    ])
    
    pdf.code_block(
        "class AIReportGenerator:\n"
        "    def __init__(provider='ollama_api', model='llama3.2:3b'):\n"
        "        # Initialise le provider avec fallback automatique\n\n"
        "    def _llm_generate(prompt, max_tokens=500) -> str:\n"
        "        # Appel unifie au LLM (REST/SDK)\n"
        "        # Nettoyage automatique du markdown (**,##,*)\n\n"
        "    # 4 types de rapports :\n"
        "    def generate_air_quality_report()     # Qualite de l'air\n"
        "    def suggest_intervention()             # Suggestion maintenance\n"
        "    def validate_intervention()            # Diagnostic + 3 solutions\n"
        "    def generate_custom_report()           # Rapport personnalise",
        "API du module IA"
    )
    
    pdf.section_title("Rapports Qualite de l'Air")
    pdf.body_text(
        "Le systeme genere des rapports de qualite de l'air en interrogeant les mesures "
        "des capteurs de type 'Qualite de l'air'. Les seuils OMS sont appliques : "
        "PM2.5 > 25 ug/m3, PM10 > 50 ug/m3, NO2 > 40 ppb. L'IA analyse les donnees "
        "et produit un rapport avec zones preoccupantes et recommandations."
    )
    
    pdf.section_title("Validation d'Interventions par IA")
    pdf.body_text(
        "Fonctionnalite avancee : l'IA valide les interventions et genere un diagnostic "
        "structure comprenant :"
    )
    pdf.bullet_list([
        "Diagnostic factuel du probleme et de l'intervention",
        "Solution principale recommandee",
        "Deux solutions alternatives",
        "Taux de confiance (0-100%)",
        "Duree estimee et cout estime",
        "Decision de validation (true/false)",
    ])
    
    pdf.body_text(
        "Le resultat est persiste dans la table rapports_ia avec le provider et le modele "
        "utilises, assurant la tracabilite complete des decisions IA."
    )
    
    pdf.section_title("Rapports Personnalises")
    pdf.body_text(
        "Le systeme permet de generer des rapports a la demande via langage naturel. "
        "Il detecte automatiquement les donnees pertinentes en analysant les mots-cles "
        "de la requete utilisateur (capteur, intervention, vehicule, citoyen) et "
        "construit le contexte adequat pour le LLM. Un mode fallback genere des rapports "
        "structures par templates quand le LLM est indisponible."
    )


if __name__ == "__main__":
    print("Part 2 OK - Chapitres 1-5 charges")
