"""
Parser — Analyse syntaxique universelle du langage naturel français
Construit un AST (Abstract Syntax Tree) à partir des tokens.

Version universelle: résolution dynamique via SchemaRegistry.
Supporte n'importe quelle requête sur les 17 tables de la BD.

Pipeline: Tokens → AST (SelectQuery | CountQuery | AggregateQuery)
"""

from typing import List, Optional, Tuple
from dataclasses import dataclass, field
from .lexer import Token, TokenType
from .schema_registry import SchemaRegistry


# ═══════════════════════════════════════════════════════════════════
# AST Nodes
# ═══════════════════════════════════════════════════════════════════

@dataclass
class ASTNode:
    """Base AST node"""
    node_type: str = ""


@dataclass
class ColumnRef(ASTNode):
    """Reference to a column, possibly with an aggregate function"""
    name: str = ""
    table: str = ""          # table context for disambiguation
    function: Optional[str] = None  # AVG, COUNT, SUM, MIN, MAX
    alias: Optional[str] = None
    node_type: str = "column_ref"


@dataclass
class Condition(ASTNode):
    """WHERE condition"""
    left: str = ""           # column name
    left_table: str = ""     # table for disambiguation
    operator: str = "="
    right: str = ""
    right_is_number: bool = False
    node_type: str = "condition"


@dataclass
class JoinClause(ASTNode):
    """JOIN clause with explicit FK info"""
    table: str = ""
    from_table: str = ""
    from_col: str = ""
    to_col: str = ""
    node_type: str = "join"


@dataclass
class OrderBy(ASTNode):
    """ORDER BY clause"""
    column: str = ""
    table: str = ""
    direction: str = "ASC"  # ASC or DESC
    node_type: str = "order_by"


@dataclass
class GroupByClause(ASTNode):
    """GROUP BY clause"""
    column: str = ""
    table: str = ""
    node_type: str = "group_by"


@dataclass
class SelectQuery(ASTNode):
    """SELECT query AST"""
    columns: List[ColumnRef] = field(default_factory=list)
    table: str = ""
    joins: List[JoinClause] = field(default_factory=list)
    conditions: List[Condition] = field(default_factory=list)
    group_by: List[GroupByClause] = field(default_factory=list)
    order_by: List[OrderBy] = field(default_factory=list)
    limit: Optional[int] = None
    node_type: str = "select"


@dataclass
class CountQuery(ASTNode):
    """COUNT query AST"""
    table: str = ""
    count_column: str = "*"
    joins: List[JoinClause] = field(default_factory=list)
    conditions: List[Condition] = field(default_factory=list)
    group_by: List[GroupByClause] = field(default_factory=list)
    node_type: str = "count"


@dataclass
class AggregateQuery(ASTNode):
    """Query with aggregate function + GROUP BY"""
    function: str = ""  # AVG, SUM, MIN, MAX
    column: str = ""
    column_table: str = ""
    table: str = ""
    joins: List[JoinClause] = field(default_factory=list)
    conditions: List[Condition] = field(default_factory=list)
    group_by: List[GroupByClause] = field(default_factory=list)
    order_by: Optional[OrderBy] = None
    limit: Optional[int] = None
    node_type: str = "aggregate"


# ═══════════════════════════════════════════════════════════════════
# Parser
# ═══════════════════════════════════════════════════════════════════

class ParseError(Exception):
    """Erreur de parsing avec contexte"""
    def __init__(self, message: str, token: Optional[Token] = None):
        self.token = token
        super().__init__(message)


class Parser:
    """
    Parser descendant récursif universel pour langage naturel français → AST.

    Grammaire (BNF/EBNF — cf. Cours 7, slides 3-5):
      Requête      → Commande Entité Filtres? Options?
                   | Question Entité Filtres? Options?
                   | Fonction Entité Filtres? Options?
      Commande     → VERB ( PRONOUN | ARTICLE )*
      Question     → QUESTION ( PREPOSITION | ARTICLE )*
      Entité       → TABLE_NAME | ADJECTIVE | TYPE_CAPTEUR | NATURE
      Filtres      → ( StatusFiltre | GrandeurFiltre | TypeFiltre | Condition )*
      StatusFiltre → STATUS | ADJECTIVE
      GrandeurFiltre → GRANDEUR
      TypeFiltre   → TYPE_CAPTEUR
      Condition    → (IDENTIFIER | COLUMN_NAME) OPERATOR (NUMBER | STRING | STATUS)
      Options      → Superlatif? Limite? GroupBy? OrderBy?
      Superlatif   → SUPERLATIVE ADJECTIVE?
      Limite       → NUMBER
      GroupBy      → GROUP_KW (ARTICLE)* (TABLE_NAME | IDENTIFIER | COLUMN_NAME)

    Stratégie de parsing:
      1. Valider la structure syntaxique minimale (commande + entité)
      2. Collecter tous les mots significatifs de la phrase
      3. Identifier les tables mentionnées (via SchemaRegistry)
      4. Identifier les colonnes, filtres, grandeurs, statuts
      5. Résoudre les jointures automatiquement (BFS sur le graphe FK)
      6. Construire l'AST approprié
    """

    # Status adjectives → normalized status value
    KNOWN_STATUS_FILTERS = {
        "actifs": "actif", "actives": "actif", "actif": "actif", "active": "actif",
        "hors_service": "hors_service",
        "en_maintenance": "en_maintenance",
        "en_route": "en_route",
        "en_cours": "en_cours",
        "en_panne": "en_panne",
        "en_ligne": "en_ligne",
        "signalé": "signalé", "signale": "signalé",
        "stationné": "stationné", "stationne": "stationné",
        "arrivé": "arrivé", "arrive": "arrivé",
        "terminée": "terminée", "terminee": "terminée", "terminé": "terminée",
        "terminees": "terminée", "terminées": "terminée", "terminés": "terminée",
        "demande": "demande",
        "fini": "terminée", "finie": "terminée",
        "maintenance": "en_maintenance",
        "assigné": "tech1_assigné", "assignés": "tech1_assigné",
        "panne": "en_panne",
    }

    # Adjective → sort column hints
    ADJECTIVE_SORT_MAP = {
        "polluées": "Valeur", "polluée": "Valeur",
        "pollués": "Valeur", "pollué": "Valeur",
        "polluees": "Valeur", "polluee": "Valeur", "pollues": "Valeur",
        "économique": "ÉconomieCO2", "économiques": "ÉconomieCO2",
        "economique": "ÉconomieCO2", "economiques": "ÉconomieCO2",
        "cher": "Coût", "chère": "Coût",
        "coûteux": "Coût", "coûteuse": "Coût",
        "couteux": "Coût", "couteuse": "Coût",
        "long": "Durée", "longue": "Durée",
        "court": "Durée", "courte": "Durée",
        "récent": "DateHeure", "récents": "DateHeure",
        "récentes": "DateHeure", "récente": "DateHeure",
        "recent": "DateHeure", "recents": "DateHeure",
        "élevé": "Valeur", "élevée": "Valeur",
        "eleve": "Valeur", "elevee": "Valeur",
        "faible": "Valeur", "faibles": "Valeur",
        "écologique": "Score", "écologiques": "Score",
        "ecologique": "Score", "ecologiques": "Score",
    }

    # Adjective → table hints (which table does the adjective suggest?)
    ADJECTIVE_TABLE_MAP = {
        "polluées": "mesures1", "polluée": "mesures1",
        "pollués": "mesures1", "pollué": "mesures1",
        "polluees": "mesures1", "polluee": "mesures1", "pollues": "mesures1",
        "économique": "trajet", "économiques": "trajet",
        "economique": "trajet", "economiques": "trajet",
        "écologique": "citoyen", "écologiques": "citoyen",
        "ecologique": "citoyen", "ecologiques": "citoyen",
        "cher": "intervention", "chère": "intervention",
        "coûteux": "intervention", "coûteuse": "intervention",
        "couteux": "intervention", "couteuse": "intervention",
    }

    def __init__(self, tokens: List[Token]):
        self.tokens = [t for t in tokens if t.type not in (TokenType.QUESTION_MARK,)]
        self.pos = 0
        self.schema = SchemaRegistry.get_instance()

    def _cur(self) -> Token:
        return self.tokens[self.pos] if self.pos < len(self.tokens) else self.tokens[-1]

    def _peek(self, offset: int = 1) -> Token:
        p = self.pos + offset
        return self.tokens[p] if p < len(self.tokens) else self.tokens[-1]

    def _advance(self) -> Token:
        t = self._cur()
        if self.pos < len(self.tokens) - 1:
            self.pos += 1
        return t

    def _match(self, *types: TokenType) -> bool:
        return self._cur().type in types

    def _skip_filler(self):
        """Skip articles, prepositions, pronouns, auxiliaries"""
        while self._match(TokenType.ARTICLE, TokenType.PRONOUN):
            self._advance()

    def _all_tokens_values(self) -> List[Tuple[TokenType, str]]:
        """Get all token type/value pairs for analysis"""
        return [(t.type, t.value) for t in self.tokens if t.type != TokenType.EOF]

    # ── Main parse entry ──────────────────────────────────────────

    def parse(self) -> ASTNode:
        """
        Parse l'entrée et retourne un AST.
        
        Implémente un analyseur syntaxique descendant récursif
        (cf. Cours 7: Analyse Syntaxique — analyse descendante).
        
        Pipeline:
          1. Validation lexicale stricte (aucun token UNKNOWN toléré)
          2. Parsing descendant récursif avec construction d'arbre de dérivation
          3. Extraction d'informations de l'analyse et construction de l'AST
        """
        # ── Étape 1: Validation lexicale (Cours 6 — fail()) ──
        self._validate_lexical()
        
        # ── Étape 2: Parsing descendant récursif (Cours 7) ──
        self.derivation_tree = self._parse_requete()
        
        # ── Étape 3: Analyse des tokens pour construire l'AST ──
        analysis = self._analyze_query()
        
        # ── Étape 4: Validation post-analyse ──
        self._validate_analysis(analysis)
        
        # ── Étape 5: Construction de l'AST ──
        return self._build_ast(analysis)

    def _validate_lexical(self):
        """
        Cours 6 — Analyse Lexicale: fonction fail()
        
        Vérifie que TOUS les tokens ont été reconnus par le lexer.
        Un seul token UNKNOWN → erreur lexicale fatale.
        
        Comme le prof l'explique (slide 14, fonction fail()):
        Si aucun automate ne reconnaît le lexème, on appelle recover()
        pour signaler l'erreur.
        """
        meaningful = [t for t in self.tokens if t.type != TokenType.EOF]
        
        if not meaningful:
            raise ParseError("Requête vide: aucun token à analyser.")
        
        # Vérification stricte: AUCUN mot inconnu toléré
        unknown = [t for t in meaningful if t.type == TokenType.UNKNOWN]
        if unknown:
            words = [f"'{t.value}' (position {t.position})" for t in unknown]
            raise ParseError(
                f"Erreur lexicale (fail): {len(unknown)} mot(s) non reconnu(s): "
                f"{', '.join(words)}. "
                f"L'analyseur lexical ne peut pas tokeniser ces mots. "
                f"Vérifiez l'orthographe. "
                f"Vocabulaire accepté: verbes (affiche, montre, liste, donne, trouve, calcule), "
                f"questions (combien, quels, quel, qui), "
                f"entités (capteurs, mesures, interventions, citoyens, véhicules, trajets, zones)."
            )

    def _parse_requete(self) -> dict:
        """
         — Analyse descendante récursive.
        
        Axiome de la grammaire — les formes acceptées:
        
        Grammaire formelle (adaptée du slide 11 du Cours 7):
        
          <requête>     →  <commande> <groupe_nominal> <filtres>
                        |  <question> <groupe_nominal> <filtres>
                        |  <fonction> <prep>? <groupe_nominal> <filtres>
          
          <commande>    →  VERB
          <question>    →  QUESTION
          <fonction>    →  FUNCTION
          
          <groupe_nominal> → <déterminant>? <quantificateur>?
                             <nom_entité> <adjectif>?
          
          <déterminant> →  ARTICLE | PREPOSITION | ε
          <nom_entité>  →  TABLE_NAME | TYPE_CAPTEUR | GRANDEUR | NATURE
                        |  STATUS | COLUMN_NAME
          <adjectif>    →  ADJECTIVE | STATUS | ε
          
          <filtres>     →  <filtre> <filtres> | ε
          <filtre>      →  <prep_filtre> | <comparaison> | <superlatif>
                        |  AUXILIARY | STATUS | NATURE | GRANDEUR
                        |  TYPE_CAPTEUR | NEGATION | NUMBER
          
          <comparaison> →  COLUMN_NAME OPERATOR (NUMBER | STRING)
          <superlatif>  →  SUPERLATIVE ADJECTIVE
          <prep_filtre> →  PREPOSITION (ARTICLE)? (TABLE_NAME | GRANDEUR | STATUS)
          
        Arbre de dérivation construit à chaque étape.
        """
        self.parse_pos = 0
        meaningful = [t for t in self.tokens if t.type != TokenType.EOF]
        self.parse_tokens = meaningful
        
        if not meaningful:
            raise ParseError("Requête vide.")
        
        # ── Validation d'accord grammatical (nombre singulier/pluriel) ──
        self._validate_grammar_agreement(meaningful)
        
        tree = {"rule": "<requête>", "children": []}
        
        # ── Essayer de reconnaître la forme de la requête ──
        first = self._pt_current()
        
        if first.type == TokenType.VERB:
            # Forme: <commande> <groupe_nominal> <filtres>
            cmd_node = self._parse_commande()
            tree["children"].append(cmd_node)
            gn_node = self._parse_groupe_nominal()
            tree["children"].append(gn_node)
            filtres_node = self._parse_filtres()
            if filtres_node["children"]:
                tree["children"].append(filtres_node)
                
        elif first.type == TokenType.QUESTION:
            # Forme: <question> <groupe_nominal> <filtres>
            q_node = self._parse_question()
            tree["children"].append(q_node)
            gn_node = self._parse_groupe_nominal()
            tree["children"].append(gn_node)
            filtres_node = self._parse_filtres()
            if filtres_node["children"]:
                tree["children"].append(filtres_node)
                
        elif first.type == TokenType.FUNCTION:
            # Forme: <fonction> <prep>? <groupe_nominal> <filtres>
            fn_node = {"rule": "<fonction>", "children": [
                {"terminal": first.type.value, "value": first.value}
            ]}
            self._pt_advance()
            tree["children"].append(fn_node)
            # Optional preposition: "moyenne DES mesures"
            self._pt_skip_filler()
            # STRICT: après FUNCTION+prep, on attend TABLE_NAME/GRANDEUR, PAS STATUS
            next_t = self._pt_current()
            if next_t.type == TokenType.STATUS:
                raise ParseError(
                    f"Erreur syntaxique: ordre des mots incorrect. "
                    f"Après '{first.value}', le nom de l'entité doit venir avant "
                    f"le statut '{next_t.value}'. "
                    f"Correction: '{first.value.capitalize()} de [entité] {next_t.value.replace('_',' ')}'. "
                    f"Exemple: 'Nombre de véhicules en route'"
                )
            gn_node = self._parse_groupe_nominal()
            tree["children"].append(gn_node)
            filtres_node = self._parse_filtres()
            if filtres_node["children"]:
                tree["children"].append(filtres_node)
        else:
            # La phrase ne commence pas par VERB, QUESTION ou FUNCTION
            # → Erreur syntaxique stricte (Cours 7: la grammaire l'exige)
            raise ParseError(
                f"Erreur syntaxique: la requête doit commencer par une commande "
                f"(verbe: affiche, montre, liste, donne, trouve, calcule, historique), "
                f"une question (combien, quels, quel, qui), "
                f"ou une fonction (moyenne, total, nombre, min, max). "
                f"Token trouvé: '{first.value}' ({first.type.value}). "
                f"Exemple: 'Affiche les capteurs actifs'"
            )
        
        return tree
    
    # ── Validation d'accord grammatical français ──────────────────
    
    # Dictionnaire: mot → nombre grammatical ('s' = singulier, 'p' = pluriel, None = invariable)
    WORD_NUMBER = {
        # ── TABLE_NAME: singulier / pluriel ──
        "capteur": "s", "capteurs": "p",
        "sensor": "s", "sensors": "p",
        "sonde": "s", "sondes": "p",
        "détecteur": "s", "détecteurs": "p",
        "mesure": "s", "mesures": "p", "mesures1": "p", "mesures2": "p",
        "relevé": "s", "relevés": "p",
        "zone": "s", "zones": "p",
        "intervention": "s", "interventions": "p",
        "réparation": "s", "réparations": "p",
        "citoyen": "s", "citoyens": "p",
        "habitant": "s", "habitants": "p",
        "personne": "s", "personnes": "p",
        "utilisateur": "s", "utilisateurs": "p",
        "consultation": "s", "consultations": "p",
        "sondage": "s", "sondages": "p",
        "participation": "s", "participations": "p",
        "technicien": "s", "techniciens": "p",
        "propriétaire": "s", "propriétaires": "p", "proprietaire": "s", "proprietaires": "p",
        "véhicule": "s", "véhicules": "p", "vehicule": "s", "vehicules": "p",
        "voiture": "s", "voitures": "p",
        "camion": "s", "camions": "p",
        "trajet": "s", "trajets": "p",
        "itinéraire": "s", "itinéraires": "p",
        "supervision": "s", "supervisions": "p",
        "rapport": "s", "rapports": "p",
        "événement": "s", "événements": "p", "evenement": "s", "evenements": "p",
        "log": "s", "logs": "p",
        "journal": "s", "journaux": "p",
        
        # ── ADJECTIVE: singulier / pluriel ──
        "actif": "s", "actifs": "p",
        "active": "s", "actives": "p",
        "pollué": "s", "pollués": "p",
        "polluée": "s", "polluées": "p",
        "polluee": "s", "polluees": "p",
        "pollues": "p",
        "économique": "s", "économiques": "p", "economique": "s", "economiques": "p",
        "écologique": "s", "écologiques": "p", "ecologique": "s", "ecologiques": "p",
        "récent": "s", "récents": "p", "récente": "s", "récentes": "p",
        "recent": "s", "recents": "p", "recente": "s", "recentes": "p",
        "disponible": "s", "disponibles": "p",
        "assigné": "s", "assignés": "p", "assigne": "s", "assignes": "p",
        "autonome": "s", "autonomes": "p",
        "urbain": "s", "urbains": "p", "urbaine": "s", "urbaines": "p",
        "intelligent": "s", "intelligents": "p", "intelligente": "s", "intelligentes": "p",
        "électrique": "s", "électriques": "p", "electrique": "s", "electriques": "p",
        "hybride": "s", "hybrides": "p",
        "faible": "s", "faibles": "p",
        "supérieur": "s", "supérieure": "s",
        "inférieur": "s", "inférieure": "s",
        "élevé": "s", "élevée": "s", "eleve": "s", "elevee": "s",
        "dernière": "s", "dernières": "p", "derniere": "s", "dernieres": "p",
        "dépassant": None,  # participe présent = invariable
        
        # ── STATUS: singulier / pluriel ──
        "terminé": "s", "terminés": "p",
        "terminée": "s", "terminées": "p",
        "terminee": "s", "terminees": "p",
        "signalé": "s", "signalés": "p", "signale": "s",
        "stationné": "s", "stationne": "s",
        "arrivé": "s", "arrive": "s",
        "fini": "s", "finis": "p", "finie": "s", "finies": "p",
        "inactif": "s", "inactive": "s",
        
        # ── NATURE: singulier / pluriel ──
        "corrective": "s", "correctives": "p",
        "curative": "s", "curatives": "p",
        "prédictive": "s", "prédictives": "p", "predictive": "s", "predictives": "p",
        
        # ── QUESTION: singulier / pluriel ──
        "quel": "s", "quels": "p",
        "quelle": "s", "quelles": "p",
    }
    
    # Dictionnaire de correction: mot singulier → pluriel et vice versa
    WORD_CORRECTION = {
        "capteur": "capteurs", "capteurs": "capteur",
        "mesure": "mesures", "mesures": "mesure",
        "zone": "zones", "zones": "zone",
        "intervention": "interventions", "interventions": "intervention",
        "citoyen": "citoyens", "citoyens": "citoyen",
        "véhicule": "véhicules", "véhicules": "véhicule",
        "vehicule": "vehicules", "vehicules": "vehicule",
        "trajet": "trajets", "trajets": "trajet",
        "technicien": "techniciens", "techniciens": "technicien",
        "rapport": "rapports", "rapports": "rapport",
        "consultation": "consultations", "consultations": "consultation",
        "supervision": "supervisions", "supervisions": "supervision",
        "événement": "événements", "événements": "événement",
        "evenement": "evenements", "evenements": "evenement",
        "actif": "actifs", "actifs": "actif",
        "active": "actives", "actives": "active",
        "terminé": "terminés", "terminés": "terminé",
        "terminée": "terminées", "terminées": "terminée",
        "terminee": "terminees", "terminees": "terminee",
        "pollué": "pollués", "pollués": "pollué",
        "polluée": "polluées", "polluées": "polluée",
        "polluee": "polluees", "polluees": "polluee",
        "corrective": "correctives", "correctives": "corrective",
        "curative": "curatives", "curatives": "curative",
        "prédictive": "prédictives", "prédictives": "prédictive",
        "économique": "économiques", "économiques": "économique",
        "écologique": "écologiques", "écologiques": "écologique",
        "disponible": "disponibles", "disponibles": "disponible",
        "électrique": "électriques", "électriques": "électrique",
        "hybride": "hybrides", "hybrides": "hybride",
        "récent": "récents", "récents": "récent",
        "récente": "récentes", "récentes": "récente",
        "faible": "faibles", "faibles": "faible",
        "signalé": "signalés", "signalés": "signalé",
        "fini": "finis", "finis": "fini",
        "finie": "finies", "finies": "finie",
        "quel": "quels", "quels": "quel",
        "quelle": "quelles", "quelles": "quelle",
    }
    
    # Articles singuliers vs pluriels
    SINGULAR_ARTICLES = {"le", "la", "un", "une", "du", "l", "ce", "cette", "son", "sa", "au"}
    PLURAL_ARTICLES = {"les", "des", "ces", "aux", "ses", "leurs"}
    # Articles neutres (pas de contrainte de nombre)
    NEUTRAL_ARTICLES = {"leur"}  # "leur capteur" = ok
    
    def _validate_grammar_agreement(self, tokens: list):
        """
        Validation stricte de l'accord grammatical en nombre (singulier/pluriel).
        
        Règles appliquées:
        1. Article pluriel (les, des) → nom et adjectif doivent être au pluriel
        2. Article singulier (le, la, un, une) → nom et adjectif doivent être au singulier
        3. Question plurielle (quels) → nom doit être au pluriel
        4. Question singulière (quel) → nom doit être au singulier
        
        Exemples:
        - "les capteur actif" → ERREUR (doit être "les capteurs actifs")
        - "un capteurs" → ERREUR (doit être "un capteur")
        - "Affiche les capteurs actifs" → OK
        """
        expected_number = None  # 's' = singulier, 'p' = pluriel, None = pas encore défini
        trigger_word = None     # Le mot qui a défini le nombre attendu
        
        for i, tok in enumerate(tokens):
            word = tok.value.lower()
            
            # ── Déterminer le nombre attendu à partir de l'article ──
            if tok.type == TokenType.ARTICLE:
                if word in self.SINGULAR_ARTICLES:
                    expected_number = "s"
                    trigger_word = tok.value
                elif word in self.PLURAL_ARTICLES:
                    expected_number = "p"
                    trigger_word = tok.value
                else:
                    expected_number = None  # article neutre
                continue
            
            # ── NUMBER: 1 = singulier, > 1 = pluriel ──
            if tok.type == TokenType.NUMBER:
                try:
                    n = float(word)
                    if n == 1:
                        expected_number = "s"
                        trigger_word = tok.value
                    elif n > 1:
                        expected_number = "p"
                        trigger_word = tok.value
                except ValueError:
                    pass
                continue
            
            # ── Question words: quel/quels, combien ──
            if tok.type == TokenType.QUESTION:
                if word in self.WORD_NUMBER:
                    word_num = self.WORD_NUMBER[word]
                    if word_num:
                        expected_number = word_num
                        trigger_word = tok.value
                elif word == "combien":
                    # "Combien de capteurs" → pluriel requis
                    expected_number = "p"
                    trigger_word = "combien"
                continue
            
            # ── Vérifier l'accord des mots variables ──
            if expected_number and word in self.WORD_NUMBER:
                word_num = self.WORD_NUMBER[word]
                if word_num and word_num != expected_number:
                    # MISMATCH: l'accord grammatical est incorrect
                    correction = self.WORD_CORRECTION.get(word, "?")
                    number_label = "pluriel" if expected_number == "p" else "singulier"
                    word_label = "pluriel" if word_num == "p" else "singulier"
                    raise ParseError(
                        f"Erreur grammaticale: accord en nombre incorrect. "
                        f"'{trigger_word}' ({number_label}) exige "
                        f"'{correction}' ({number_label}), "
                        f"mais '{tok.value}' ({word_label}) a été trouvé. "
                        f"Correction: remplacez '{tok.value}' par '{correction}'."
                    )
            
            # ── Réinitialiser le nombre attendu après certaines prépositions ──
            # "avec leur capteur", "dans la zone" → nouveau contexte
            # MAIS "de/d/du" ne réinitialise PAS (ex: "combien de capteurs", "nombre de véhicules")
            if tok.type == TokenType.CONJUNCTION:
                expected_number = None
                trigger_word = None
            elif tok.type == TokenType.GROUP_KEYWORD:
                expected_number = None
                trigger_word = None
            elif tok.type == TokenType.PREPOSITION and word not in ("de", "d", "en"):
                expected_number = None
                trigger_word = None
    
    # ── Productions de la grammaire (méthodes récursives) ──
    
    def _parse_commande(self) -> dict:
        """<commande> → VERB"""
        t = self._pt_current()
        if t.type != TokenType.VERB:
            raise ParseError(
                f"Erreur syntaxique: verbe attendu, trouvé '{t.value}' ({t.type.value})."
            )
        self._pt_advance()
        return {"rule": "<commande>", "children": [
            {"terminal": "VERB", "value": t.value}
        ]}
    
    def _parse_question(self) -> dict:
        """<question> → QUESTION"""
        t = self._pt_current()
        if t.type != TokenType.QUESTION:
            raise ParseError(
                f"Erreur syntaxique: question attendue, trouvé '{t.value}' ({t.type.value})."
            )
        self._pt_advance()
        return {"rule": "<question>", "children": [
            {"terminal": "QUESTION", "value": t.value}
        ]}
    
    def _parse_groupe_nominal(self) -> dict:
        """
        <groupe_nominal> → <déterminant>? <quantificateur>? <nom_entité> <adjectif>?
        
        Le groupe nominal est le cœur de la requête.
        Il DOIT contenir au moins un <nom_entité>.
        """
        node = {"rule": "<groupe_nominal>", "children": []}
        
        # Skip articles & prepositions (déterminants)
        self._pt_skip_filler()
        
        # Optionnel: NUMBER (quantificateur) - e.g. "les 5 zones"
        cur = self._pt_current()
        if cur.type == TokenType.NUMBER:
            node["children"].append({"terminal": "NUMBER", "value": cur.value})
            self._pt_advance()
            self._pt_skip_filler()
        
        # Optionnel: SUPERLATIVE before entity - "les plus polluées"
        cur = self._pt_current()
        if cur.type == TokenType.SUPERLATIVE:
            node["children"].append({"terminal": "SUPERLATIVE", "value": cur.value})
            self._pt_advance()
            self._pt_skip_filler()
        
        # DOIT trouver un nom d'entité (TABLE, TYPE_CAPTEUR, GRANDEUR, etc.)
        entity_types = (
            TokenType.TABLE_NAME, TokenType.TYPE_CAPTEUR, TokenType.GRANDEUR,
            TokenType.NATURE, TokenType.COLUMN_NAME,
        )
        
        # Also accept ADJECTIVE that maps to a table
        cur = self._pt_current()
        
        if cur.type in entity_types:
            node["children"].append({
                "terminal": cur.type.value, "value": cur.value,
                "role": "nom_entité"
            })
            self._pt_advance()
        elif cur.type == TokenType.ADJECTIVE and cur.value.lower() in self.ADJECTIVE_TABLE_MAP:
            node["children"].append({
                "terminal": "ADJECTIVE→ENTITÉ", "value": cur.value,
                "role": "nom_entité"
            })
            self._pt_advance()
        elif cur.type == TokenType.STATUS:
            # "actifs" alone can imply capteur table
            node["children"].append({
                "terminal": "STATUS", "value": cur.value,
                "role": "nom_entité"
            })
            self._pt_advance()
        elif cur.type == TokenType.EOF:
            raise ParseError(
                f"Erreur syntaxique: la requête est incomplète. "
                f"Un nom d'entité est attendu après la commande. "
                f"Entités valides: capteurs, mesures, interventions, citoyens, véhicules, trajets, zones. "
                f"Exemple: 'Affiche les capteurs actifs'"
            )
        else:
            raise ParseError(
                f"Erreur syntaxique: nom d'entité attendu, trouvé '{cur.value}' ({cur.type.value}). "
                f"Entités valides: capteurs, mesures, interventions, citoyens, véhicules, trajets, zones. "
                f"Exemple: 'Affiche les capteurs actifs'"
            )
        
        # Optionnel: ADJECTIVE/STATUS après l'entité
        cur = self._pt_current()
        if cur.type in (TokenType.ADJECTIVE, TokenType.STATUS):
            node["children"].append({
                "terminal": cur.type.value, "value": cur.value,
                "role": "adjectif"
            })
            self._pt_advance()
        
        # Optionnel: (ARTICLE)? SUPERLATIVE ADJECTIVE après l'entité
        # Ex: "les plus polluées", "le plus économique"
        cur = self._pt_current()
        saved_pos = self.parse_pos
        if cur.type == TokenType.ARTICLE:
            self._pt_advance()
            cur = self._pt_current()
        if cur.type == TokenType.SUPERLATIVE:
            node["children"].append({
                "terminal": "SUPERLATIVE", "value": cur.value,
                "role": "superlatif"
            })
            self._pt_advance()
            cur = self._pt_current()
            if cur.type in (TokenType.ADJECTIVE, TokenType.STATUS):
                node["children"].append({
                    "terminal": cur.type.value, "value": cur.value,
                    "role": "adjectif_sup"
                })
                self._pt_advance()
        elif self.parse_pos != saved_pos:
            # ARTICLE consumed but no SUPERLATIVE found → rollback
            self.parse_pos = saved_pos
        
        return node
    
    def _parse_filtres(self) -> dict:
        """
        <filtres> → <filtre> <filtres> | ε
        
        Consomme les tokens restants comme filtres avec validation STRICTE.
        
        Règles de validation (Cours 7):
        - Un TABLE_NAME dans les filtres DOIT être précédé d'une PREPOSITION
          ou CONJUNCTION (sinon c'est une entité dupliquée → erreur)
        - Les filtres doivent suivre des patterns valides
        - Pas de tokens dupliqués incohérents
        """
        node = {"rule": "<filtres>", "children": []}
        
        valid_filter_types = (
            TokenType.PREPOSITION, TokenType.ARTICLE, TokenType.CONJUNCTION,
            TokenType.STATUS, TokenType.GRANDEUR, TokenType.TYPE_CAPTEUR,
            TokenType.NATURE, TokenType.ADJECTIVE, TokenType.NUMBER,
            TokenType.STRING, TokenType.OPERATOR, TokenType.COLUMN_NAME,
            TokenType.TABLE_NAME, TokenType.AUXILIARY, TokenType.NEGATION,
            TokenType.TEMPORAL, TokenType.PRONOUN,
            TokenType.FUNCTION, TokenType.VERB, TokenType.GROUP_KEYWORD,
            TokenType.QUESTION, TokenType.IDENTIFIER, TokenType.QUESTION_MARK,
        )
        
        prev_type = None
        prev_prev_type = None
        seen_table_names = set()
        # Collect the entity from groupe_nominal
        for t in self.parse_tokens[:self.parse_pos]:
            if t.type == TokenType.TABLE_NAME:
                seen_table_names.add(t.value.lower())
        
        while self._pt_current().type != TokenType.EOF:
            cur = self._pt_current()
            
            if cur.type == TokenType.TABLE_NAME:
                # STRICT: Duplicate TABLE_NAME detection
                # Même si précédé d'un ARTICLE, si c'est la même entité → erreur
                if cur.value.lower() in seen_table_names:
                    raise ParseError(
                        f"Erreur syntaxique: entité dupliquée '{cur.value}' "
                        f"détectée. L'entité a déjà été spécifiée dans la requête. "
                        f"Supprimez la répétition."
                    )
                # Un TABLE_NAME dans les filtres doit être précédé d'une
                # PREPOSITION, CONJUNCTION ou GROUP_KEYWORD (par capteur)
                if prev_type not in (TokenType.PREPOSITION, TokenType.CONJUNCTION,
                                     TokenType.ARTICLE, TokenType.GROUP_KEYWORD):
                    raise ParseError(
                        f"Erreur syntaxique: nom d'entité '{cur.value}' inattendu "
                        f"en position filtre. Utilisez une préposition "
                        f"(avec, de, par) avant un nom d'entité dans les filtres. "
                        f"Exemple: 'Affiche les interventions avec leur capteur'"
                    )
                seen_table_names.add(cur.value.lower())
            
            if cur.type == TokenType.SUPERLATIVE:
                # STRICT: Superlatif interdit dans les filtres
                # Le superlatif doit être dans le groupe nominal:
                # "les 5 zones les plus polluées en NO2" (correct)
                # "les 5 zones en NO2 le plus pollué" (incorrect)
                raise ParseError(
                    f"Erreur syntaxique: superlatif '{cur.value}' en mauvaise position. "
                    f"Le superlatif doit être placé directement après le nom de l'entité, "
                    f"avant les filtres. "
                    f"Exemple correct: 'Affiche les 5 zones les plus polluées en NO2'"
                )
            
            if cur.type in valid_filter_types:
                node["children"].append({
                    "terminal": cur.type.value, "value": cur.value
                })
                prev_type = cur.type
                self._pt_advance()
            elif cur.type == TokenType.UNKNOWN:
                raise ParseError(
                    f"Erreur lexicale: mot non reconnu '{cur.value}' en position {cur.position}."
                )
            else:
                raise ParseError(
                    f"Erreur syntaxique: token inattendu '{cur.value}' ({cur.type.value}) "
                    f"en position {cur.position}."
                )
        
        return node
    
    # ── Helpers pour le parsing descendant ──
    
    def _pt_current(self) -> Token:
        """Token courant dans le parsing descendant"""
        if self.parse_pos < len(self.parse_tokens):
            return self.parse_tokens[self.parse_pos]
        return Token(TokenType.EOF, "", -1)
    
    def _pt_advance(self) -> Token:
        """Avancer au token suivant"""
        t = self._pt_current()
        if self.parse_pos < len(self.parse_tokens):
            self.parse_pos += 1
        return t
    
    def _pt_skip_filler(self):
        """Sauter les articles, prépositions, auxiliaires (déterminants)
        STRICT: détecte les doublons consécutifs (ex: 'les les')"""
        filler_types = (
            TokenType.ARTICLE, TokenType.PREPOSITION,
            TokenType.PRONOUN, TokenType.AUXILIARY,
            TokenType.CONJUNCTION, TokenType.NEGATION,
        )
        prev_filler = None
        while self._pt_current().type in filler_types:
            cur = self._pt_current()
            if prev_filler and cur.type == prev_filler.type and cur.value.lower() == prev_filler.value.lower():
                raise ParseError(
                    f"Erreur syntaxique: mot dupliqué '{cur.value}' détecté. "
                    f"Supprimez la répétition."
                )
            prev_filler = cur
            self._pt_advance()

    def get_derivation_tree(self) -> dict:
        """Retourne l'arbre de dérivation construit lors du parsing"""
        return getattr(self, 'derivation_tree', None)

    def _validate_analysis(self, analysis: dict):
        """
        Validation post-analyse: vérifier que l'analyse a produit
        suffisamment d'informations pour construire un AST valide.
        """
        # Si aucune table n'a été identifiée après l'analyse complète
        if not analysis["tables"]:
            # Tenter l'inférence
            inferred = self._infer_tables_from_context(analysis)
            if not inferred or inferred == ["capteur"]:
                # Vérifier si on a vraiment des indices pour cette table
                has_capteur_hints = (
                    analysis["statuses"] or
                    analysis["types_capteur"] or
                    analysis["grandeurs"] or
                    analysis["natures"] or
                    analysis.get("energy_filters") or
                    analysis.get("preference_filters") or
                    analysis["conditions"] or
                    analysis["adjectives"]
                )
                if not has_capteur_hints and inferred == ["capteur"]:
                    raise ParseError(
                        f"Erreur syntaxique: impossible d'identifier la table cible. "
                        f"Précisez une entité: capteurs, mesures, interventions, citoyens, etc."
                    )
            analysis["tables"] = inferred

    # ── Query Analysis ────────────────────────────────────────────

    def _analyze_query(self) -> dict:
        """
        Parcourir tous les tokens et extraire les infos structurées:
        - query_type: select, count, aggregate
        - tables: list of table names
        - columns: list of column refs
        - conditions: list of conditions
        - statuses: list of status filters
        - grandeurs: list of grandeur filters
        - types_capteur: list of capteur type filters
        - natures: list of intervention nature filters
        - superlative: (direction, adjective) or None
        - limit: int or None
        - group_by: column for grouping
        - function: aggregate function name
        """
        analysis = {
            "query_type": "select",
            "tables": [],
            "columns": [],
            "conditions": [],
            "statuses": [],
            "grandeurs": [],
            "types_capteur": [],
            "natures": [],
            "superlative": None,
            "limit": None,
            "group_by": None,
            "function": None,
            "identifiers": [],
            "adjectives": [],
            "column_refs": [],       # explicit COLUMN_NAME tokens
            "event_filters": [],     # for capteurs_history.event
            "preference_filters": [],  # for citoyen.Préférences LIKE
            "energy_filters": [],      # for véhicule.Énergie Utilisée
            "has_negation": False,     # ne...pas, aucun
            "or_natures": False,       # "correctives ou curatives"
        }

        i = 0
        tokens = self.tokens
        
        # ── Pré-scan: détecter articles singuliers ("un", "une") → LIMIT 1
        for idx, tok in enumerate(tokens):
            if tok.type == TokenType.ARTICLE and tok.value.lower() in ("un", "une"):
                # Vérifier que le token suivant est un TABLE_NAME ou entité
                if idx + 1 < len(tokens) and tokens[idx + 1].type in (
                    TokenType.TABLE_NAME, TokenType.TYPE_CAPTEUR, TokenType.GRANDEUR,
                    TokenType.COLUMN_NAME, TokenType.ADJECTIVE
                ):
                    if analysis["limit"] is None:
                        analysis["limit"] = 1

        while i < len(tokens) and tokens[i].type != TokenType.EOF:
            t = tokens[i]

            # ── Question word → query type
            if t.type == TokenType.QUESTION:
                if t.value == "combien":
                    analysis["query_type"] = "count"

            # ── Function → aggregate
            elif t.type == TokenType.FUNCTION:
                fn = t.value.lower()
                if fn in ("nombre", "count"):
                    analysis["query_type"] = "count"
                else:
                    analysis["query_type"] = "aggregate"
                    analysis["function"] = fn

            # ── Table names
            elif t.type == TokenType.TABLE_NAME:
                resolved = self.schema.resolve_table_name(t.value)
                if resolved and resolved not in analysis["tables"]:
                    analysis["tables"].append(resolved)

            # ── Column names (from multi-word expressions like "economie co2")
            elif t.type == TokenType.COLUMN_NAME:
                col_word = t.value.lower()
                resolved = self.schema.resolve_column(col_word)
                if resolved:
                    table, col = resolved
                    analysis["column_refs"].append((table, col))
                    if table not in analysis["tables"]:
                        analysis["tables"].append(table)
                else:
                    analysis["identifiers"].append(col_word)

            # ── Grandeur
            elif t.type == TokenType.GRANDEUR:
                # Skip if already captured as part of a COLUMN_NAME expression
                # (e.g. "economie co2" was already handled as COLUMN_NAME)
                if not analysis["column_refs"]:
                    analysis["grandeurs"].append(t.value)
                    if "mesures1" not in analysis["tables"]:
                        analysis["tables"].append("mesures1")

            # ── Status
            elif t.type == TokenType.STATUS:
                sv = t.value
                if sv in self.KNOWN_STATUS_FILTERS:
                    analysis["statuses"].append(self.KNOWN_STATUS_FILTERS[sv])
                else:
                    analysis["statuses"].append(sv)

            # ── Type capteur
            elif t.type == TokenType.TYPE_CAPTEUR:
                analysis["types_capteur"].append(t.value)
                if "capteur" not in analysis["tables"]:
                    analysis["tables"].append("capteur")

            # ── Nature intervention
            elif t.type == TokenType.NATURE:
                analysis["natures"].append(t.value)
                if "intervention" not in analysis["tables"]:
                    analysis["tables"].append("intervention")
                # Check if previous token was "ou" (OR conjunction)
                if i >= 2 and tokens[i-1].type == TokenType.CONJUNCTION and tokens[i-1].value == "ou":
                    analysis["or_natures"] = True

            # ── Negation
            elif t.type == TokenType.NEGATION:
                analysis["has_negation"] = True

            # ── Number (check if LIMIT)
            elif t.type == TokenType.NUMBER:
                # Number immediately after verb/article = LIMIT
                if i >= 1 and tokens[i-1].type in (TokenType.VERB, TokenType.ARTICLE,
                                                      TokenType.PREPOSITION, TokenType.PRONOUN):
                    analysis["limit"] = int(float(t.value))
                # Number after operator = part of condition (handled below)
                elif i >= 2 and tokens[i-1].type == TokenType.OPERATOR:
                    pass  # handled in operator section
                else:
                    # Could be a limit at start: "10 capteurs actifs"
                    if analysis["limit"] is None:
                        try:
                            analysis["limit"] = int(float(t.value))
                        except ValueError:
                            pass

            # ── Operator → condition
            elif t.type == TokenType.OPERATOR:
                op = t.value
                # Look backward for column, forward for value
                col_word = self._find_column_before(tokens, i)
                val_word = self._find_value_after(tokens, i)
                if col_word and val_word is not None:
                    is_num = False
                    try:
                        float(val_word)
                        is_num = True
                    except ValueError:
                        pass
                    analysis["conditions"].append({
                        "left": col_word,
                        "operator": op,
                        "right": val_word,
                        "right_is_number": is_num,
                    })

            # ── Superlative
            elif t.type == TokenType.SUPERLATIVE:
                direction = "DESC" if t.value in ("plus", "meilleur", "meilleure",
                                                     "premier", "première", "dernier", "dernière",
                                                     "top") else "ASC"
                if t.value in ("moins",):
                    direction = "ASC"
                # "top N" pattern: top 10 citoyens
                if t.value == "top":
                    # Look ahead for a number
                    if i + 1 < len(tokens) and tokens[i+1].type == TokenType.NUMBER:
                        try:
                            analysis["limit"] = int(float(tokens[i+1].value))
                        except ValueError:
                            pass
                # Look ahead for adjective
                adj = ""
                if i + 1 < len(tokens) and tokens[i+1].type in (TokenType.ADJECTIVE, TokenType.IDENTIFIER):
                    adj = tokens[i+1].value
                analysis["superlative"] = (direction, adj)

            # ── Adjective
            elif t.type == TokenType.ADJECTIVE:
                adj = t.value.lower()
                analysis["adjectives"].append(adj)
                # Check if energy-type adjective (électrique, hybride, hydrogène)
                energy_map = {
                    "électrique": "Électrique", "electrique": "Électrique",
                    "électriques": "Électrique", "electriques": "Électrique",
                    "hybride": "Hybride", "hybrides": "Hybride",
                    "hydrogène": "Hydrogène", "hydrogene": "Hydrogène",
                }
                if adj in energy_map:
                    analysis["energy_filters"].append(energy_map[adj])
                    if "véhicule" not in analysis["tables"]:
                        analysis["tables"].append("véhicule")
                # Check if it implies a status
                elif adj in self.KNOWN_STATUS_FILTERS:
                    analysis["statuses"].append(self.KNOWN_STATUS_FILTERS[adj])
                # Check if it implies a table
                if adj in self.ADJECTIVE_TABLE_MAP:
                    tbl = self.ADJECTIVE_TABLE_MAP[adj]
                    if tbl not in analysis["tables"]:
                        analysis["tables"].append(tbl)

            # ── Group keyword (par, chaque, selon)
            elif t.type == TokenType.GROUP_KEYWORD:
                # Look ahead for what we're grouping by
                j = i + 1
                while j < len(tokens) and tokens[j].type in (TokenType.ARTICLE, TokenType.PREPOSITION):
                    j += 1
                if j < len(tokens) and tokens[j].type in (
                    TokenType.TABLE_NAME, TokenType.IDENTIFIER,
                    TokenType.COLUMN_NAME, TokenType.TYPE_CAPTEUR
                ):
                    analysis["group_by"] = tokens[j].value
                    # If count doesn't have explicit function, make it count
                    if analysis["query_type"] == "select" and analysis["function"] is None:
                        if any(tk.type == TokenType.FUNCTION for tk in tokens):
                            pass
                        elif any(tk.value == "combien" for tk in tokens):
                            pass
                        else:
                            analysis["query_type"] = "count"

            # ── Identifier (potential table/column)
            elif t.type == TokenType.IDENTIFIER:
                word = t.value.lower()
                # Check if it's a known table word
                resolved_table = self.schema.resolve_table_name(word)
                if resolved_table:
                    if resolved_table not in analysis["tables"]:
                        analysis["tables"].append(resolved_table)
                else:
                    # Check if it's a known status filter
                    if word in self.KNOWN_STATUS_FILTERS:
                        analysis["statuses"].append(self.KNOWN_STATUS_FILTERS[word])
                    else:
                        # Check if it's a preference keyword (vélo, bus, marche, transport)
                        preference_keywords = {
                            "vélo": "vélo", "velo": "vélo",
                            "bus": "bus", "marche": "marche",
                            "transport": "transport en commun",
                            "covoiturage": "covoiturage",
                        }
                        if word in preference_keywords:
                            analysis["preference_filters"].append(preference_keywords[word])
                            if "citoyen" not in analysis["tables"]:
                                analysis["tables"].append("citoyen")
                        else:
                            # Check if it's a grandeur
                            grandeur = self.schema.resolve_grandeur(word)
                            if grandeur:
                                analysis["grandeurs"].append(word)
                                if "mesures1" not in analysis["tables"]:
                                    analysis["tables"].append("mesures1")
                            else:
                                analysis["identifiers"].append(word)

            # ── Conjunction with → implies join
            elif t.type == TokenType.PREPOSITION and t.value == "avec":
                pass  # Tables after "avec" will be picked up naturally

            i += 1

        # ── Post-processing: context-aware fixups ──

        # 1) If main table is capteurs_history, convert statuses to event filters
        if analysis["tables"] and analysis["tables"][0] == "capteurs_history":
            for s in analysis["statuses"]:
                # Use the raw status keyword as event value (e.g. "panne", not "En Panne")
                raw_event = s.lower().replace("en_", "").replace("_", " ").strip()
                analysis["event_filters"].append(raw_event)
            analysis["statuses"] = []

        # 2) If trajet is the main table and no mesures1 context, remove grandeur filters
        #    (CO2 in trajet context means ÉconomieCO2, not NomGrandeur)
        if analysis["tables"] and analysis["tables"][0] == "trajet":
            if "mesures1" not in analysis["tables"]:
                analysis["grandeurs"] = []
            elif "mesures1" in analysis["tables"] and len(analysis["tables"]) == 2:
                # If mesures1 was only added because of a grandeur, and trajet is main,
                # remove it
                if not any(t.type == TokenType.TABLE_NAME and
                           self.schema.resolve_table_name(t.value) == "mesures1"
                           for t in self.tokens):
                    analysis["tables"].remove("mesures1")
                    analysis["grandeurs"] = []

        # 3) Detect preference context: when citoyen is present and transport-related
        #    words (bus, voiture, marche) appear after "préfèrent", treat them as
        #    preference filters instead of table names
        preference_transport_words = {"bus", "voiture", "voitures", "marche", "tramway", "métro", "metro"}
        has_prefer_verb = any(t.value in ("préfèrent", "preferent", "préfère", "prefere",
                                            "préférer", "preferer", "aiment", "aime",
                                            "utilisent", "utilisent", "choisissent")
                              for t in self.tokens if t.type in (TokenType.VERB, TokenType.IDENTIFIER, TokenType.AUXILIARY))
        if "citoyen" in analysis["tables"] and has_prefer_verb:
            for t in self.tokens:
                if t.type == TokenType.TABLE_NAME and t.value.lower() in preference_transport_words:
                    # This is a preference, not a table join
                    pref_val = t.value.lower()
                    analysis["preference_filters"].append(pref_val)
                    # Remove the wrongly-added table
                    resolved_tbl = self.schema.resolve_table_name(pref_val)
                    if resolved_tbl and resolved_tbl in analysis["tables"] and resolved_tbl != "citoyen":
                        analysis["tables"].remove(resolved_tbl)

        return analysis

    def _find_column_before(self, tokens: List[Token], op_idx: int) -> Optional[str]:
        """Find the column name before an operator"""
        j = op_idx - 1
        parts = []
        while j >= 0 and tokens[j].type in (TokenType.IDENTIFIER, TokenType.ADJECTIVE,
                                              TokenType.COLUMN_NAME, TokenType.TABLE_NAME):
            parts.insert(0, tokens[j].value)
            j -= 1
        return "_".join(parts) if parts else None

    def _find_value_after(self, tokens: List[Token], op_idx: int) -> Optional[str]:
        """Find the value after an operator"""
        j = op_idx + 1
        if j < len(tokens):
            if tokens[j].type in (TokenType.NUMBER, TokenType.STRING,
                                   TokenType.IDENTIFIER, TokenType.STATUS):
                return tokens[j].value
        return None

    # ── AST Building ──────────────────────────────────────────────

    def _build_ast(self, analysis: dict) -> ASTNode:
        """Build the appropriate AST from the analysis"""

        # Default table if none found
        if not analysis["tables"]:
            # _validate_analysis devrait avoir déjà géré ce cas,
            # mais par sécurité on tente l'inférence
            analysis["tables"] = self._infer_tables_from_context(analysis)

        if not analysis["tables"]:
            raise ParseError(
                "Erreur syntaxique: aucune table identifiée dans la requête. "
                "Précisez une entité cible (capteurs, mesures, interventions, etc.)."
            )

        main_table = analysis["tables"][0]

        # Build conditions
        conditions = self._build_conditions(analysis, main_table)

        # Build joins
        joins = self._build_joins(analysis["tables"])

        # Build based on query type
        if analysis["query_type"] == "count":
            return self._build_count(analysis, main_table, joins, conditions)
        elif analysis["query_type"] == "aggregate":
            return self._build_aggregate(analysis, main_table, joins, conditions)
        else:
            return self._build_select(analysis, main_table, joins, conditions)

    def _build_conditions(self, analysis: dict, main_table: str) -> List[Condition]:
        """Build WHERE conditions from analysis"""
        conditions = []
        all_tables = analysis["tables"]

        # Status conditions
        for status_val in analysis["statuses"]:
            resolved = self.schema.resolve_status(status_val) or status_val
            # Determine which table has Statut
            status_table = main_table
            for t in all_tables:
                if self.schema.column_exists(t, "Statut") or self.schema.column_exists(t, "statut"):
                    status_table = t
                    break

            # Find the correct column name (Statut or statut)
            col_name = "Statut"
            if status_table in self.schema.tables:
                tdef = self.schema.tables[status_table]
                if tdef.has_column("statut") and not tdef.has_column("Statut"):
                    col_name = "statut"
                elif tdef.has_column("Statut"):
                    col_name = "Statut"

            conditions.append(Condition(
                left=col_name, left_table=status_table,
                operator="=", right=resolved
            ))

        # Grandeur conditions
        for g in analysis["grandeurs"]:
            resolved_g = self.schema.resolve_grandeur(g) or g.upper()
            conditions.append(Condition(
                left="NomGrandeur", left_table="mesures1",
                operator="=", right=resolved_g
            ))

        # Type capteur conditions
        for tc in analysis["types_capteur"]:
            resolved_tc = self.schema.resolve_type_capteur(tc) or tc
            conditions.append(Condition(
                left="Type", left_table="capteur",
                operator="=", right=resolved_tc
            ))

        # Nature intervention conditions
        for nat in analysis["natures"]:
            resolved_nat = self.schema.resolve_nature_intervention(nat) or nat
            conditions.append(Condition(
                left="Nature", left_table="intervention",
                operator="=", right=resolved_nat
            ))

        # Explicit operator conditions
        for cond in analysis["conditions"]:
            col_word = cond["left"]
            # Resolve the column
            resolved = self.schema.resolve_column_for_tables(col_word, all_tables)
            if resolved:
                col_table, col_name = resolved
            else:
                col_table = main_table
                col_name = col_word

            conditions.append(Condition(
                left=col_name, left_table=col_table,
                operator=cond["operator"],
                right=cond["right"],
                right_is_number=cond["right_is_number"]
            ))

        # Event filters (for capteurs_history)
        for ef in analysis.get("event_filters", []):
            # Normalize the event value
            raw = ef.lower().replace("en_", "").replace("_", " ")
            conditions.append(Condition(
                left="event", left_table="capteurs_history",
                operator="=", right=raw
            ))

        # Preference filters (citoyen.Préférences LIKE '%vélo%')
        for pf in analysis.get("preference_filters", []):
            conditions.append(Condition(
                left="Préférences", left_table="citoyen",
                operator="LIKE", right=f"%{pf}%"
            ))

        # Energy type filters (véhicule.Énergie Utilisée = 'Électrique')
        for ef in analysis.get("energy_filters", []):
            conditions.append(Condition(
                left="Énergie Utilisée", left_table="véhicule",
                operator="=", right=ef
            ))

        # Apply negation: if has_negation and we have status conditions, flip = to !=
        if analysis.get("has_negation") and conditions:
            for i, c in enumerate(conditions):
                if c.left.lower() in ("statut", "status") and c.operator == "=":
                    conditions[i] = Condition(
                        left=c.left, left_table=c.left_table,
                        operator="!=", right=c.right,
                        right_is_number=c.right_is_number
                    )

        return conditions

    def _build_joins(self, tables: List[str]) -> List[JoinClause]:
        """Build JOIN clauses by finding FK paths between tables"""
        if len(tables) <= 1:
            return []

        join_path = self.schema.find_join_path(tables)
        joins = []
        for (t_from, t_to, c_from, c_to) in join_path:
            joins.append(JoinClause(
                table=t_to,
                from_table=t_from,
                from_col=c_from,
                to_col=c_to
            ))
        return joins

    def _build_select(self, analysis: dict, main_table: str,
                      joins: List[JoinClause], conditions: List[Condition]) -> SelectQuery:
        """Build a SELECT query"""
        columns = [ColumnRef(name="*")]

        # Order by
        order_by = []
        if analysis["superlative"]:
            direction, adj = analysis["superlative"]
            sort_col = self._resolve_sort_column(adj, analysis, main_table)
            order_by = [OrderBy(column=sort_col, direction=direction)]
            # Default limit for superlatives
            if analysis["limit"] is None:
                analysis["limit"] = 1

        # Group by
        group_by = []
        if analysis["group_by"]:
            gb_col = self._resolve_group_column(analysis["group_by"], analysis["tables"])
            if gb_col:
                group_by = [GroupByClause(column=gb_col[1], table=gb_col[0])]
                # Add the group column and count to SELECT
                columns = [
                    ColumnRef(name=gb_col[1], table=gb_col[0]),
                    ColumnRef(name="*", function="COUNT", alias="total"),
                ]

        return SelectQuery(
            columns=columns,
            table=main_table,
            joins=joins,
            conditions=conditions,
            group_by=group_by,
            order_by=order_by,
            limit=analysis["limit"],
        )

    def _build_count(self, analysis: dict, main_table: str,
                     joins: List[JoinClause], conditions: List[Condition]) -> CountQuery:
        """Build a COUNT query"""
        group_by = []
        if analysis["group_by"]:
            gb_col = self._resolve_group_column(analysis["group_by"], analysis["tables"])
            if gb_col:
                group_by = [GroupByClause(column=gb_col[1], table=gb_col[0])]

        return CountQuery(
            table=main_table,
            joins=joins,
            conditions=conditions,
            group_by=group_by,
        )

    def _build_aggregate(self, analysis: dict, main_table: str,
                         joins: List[JoinClause], conditions: List[Condition]) -> AggregateQuery:
        """Build an AGGREGATE query"""
        func = analysis["function"] or "avg"

        # Find the column to aggregate
        agg_col = "Valeur"
        agg_table = main_table

        # Try to find from identifiers
        for ident in analysis["identifiers"]:
            resolved = self.schema.resolve_column_for_tables(ident, analysis["tables"])
            if resolved:
                agg_table, agg_col = resolved
                break

        # Group by
        group_by = []
        order_by = None
        if analysis["group_by"]:
            gb_col = self._resolve_group_column(analysis["group_by"], analysis["tables"])
            if gb_col:
                group_by = [GroupByClause(column=gb_col[1], table=gb_col[0])]

        return AggregateQuery(
            function=func,
            column=agg_col,
            column_table=agg_table,
            table=main_table,
            joins=joins,
            conditions=conditions,
            group_by=group_by,
            order_by=order_by,
            limit=analysis["limit"],
        )

    # ── Resolution Helpers ────────────────────────────────────────

    def _infer_tables_from_context(self, analysis: dict) -> List[str]:
        """Infer tables when none are explicitly mentioned"""
        tables = []

        # From adjectives
        for adj in analysis["adjectives"]:
            if adj in self.ADJECTIVE_TABLE_MAP:
                t = self.ADJECTIVE_TABLE_MAP[adj]
                if t not in tables:
                    tables.append(t)

        # From grandeurs
        if analysis["grandeurs"]:
            if "mesures1" not in tables:
                tables.append("mesures1")

        # From natures
        if analysis["natures"]:
            if "intervention" not in tables:
                tables.append("intervention")

        # From types_capteur
        if analysis["types_capteur"]:
            if "capteur" not in tables:
                tables.append("capteur")

        # From preference_filters
        if analysis.get("preference_filters"):
            if "citoyen" not in tables:
                tables.append("citoyen")

        # From energy_filters
        if analysis.get("energy_filters"):
            if "véhicule" not in tables:
                tables.append("véhicule")

        # From identifiers
        for ident in analysis["identifiers"]:
            resolved = self.schema.resolve_table_name(ident)
            if resolved and resolved not in tables:
                tables.append(resolved)

        # From conditions
        for cond in analysis["conditions"]:
            col = cond["left"]
            hits = self.schema.resolve_column(col)
            if hits and hits[0] not in tables:
                tables.append(hits[0])

        return tables if tables else ["capteur"]

    def _resolve_sort_column(self, adj: str, analysis: dict, main_table: str) -> str:
        """Resolve the column to sort by from an adjective"""
        adj_lower = adj.lower() if adj else ""

        # Direct adjective mapping
        if adj_lower in self.ADJECTIVE_SORT_MAP:
            return self.ADJECTIVE_SORT_MAP[adj_lower]

        # Try to resolve as column
        if adj_lower:
            resolved = self.schema.resolve_column_for_tables(adj_lower, analysis["tables"])
            if resolved:
                return resolved[1]

        # Default based on table
        if main_table == "mesures1":
            return "Valeur"
        elif main_table == "intervention":
            return "DateHeure"
        elif main_table == "trajet":
            return "ÉconomieCO2"
        elif main_table == "citoyen":
            return "Score"

        return "id"

    def _resolve_group_column(self, word: str, tables: List[str]) -> Optional[Tuple[str, str]]:
        """Resolve the column to GROUP BY"""
        w = word.lower()

        # Direct column resolution
        resolved = self.schema.resolve_column_for_tables(w, tables)
        if resolved:
            return resolved

        # Common grouping patterns
        group_hints = {
            "type": ("capteur", "Type"),
            "statut": ("capteur", "Statut"),
            "status": ("capteur", "Statut"),
            "état": ("capteur", "Statut"),
            "nature": ("intervention", "Nature"),
            "énergie": ("véhicule", "Énergie Utilisée"),
            "energie": ("véhicule", "Énergie Utilisée"),
            "grandeur": ("mesures1", "NomGrandeur"),
            "nom_grandeur": ("mesures1", "NomGrandeur"),
            "mode": ("consultation", "Mode"),
            "adresse": ("citoyen", "Adresse"),
            "propriété": ("propriétaire", "Propriété"),
            "rôle": ("supervision", "Rôle"),
            "capteur": ("mesures1", "UUID"),
            "zone": ("mesures1", "UUID"),
        }

        if w in group_hints:
            return group_hints[w]

        # Fallback: if the word is a table name, group by its PK
        resolved_table = self.schema.resolve_table_name(w)
        if resolved_table and resolved_table in self.schema.tables:
            pks = self.schema.tables[resolved_table].pk
            if pks:
                return (resolved_table, pks[0].name)

        return None
