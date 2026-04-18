"""
Compiler Facade — Point d'entrée unique pour la compilation NL → SQL
Pipeline: Texte → Lexer → Parser → Semantic Analyzer → CodeGen → SQL

Version universelle: supporte n'importe quelle requête en français
sur les 17 tables de la BD sousse_smart_city_projet_module.
"""

from typing import Dict, Any, Optional, List
from .lexer import Lexer, Token, TokenType
from .parser import Parser, ASTNode, ParseError
from .codegen import CodeGenerator
from .semantic_analyzer import SemanticAnalyzer, SemanticWarning


class CompilationResult:
    """Résultat d'une compilation NL → SQL"""
    def __init__(self):
        self.success: bool = False
        self.nl_input: str = ""
        self.sql: str = ""
        self.tokens: list = []
        self.ast: Optional[ASTNode] = None
        self.error: Optional[str] = None
        self.warnings: List[SemanticWarning] = []
        self.suggestions: List[str] = []
        self.lexer_errors: List[str] = []      # Erreurs lexicales
        self.unknown_words: List[str] = []     # Mots non reconnus
        self.derivation_tree: Optional[dict] = None  # Arbre de dérivation 

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "nl_input": self.nl_input,
            "sql": self.sql,
            "tokens": [{
                "type": t.type.value,
                "value": t.value,
                "position": t.position,
            } for t in self.tokens if t.type != TokenType.EOF],
            "ast_type": self.ast.node_type if self.ast else None,
            "error": self.error,
            "warnings": [str(w) for w in self.warnings],
            "suggestions": self.suggestions,
            "lexer_errors": self.lexer_errors,
            "unknown_words": self.unknown_words,
            "derivation_tree": self.derivation_tree,
        }


class Compiler:
    """
    Compilateur NL → SQL universel.

    Pipeline:
      1. Lexer: Texte → Tokens
      2. Parser: Tokens → AST (avec résolution dynamique via SchemaRegistry)
      3. Semantic Analyzer: AST → Warnings
      4. CodeGen: AST → SQL
    """

    def __init__(self):
        self.codegen = CodeGenerator()
        self.semantic = SemanticAnalyzer()

    def compile(self, nl_text: str) -> CompilationResult:
        """
        Compiler une requête en langage naturel vers SQL.

        Args:
            nl_text: Requête en français (n'importe quelle forme)

        Returns:
            CompilationResult avec SQL généré ou erreur
        """
        result = CompilationResult()
        result.nl_input = nl_text.strip()

        if not result.nl_input:
            result.error = "Requête vide"
            return result

        # Step 1: Tokenization (Lexer)
        try:
            lexer = Lexer(result.nl_input)
            result.tokens = lexer.tokenize()
            # Propager les erreurs lexicales (mots non reconnus, cf. Cours 6 fail())
            result.lexer_errors = lexer.errors
            result.unknown_words = lexer.unknown_words
        except SyntaxError as e:
            result.error = f"Erreur lexicale: {str(e)}"
            return result

        # Step 2: Parsing (AST)
        try:
            parser = Parser(result.tokens)
            result.ast = parser.parse()
            result.derivation_tree = parser.get_derivation_tree()
        except ParseError as e:
            result.error = f"Erreur syntaxique: {str(e)}"
            return result
        except Exception as e:
            result.error = f"Erreur d'analyse: {str(e)}"
            return result

        # Step 3: Semantic Analysis
        try:
            result.warnings = self.semantic.analyze(result.ast)
            result.suggestions = self.semantic.get_suggestions(result.nl_input)
        except Exception:
            pass  # Semantic analysis is non-blocking

        # Step 4: Code Generation (SQL)
        try:
            result.sql = self.codegen.generate(result.ast)
            result.success = True
        except Exception as e:
            result.error = f"Erreur de génération SQL: {str(e)}"
            return result

        return result

    def compile_to_sql(self, nl_text: str) -> str:
        """Shortcut: compile et retourne le SQL directement (lève exception si erreur)"""
        result = self.compile(nl_text)
        if not result.success:
            raise ValueError(result.error)
        return result.sql

    @staticmethod
    def get_example_queries() -> list:
        """
        Retourner TOUTES les requêtes possibles couvrant toutes les tables,
        toutes les jointures, tous les filtres, et tous les types de requêtes.
        """
        return [
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            # ── CAPTEUR (7 colonnes, 4 statuts, 5 types) ──
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            "Affiche les capteurs actifs",
            "Affiche les capteurs en maintenance",
            "Affiche les capteurs hors service",
            "Affiche les capteurs en panne",
            "Affiche les capteurs de type Éclairage",
            "Affiche les capteurs de type Trafic",
            "Affiche les capteurs de type Déchets",
            "Affiche les capteurs de type Énergie",
            "Montre les capteurs actifs",
            "Affiche un capteur actif",
            "Combien de capteurs sont actifs ?",
            "Combien de capteurs sont hors service ?",
            "Combien de capteurs sont en maintenance ?",
            "Quels capteurs sont actifs ?",
            "Quels capteurs sont en maintenance ?",
            "Nombre de capteurs actifs",
            "Nombre de capteurs par type",
            "Liste les capteurs en panne",

            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            # ── MESURES (grandeurs: NO2, CO2, PM10, Température...) ──
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            "Affiche les mesures",
            "Affiche les mesures de Température",
            "Affiche les mesures de NO2",
            "Affiche les mesures de CO2",
            "Affiche les mesures de PM10",
            "Affiche les mesures de Luminosité",
            "Affiche les mesures de Humidité",
            "Moyenne des mesures de Température",
            "Moyenne des mesures de NO2",
            "Nombre de mesures par capteur",
            "Total des mesures de CO2",

            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            # ── ZONES (pollution, superlatifs) ──
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            "Affiche les zones",
            "Affiche les 5 zones les plus polluées en NO2",
            "Affiche les 3 zones les plus polluées en CO2",
            "Affiche les 10 zones les plus polluées en PM10",

            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            # ── INTERVENTION (Nature, statut, coût) ──
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            "Affiche les interventions",
            "Affiche les interventions terminées",
            "Affiche les interventions en cours",
            "Affiche les interventions correctives",
            "Affiche les interventions curatives",
            "Affiche les interventions prédictives",
            "Affiche les interventions correctives avec coût > 200",
            "Affiche les interventions avec coût > 100",
            "Nombre de interventions terminées",
            "Nombre de interventions par nature",
            "Combien de interventions sont terminées ?",
            "Liste les interventions terminées",

            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            # ── CITOYEN (score, préférences) ──
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            "Affiche les citoyens",
            "Quels citoyens ont un score écologique > 80 ?",
            "Quels citoyens ont un score > 50 ?",
            "Trouve les citoyens qui préfèrent le vélo",
            "Trouve les citoyens qui préfèrent le transport",
            "Nombre de citoyens",
            "Liste les citoyens",

            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            # ── VÉHICULE (statut, énergie) ──
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            "Affiche les véhicules",
            "Affiche les véhicules en route",
            "Affiche les véhicules en panne",
            "Affiche les véhicules disponibles",
            "Affiche les véhicules électriques",
            "Affiche les véhicules hybrides",
            "Nombre de véhicules en route",
            "Nombre de véhicules en panne",
            "Combien de véhicules sont en route ?",
            "Liste les véhicules",

            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            # ── TRAJET (économie CO2, durée) ──
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            "Affiche les trajets",
            "Affiche les trajets avec économie CO2 > 5",
            "Donne-moi le trajet le plus économique en CO2",
            "Affiche les 5 trajets les plus économiques en CO2",
            "Nombre de trajets",
            "Liste les trajets",

            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            # ── TECHNICIEN ──
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            "Affiche les techniciens",
            "Liste les techniciens",
            "Nombre de techniciens",
            "Qui sont les techniciens ?",

            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            # ── CONSULTATION ──
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            "Affiche les consultations",
            "Liste les consultations",
            "Nombre de consultations",

            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            # ── PROPRIÉTAIRE ──
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            "Affiche les propriétaires",
            "Liste les propriétaires",

            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            # ── SUPERVISION ──
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            "Affiche les supervisions",
            "Liste les supervisions",
            "Nombre de supervisions",

            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            # ── PARTICIPATION ──
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            "Affiche les participations",
            "Liste les participations",
            "Nombre de participations",

            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            # ── RAPPORTS IA (confiance, diagnostic) ──
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            "Affiche les rapports IA",
            "Affiche les rapports IA avec confiance > 80",
            "Affiche les rapports IA avec confiance > 90",
            "Liste les rapports IA",
            "Nombre de rapports",

            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            # ── HISTORIQUE / ÉVÉNEMENTS ──
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            "Historique des événements de panne",
            "Historique des événements",
            "Affiche les événements",

            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            # ── JOINTURES (toutes les FK) ──
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

            # capteur ↔ propriétaire
            "Affiche les capteurs avec leur propriétaire",
            "Montre les capteurs et leurs propriétaires",

            # intervention ↔ capteur
            "Affiche les interventions avec leur capteur",
            "Liste les interventions et leurs capteurs",

            # intervention ↔ technicien
            "Affiche les interventions avec leur technicien",
            "Liste les interventions et leurs techniciens",

            # mesures ↔ capteur
            "Affiche les mesures avec leur capteur",
            "Montre les mesures et leurs capteurs",

            # consultation ↔ citoyen
            "Affiche les consultations avec leur citoyen",
            "Montre les consultations et leurs citoyens",

            # participation ↔ citoyen / consultation
            "Affiche les participations avec leur citoyen",
            "Affiche les participations avec leur consultation",

            # rapports_ia ↔ intervention
            "Affiche les rapports IA avec leur intervention",
            "Montre les rapports et leurs interventions",

            # supervision ↔ technicien / intervention
            "Liste les techniciens et leurs supervisions",
            "Affiche les supervisions avec leur technicien",
            "Affiche les supervisions avec leur intervention",

            # trajet ↔ véhicule
            "Affiche les trajets avec leur véhicule",
            "Montre les trajets et leurs véhicules",

            # citoyen ↔ consultation / participation
            "Montre les citoyens et leurs consultations",
            "Affiche les citoyens avec leurs consultations",
            "Affiche les citoyens avec leurs participations",
        ]

