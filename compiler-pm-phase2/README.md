# 🏗️ PM-Compilation     : Smart City avec Automates & Compilateur

**Plateforme intelligente de gestion urbaine avec langage naturel et automates**

## 📋 Vue d'Ensemble

Ce projet est la **deuxième phase** de la plateforme SensorLinker. Il ajoute:

- ✅ **Compilateur NL→SQL**: Transforme les requêtes en langage naturel en SQL
- ✅ **Automates à États Finis**: Gestion des workflows métier (capteurs, interventions, véhicules)
- ✅ **IA Générative**: Rapport automatiques et suggestions d'actions
- ✅ **Dashboard Interactif**: Interface conviviale pour tous les modules

## 🎯 Objectives

- Appliquer **théorie des langages** formels
- Modéliser workflows complexes avec **automates**
- Intégrer **LLMs** (Large Language Models) pour IA générative
- Développer une **architecture complète** professionnelle

## 📊 Structure du Projet

```
compiler-pm-phase2/
├── src/
│   ├── compiler/              # Moteur NL→SQL
│   │   ├── __init__.py
│   │   ├── lexer.py           # Tokenization
│   │   ├── parser.py          # Analyse syntaxique
│   │   ├── ast.py             # Arbre syntaxique
│   │   ├── codegen.py         # Génération SQL
│   │   ├── grammar.py         # Définition grammaire
│   │   └── compiler.py        # Orchestrateur
│   │
│   ├── automata/              # Automates à états finis
│   │   ├── __init__.py
│   │   ├── base.py            # Classe de base automate
│   │   ├── sensor_automata.py # AEF cycle capteur
│   │   ├── intervention_automata.py # AEF validation intervention
│   │   ├── vehicle_automata.py # AEF trajet véhicule
│   │   └── engine.py          # Orchestrateur automates
│   │
│   ├── ia/                    # Module IA générative
│   │   ├── __init__.py
│   │   ├── llm_provider.py    # Connexion LLM (OpenAI/Ollama)
│   │   ├── report_generator.py # Génération rapports
│   │   └── suggestions.py      # Suggestions actions
│   │
│   └── dashboard/             # Interface utilisateur
│       ├── __init__.py
│       ├── app.py             # App principale Streamlit
│       └── pages/             # Sous-pages
│
├── tests/
│   ├── conftest.py
│   ├── test_lexer.py          # Tests lexer
│   ├── test_parser.py         # Tests parser
│   ├── test_compiler.py       # Tests compilateur complet
│   ├── test_automata.py       # Tests automates
│   ├── test_ia.py             # Tests module IA
│   └── test_integration.py    # Tests intégration E2E
│
├── data/
│   ├── schema.sql             # Schéma BD
│   ├── seed.sql               # Données test (~1000 records)
│   └── test_cases.json        # Scénarios test
│
├── docs/
│   ├── GRAMMAR.md             # Grammaire complète
│   ├── ARCHITECTURE.md        # Design du système
│   ├── API.md                 # Utilisation APIs
│   └── DEPLOYMENT.md          # Guide déploiement
│
├── diagrams/
│   ├── sensor_automata.txt    # Diagramme GraphViz
│   ├── intervention_automata.txt
│   ├── vehicle_automata.txt
│   └── compiler_pipeline.txt
│
├── requirements.txt           # Dépendances Python
├── pytest.ini                 # Config pytest
├── .env.example               # Template variables d'env
├── main.py                    # Entrée principale
└── README.md                  # Ce fichier
```

## 🚀 Quick Start

### 1️⃣ Installation

```bash
# Cloner et naviguer
cd compiler-pm-phase2

# Créer environnement virtuel
python -m venv venv
source venv/Scripts/activate  # Windows
# ou
source venv/bin/activate      # Linux/Mac

# Installer dépendances
pip install -r requirements.txt
```

### 2️⃣ Configuration

```bash
# Copier template environnement
cp .env.example .env

# Éditer .env avec config locale
# - Base de données (PostgreSQL/MySQL)
# - Clé OpenAI (si utilisant GPT-4)
# - Ollama endpoint (si local)
```

### 3️⃣ Initialiser la Base de Données

```bash
# Créer schéma
psql -U postgres -d smart_city -f data/schema.sql

# Importer données test
psql -U postgres -d smart_city -f data/seed.sql
```

### 4️⃣ Tester

```bash
# Tests unitaires
pytest tests/ -v

# Avec couverture
pytest tests/ -v --cov=src

# Test spécifique
pytest tests/test_compiler.py -v
```

### 5️⃣ Lancer le Dashboard

```bash
# Démarrer Streamlit
streamlit run src/dashboard/app.py

# Interface disponible à: http://localhost:8501
```

### 6️⃣ Utilisation du Compilateur

```python
from src.compiler.compiler import Compiler

compiler = Compiler()

# Exemple: requête naturelle
nl_query = "Affiche les 5 zones les plus polluées"

# Compiler en SQL
sql = compiler.compile(nl_query)

print(sql)
# Output: SELECT zone, AVG(pollution) FROM mesures 
#         GROUP BY zone ORDER BY AVG(pollution) DESC LIMIT 5
```

## 📚 Modules Principaux

### Compilateur (src/compiler/)

**Pipeline de compilation:**
```
Requête NL
    ↓
Lexer (Tokenization): "Affiche" → TOKEN_VERBE, "les" → TOKEN_ARTICLE, ...
    ↓
Parser (Analyse syntaxique): Construire AST selon grammaire
    ↓
Sémantique: Vérifier validité (colonnes, tables, fonctions)
    ↓
Codegen (Génération SQL): Transformer AST en SQL exécutable
    ↓
SQL Query (Exécution)
```

**Grammaire supportée (EBNF simplifié):**
```ebnf
QUERY ::= "Affiche" | "Montre" | "Donne" COLUMNS FROM_CLAUSE [WHERE] [ORDER] [LIMIT]
COLUMNS ::= COLUMN | NUMBER COLUMN | "*"
FROM_CLAUSE ::= "de" | "du" ENTITY
WHERE ::= "où" CONDITION ["et" CONDITION]*
ORDER ::= "triées" | "ordonnées" "par" COLUMN
LIMIT ::= "les" NUMBER [PREMIER]
```

**Exemple:**
```
NL: "Combien de capteurs sont hors service?"
SQL: SELECT COUNT(*) FROM capteurs WHERE statut = 'hors_service'
```

### Automates (src/automata/)

**3 Automates Implémentés:**

1. **Cycle de vie Capteur**
   - États: INACTIF → ACTIF → SIGNALÉ → EN_MAINTENANCE → HORS_SERVICE
   - Événements: installation, détection_anomalie, réparation, panne

2. **Validation d'Intervention**
   - États: DEMANDE → TECH1_ASSIGNÉ → TECH2_VALIDE → IA_VALIDE → TERMINÉ
   - Workflow avec validations multiples

3. **Trajet Véhicule Autonome**
   - États: STATIONNÉ → EN_ROUTE → EN_PANNE → ARRIVÉ
   - Gestion circulation urbaine

**Usage:**

```python
from src.automata.engine import AutomataEngine

engine = AutomataEngine()

# Créer instance automate capteur
automata = engine.create_sensor_automata("C-001")

# Déclencher événements
automata.trigger("installation")  # INACTIF → ACTIF
automata.trigger("detection_anomalie")  # ACTIF → SIGNALÉ

# Vérifier transitions valides
if automata.is_valid_transition("réparation"):
    automata.trigger("réparation")

# État courant
print(automata.get_state())  # → "EN_MAINTENANCE"

# Historique
print(automata.history)  # Trace complète transitions
```

### IA Générative (src/ia/)

**Fonctionnalités:**

- 📊 Génération de rapports contextuels
- 💡 Suggestions d'actions intelligentes
- ✓ Validation de séquences d'interventions
- 📈 Analyse de tendances

**Usage:**

```python
from src.ia.report_generator import AIReportGenerator

ia = AIReportGenerator(api_provider="openai", model="gpt-4")

# Générer rapport capteur
sensor_data = {
    "id": "C-001",
    "type": "Qualité air",
    "statut": "ACTIF",
    "error_rate": 2.5,
    "recent_measurements": [42, 45, 43, 48]
}

report = ia.generate_sensor_report(sensor_data)
# Output: "Le capteur C-001 fonctionne correctement avec un taux d'erreur de 2.5%..."

# Suggestions d'action
suggestion = ia.suggest_intervention(sensor_data)
# Output: "✓ Le capteur fonctionne normalement."
```

### Dashboard (src/dashboard/)

Interface Streamlit avec plusieurs pages:

- 📊 **Dashboard**: Vue d'ensemble système
- 🔤 **Requêtes NL→SQL**: Tester compilateur en direct
- 🤖 **Automates**: Visualiser et contrôler automates
- 📄 **Rapports IA**: Consulter rapports générés
- ⚙️ **Paramètres**: Configuration système

## 🧪 Tests

### Couverture Requise

- ✓ Lexer: 90% couverture
- ✓ Parser: 85% couverture
- ✓ Automates: 95% couverture
- ✓ IA: 70% couverture
- ✓ Intégration: 10 scénarios

### Exemples de Tests

```bash
# Test compilateur simple
pytest tests/test_compiler.py::test_simple_query -v

# Test automate avec transition invalide
pytest tests/test_automata.py::test_invalid_transition -v

# Test intégration complète (E2E)
pytest tests/test_integration.py::test_complete_workflow -v

# Tous les tests
pytest tests/ -v --cov=src --cov-report=html
```

## 📊 Données

### Schéma Principal (schema.sql)

Tables principales héritées de SensorLinker:
- `capteurs` (200+ enregistrements)
- `interventions` (100+ enregistrements)
- `mesures` (2000+ série temporelle)
- `citoyens` (500+ enregistrements)
- `vehicules` (50+ enregistrements)
- `techniciens` (30+ enregistrements)

### Génération de Données

```bash
# Seed données depuis script
python data/generate_seed.py

# Importer dans BD
psql -d smart_city -f data/seed_generated.sql
```

## 📈 Performance

**Objectifs:**
- ✓ Compilation NL→SQL < 100ms
- ✓ Dashboard chargement < 2s
- ✓ Automate transition < 10ms
- ✓ IA génération rapport < 5s

**Monitoring:**

```python
from src.compiler.compiler import Compiler

compiler = Compiler()
result = compiler.compile("Affiche les 5 zones polluées", debug=True)
# Output: Temps lexer: 2ms, Temps parser: 5ms, Temps codegen: 3ms
```

## 🔐 Variables d'Environnement

```bash
# .env
DATABASE_URL=postgresql://user:password@localhost/smart_city
DATABASE_PORT=5432

OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4

# Si utilisant Ollama (local)
OLLAMA_API_URL=http://localhost:11434
OLLAMA_MODEL=llama2

# Debug mode
DEBUG=true
```

## 📖 Documentation

- [GRAMMAR.md](docs/GRAMMAR.md) - Spécification grammaire EBNF complète
- [ARCHITECTURE.md](docs/ARCHITECTURE.md) - Design patterns et architecture
- [API.md](docs/API.md) - Endpoints et utilisation APIs
- [DEPLOYMENT.md](docs/DEPLOYMENT.md) - Guide production

## 🎯 Critères d'Évaluation

| Critère | Poids | Status |
|---------|-------|--------|
| Modélisation automates | 25% | 🔄 En cours |
| Implémentation compilateur | 30% | 🔄 En cours |
| Interface dashboard | 20% | 🔄 En cours |
| Données & Tests | 15% | 🔄 En cours |
| Innovation | 10% | 🔄 En cours |

## 💡 Bonus Points

- +5%: Gestion requêtes ambigües avec résolution IA
- +5%: Intégration TimescaleDB (séries temporelles)
- +5%: Visualisation graphique animated des automates

## 🤝 Stack Technique

```
Backend:
  ├── Python 3.10+
  ├── PostgreSQL 14
  ├── SQLAlchemy (ORM)
  └── transitions (state machine)

IA:
  ├── OpenAI GPT-4 (cloud)
  ├── Ollama (local alternative)
  └── LangChain (orchestration)

Frontend:
  ├── Streamlit (dashboard)
  ├── Plotly (charts)
  └── Graphviz (diagrams)

Testing:
  ├── pytest
  ├── pytest-cov
  └── pytest-mock
```

## 🚦 Roadmap

- [x] Phase 1: Planification & Modélisation
- [ ] Semaine 1: Finir modélisation automates
- [ ] Semaine 2-3: Implémenter compilateur
- [ ] Semaine 3-4: Automates engine
- [ ] Semaine 4-5: IA générative
- [ ] Semaine 5-6: Dashboard + Tests + Polish

## 📞 Support

**Pour questions:**

- **Compilateur**: Voir [GRAMMAR.md](docs/GRAMMAR.md)
- **Automates**: Voir cours "Théorie des Langages"
- **IA**: Voir documentation OpenAI/LangChain
- **Architecture**: Voir [ARCHITECTURE.md](docs/ARCHITECTURE.md)

## 📝 License

MIT License - Voir LICENSE

---

**Version**: 1.0  
**Last Updated**: 26 Mars 2026  
**Status**: 🟡 In Development  
**Team**: Firaz Mrabett + ...
