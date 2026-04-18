"""
Lexer — Tokenisation du langage naturel français
Version universelle: supporte TOUTE requête sur la BD sousse_smart_city

Pipeline: Texte brut → Liste de Tokens typés

Grammaire lexicale (expressions rationnelles — cf. Cours 6, slides 8-9):
  lettre     = [a-zA-ZéèêëàâùûôîïçÉÈÊËÀÂÙÛÔÎÏÇ]
  chiffre    = [0-9]
  mot        = (lettre | '-' | '_' | "'") (lettre | chiffre | '-' | '_' | "'")*
  nombre     = chiffre+ ('.' chiffre+)?
  operateur  = '<' | '<=' | '>' | '>=' | '=' | '!=' | '<>'
  ponctuation = '(' | ')' | ',' | '?'
  ws         = (' ' | '\t' | '\n')+
  chaine     = "'" [^']* "'" | '"' [^"]* '"'

Automate du lexer (cf. Cours 6, slide 11-12):
  État 0 (initial): lire caractère c
    si ws           → rester en 0 (ignorer)
    si lettre       → état 1 (accumulation mot)
    si chiffre      → état 2 (accumulation nombre)
    si '<','>','!','=' → état 3 (opérateur)
    si quote        → état 4 (chaîne)
    si ponctuation  → émettre token, rester en 0
    sinon           → ERREUR lexicale (caractère inconnu)
  État 1 (mot): accumuler lettres/chiffres/tirets
    en sortie → classifier via table de mots-clés (install_id)
    si mot ∈ KEYWORDS     → token typé (VERB, QUESTION, etc.)
    si mot ∈ TABLE_WORDS  → TABLE_NAME
    si mot ∈ GRANDEUR_WORDS → GRANDEUR
    sinon                 → UNKNOWN (erreur lexicale: mot non reconnu)
  État 2 (nombre): accumuler chiffres et '.'
    en sortie → NUMBER
  État 3 (opérateur): anticiper '=' pour <=, >=, !=, ==
    en sortie → OPERATOR
  État 4 (chaîne): accumuler jusqu'à quote fermante
    en sortie → STRING

Exemples de requêtes supportées:
  - "Affiche les 7 zones les plus polluées en NO2"
  - "Combien de capteurs sont hors service ?"
  - "Quels citoyens ont un score écologique > 80 ?"
  - "Donne-moi le trajet le plus économique en CO2"
  - "Liste les interventions correctives avec leur technicien"
  - + n'importe quelle requête sur les 17 tables de la BD
"""

from enum import Enum, auto
from typing import List, NamedTuple, Optional
import re


class TokenType(Enum):
    # Verbs / Actions
    VERB = "VERB"                  # affiche, montre, donne, liste, trouve, calcule
    # Questions
    QUESTION = "QUESTION"          # combien, quels, quelles, quel, qui
    # Articles & determiners
    ARTICLE = "ARTICLE"            # le, la, les, un, une, des, du, l'
    # Prepositions
    PREPOSITION = "PREP"           # de, du, d', en, par, pour, avec, sur, dans
    # Conjunctions
    CONJUNCTION = "CONJ"           # et, ou
    # Superlatives / adjectives
    SUPERLATIVE = "SUPERLATIVE"    # plus, moins, meilleur
    ADJECTIVE = "ADJECTIVE"        # polluées, économique, actif, récent, etc.
    # Table names (recognized from schema)
    TABLE_NAME = "TABLE_NAME"
    # Column references
    COLUMN_NAME = "COLUMN_NAME"
    # Grandeur values (NO2, CO2, PM10, Luminosité, etc.)
    GRANDEUR = "GRANDEUR"
    # Identifiers (unknown words)
    IDENTIFIER = "IDENTIFIER"
    # Numbers
    NUMBER = "NUMBER"
    # Strings
    STRING = "STRING"
    # Operators
    OPERATOR = "OPERATOR"          # >, <, =, !=, >=, <=
    # Aggregate functions
    FUNCTION = "FUNCTION"          # moyenne, total, min, max, nombre, count
    # Status keywords (match DB enums)
    STATUS = "STATUS"              # actif, en_maintenance, hors_service, signalé
    # Type keywords (match DB enums)
    TYPE_CAPTEUR = "TYPE_CAPTEUR"  # éclairage, déchets, trafic, énergie, qualité air
    # Nature intervention
    NATURE = "NATURE"              # prédictive, corrective, curative
    # Punctuation
    LPAREN = "LPAREN"
    RPAREN = "RPAREN"
    COMMA = "COMMA"
    QUESTION_MARK = "QMARK"
    # Special
    PRONOUN = "PRONOUN"            # moi, me, nous, je
    AUXILIARY = "AUXILIARY"        # sont, est, ont, a, avoir, être
    NEGATION = "NEGATION"          # ne, pas, n'
    # Grouping
    GROUP_KEYWORD = "GROUP_KW"     # par, chaque, selon, groupé
    # Temporal
    TEMPORAL = "TEMPORAL"          # depuis, avant, après, entre, dernier, récent
    EOF = "EOF"
    UNKNOWN = "UNKNOWN"


class Token(NamedTuple):
    type: TokenType
    value: str
    position: int = 0
    original: str = ""  # original form before lowering


class Lexer:
    """
    Lexer universel pour tokenisation du langage naturel français.
    Implémente un automate fini déterministe (cf. Cours 6, slides 11-15)
    avec reconnaissance par table de mots-clés (table des symboles).

    Gestion d'erreurs:
    - Mots non reconnus → token UNKNOWN + erreur lexicale enregistrée
    - Caractères invalides → erreur lexicale (cf. fail() du cours 6, slide 14)
    """

    # ── Keyword dictionaries ──────────────────────────────────────

    KEYWORDS = {
        # ── Verbes ──
        "affiche": TokenType.VERB, "afficher": TokenType.VERB,
        "affiche-moi": TokenType.VERB,
        "montre": TokenType.VERB, "montrer": TokenType.VERB,
        "montre-moi": TokenType.VERB,
        "donne": TokenType.VERB, "donner": TokenType.VERB,
        "donne-moi": TokenType.VERB,
        "liste": TokenType.VERB, "lister": TokenType.VERB,
        "trouve": TokenType.VERB, "trouver": TokenType.VERB,
        "cherche": TokenType.VERB, "chercher": TokenType.VERB,
        "sélectionne": TokenType.VERB, "sélectionner": TokenType.VERB,
        "selectionne": TokenType.VERB,
        "calcule": TokenType.VERB, "calculer": TokenType.VERB,
        "résume": TokenType.VERB, "résumer": TokenType.VERB,
        "compare": TokenType.VERB, "comparer": TokenType.VERB,
        "identifie": TokenType.VERB, "identifier": TokenType.VERB,
        "extrais": TokenType.VERB, "extraire": TokenType.VERB,
        "récupère": TokenType.VERB, "récupérer": TokenType.VERB,
        "recupere": TokenType.VERB, "recuperer": TokenType.VERB,
        "obtiens": TokenType.VERB,
        "préfèrent": TokenType.VERB, "préfère": TokenType.VERB,
        "prefere": TokenType.VERB, "preferent": TokenType.VERB,
        "dépassent": TokenType.VERB, "dépasse": TokenType.VERB,
        "depassent": TokenType.VERB, "depasse": TokenType.VERB,
        "historique": TokenType.VERB,

        # ── Questions ──
        "combien": TokenType.QUESTION,
        "quels": TokenType.QUESTION, "quelles": TokenType.QUESTION,
        "quel": TokenType.QUESTION, "quelle": TokenType.QUESTION,
        "qui": TokenType.QUESTION, "où": TokenType.QUESTION, "ou": TokenType.CONJUNCTION,

        # ── Articles ──
        "le": TokenType.ARTICLE, "la": TokenType.ARTICLE,
        "les": TokenType.ARTICLE,
        "un": TokenType.ARTICLE, "une": TokenType.ARTICLE,
        "des": TokenType.ARTICLE, "du": TokenType.ARTICLE,
        "l": TokenType.ARTICLE, "au": TokenType.ARTICLE,
        "aux": TokenType.ARTICLE, "ce": TokenType.ARTICLE,
        "cette": TokenType.ARTICLE, "ces": TokenType.ARTICLE,
        "leur": TokenType.ARTICLE, "leurs": TokenType.ARTICLE,
        "son": TokenType.ARTICLE, "sa": TokenType.ARTICLE, "ses": TokenType.ARTICLE,

        # ── Prépositions ──
        "de": TokenType.PREPOSITION, "d": TokenType.PREPOSITION,
        "en": TokenType.PREPOSITION,
        "pour": TokenType.PREPOSITION,
        "avec": TokenType.PREPOSITION,
        "sur": TokenType.PREPOSITION,
        "dans": TokenType.PREPOSITION,
        "entre": TokenType.PREPOSITION,
        "sans": TokenType.PREPOSITION,
        "vers": TokenType.PREPOSITION,
        "depuis": TokenType.TEMPORAL,
        "avant": TokenType.TEMPORAL,
        "après": TokenType.TEMPORAL,
        "apres": TokenType.TEMPORAL,

        # ── Conjonctions ──
        "et": TokenType.CONJUNCTION, "ou": TokenType.CONJUNCTION,

        # ── Superlatifs ──
        "plus": TokenType.SUPERLATIVE, "moins": TokenType.SUPERLATIVE,
        "meilleur": TokenType.SUPERLATIVE, "meilleure": TokenType.SUPERLATIVE,
        "pire": TokenType.SUPERLATIVE,
        "premier": TokenType.SUPERLATIVE, "première": TokenType.SUPERLATIVE,
        "dernier": TokenType.SUPERLATIVE, "dernière": TokenType.SUPERLATIVE,
        "top": TokenType.SUPERLATIVE,

        # ── Adjectifs (domaine) ──
        "polluées": TokenType.ADJECTIVE, "polluée": TokenType.ADJECTIVE,
        "pollués": TokenType.ADJECTIVE, "pollué": TokenType.ADJECTIVE,
        "polluees": TokenType.ADJECTIVE, "polluee": TokenType.ADJECTIVE,
        "pollues": TokenType.ADJECTIVE,
        "économique": TokenType.ADJECTIVE, "économiques": TokenType.ADJECTIVE,
        "economique": TokenType.ADJECTIVE, "economiques": TokenType.ADJECTIVE,
        "ecologique": TokenType.ADJECTIVE, "écologique": TokenType.ADJECTIVE,
        "écologiques": TokenType.ADJECTIVE, "ecologiques": TokenType.ADJECTIVE,
        "actifs": TokenType.ADJECTIVE, "actives": TokenType.ADJECTIVE,
        "récent": TokenType.ADJECTIVE, "récents": TokenType.ADJECTIVE,
        "récentes": TokenType.ADJECTIVE, "récente": TokenType.ADJECTIVE,
        "recent": TokenType.ADJECTIVE, "recents": TokenType.ADJECTIVE,
        "recentes": TokenType.ADJECTIVE, "recente": TokenType.ADJECTIVE,
        "cher": TokenType.ADJECTIVE, "chère": TokenType.ADJECTIVE,
        "coûteux": TokenType.ADJECTIVE, "coûteuse": TokenType.ADJECTIVE,
        "couteux": TokenType.ADJECTIVE, "couteuse": TokenType.ADJECTIVE,
        "long": TokenType.ADJECTIVE, "longue": TokenType.ADJECTIVE,
        "court": TokenType.ADJECTIVE, "courte": TokenType.ADJECTIVE,
        "élevé": TokenType.ADJECTIVE, "élevée": TokenType.ADJECTIVE,
        "eleve": TokenType.ADJECTIVE, "elevee": TokenType.ADJECTIVE,
        "faible": TokenType.ADJECTIVE, "faibles": TokenType.ADJECTIVE,
        "disponible": TokenType.ADJECTIVE, "disponibles": TokenType.ADJECTIVE,
        "assigné": TokenType.ADJECTIVE, "assignés": TokenType.ADJECTIVE,
        "assigne": TokenType.ADJECTIVE, "assignes": TokenType.ADJECTIVE,
        "autonome": TokenType.ADJECTIVE, "autonomes": TokenType.ADJECTIVE,
        "urbain": TokenType.ADJECTIVE, "urbaine": TokenType.ADJECTIVE,
        "urbains": TokenType.ADJECTIVE, "urbaines": TokenType.ADJECTIVE,
        "intelligent": TokenType.ADJECTIVE, "intelligente": TokenType.ADJECTIVE,
        "intelligents": TokenType.ADJECTIVE, "intelligentes": TokenType.ADJECTIVE,
        "dernière": TokenType.ADJECTIVE, "derniere": TokenType.ADJECTIVE,
        "dernieres": TokenType.ADJECTIVE, "dernières": TokenType.ADJECTIVE,

        # ── Fonctions d'agrégation ──
        "moyenne": TokenType.FUNCTION, "total": TokenType.FUNCTION,
        "somme": TokenType.FUNCTION,
        "min": TokenType.FUNCTION, "max": TokenType.FUNCTION,
        "nombre": TokenType.FUNCTION, "count": TokenType.FUNCTION,
        "sum": TokenType.FUNCTION, "avg": TokenType.FUNCTION,
        "minimum": TokenType.FUNCTION, "maximum": TokenType.FUNCTION,

        # ── Statuts (toutes tables) ──
        "actif": TokenType.STATUS, "active": TokenType.STATUS,
        "maintenance": TokenType.STATUS,
        "signalé": TokenType.STATUS, "signale": TokenType.STATUS,
        "stationné": TokenType.STATUS, "stationne": TokenType.STATUS,
        "arrivé": TokenType.STATUS, "arrive": TokenType.STATUS,
        "terminée": TokenType.STATUS, "terminee": TokenType.STATUS,
        "terminé": TokenType.STATUS, "terminées": TokenType.STATUS,
        "terminés": TokenType.STATUS, "terminees": TokenType.STATUS,
        "demande": TokenType.STATUS,
        "fini": TokenType.STATUS, "finie": TokenType.STATUS,
        "finis": TokenType.STATUS, "finies": TokenType.STATUS,
        "panne": TokenType.STATUS,
        "inactif": TokenType.STATUS, "inactive": TokenType.STATUS,

        # ── Types de capteur ──
        "éclairage": TokenType.TYPE_CAPTEUR, "eclairage": TokenType.TYPE_CAPTEUR,
        "déchets": TokenType.TYPE_CAPTEUR, "dechets": TokenType.TYPE_CAPTEUR,
        "trafic": TokenType.TYPE_CAPTEUR, "traffic": TokenType.TYPE_CAPTEUR,
        "énergie": TokenType.TYPE_CAPTEUR, "energie": TokenType.TYPE_CAPTEUR,

        # ── Nature intervention ──
        "prédictive": TokenType.NATURE, "predictive": TokenType.NATURE,
        "corrective": TokenType.NATURE, "correctives": TokenType.NATURE,
        "curative": TokenType.NATURE, "curatives": TokenType.NATURE,
        "prédictives": TokenType.NATURE, "predictives": TokenType.NATURE,

        # ── Noms de colonnes (COLUMN_NAME) ──
        "score": TokenType.COLUMN_NAME,
        "type": TokenType.COLUMN_NAME,
        "nom": TokenType.COLUMN_NAME,
        "statut": TokenType.COLUMN_NAME,
        "date": TokenType.COLUMN_NAME,
        "valeur": TokenType.COLUMN_NAME,
        "adresse": TokenType.COLUMN_NAME,
        "coût": TokenType.COLUMN_NAME, "cout": TokenType.COLUMN_NAME,
        "durée": TokenType.COLUMN_NAME, "duree": TokenType.COLUMN_NAME,
        "latitude": TokenType.COLUMN_NAME, "longitude": TokenType.COLUMN_NAME,
        "isp": TokenType.COLUMN_NAME,
        "priorité": TokenType.COLUMN_NAME, "priorite": TokenType.COLUMN_NAME,
        "description": TokenType.COLUMN_NAME,
        "pollution": TokenType.COLUMN_NAME,
        "installation": TokenType.COLUMN_NAME,
        # Colonnes intervention
        "nature": TokenType.NATURE,
        "dateheure": TokenType.COLUMN_NAME,
        "impactco2": TokenType.COLUMN_NAME,
        "impact": TokenType.COLUMN_NAME,
        # Colonnes trajet
        "origine": TokenType.COLUMN_NAME,
        "destination": TokenType.COLUMN_NAME,
        "économieco2": TokenType.COLUMN_NAME, "economieco2": TokenType.COLUMN_NAME,
        "économie": TokenType.COLUMN_NAME, "economie": TokenType.COLUMN_NAME,
        "plaque": TokenType.COLUMN_NAME,
        # Colonnes citoyen
        "téléphone": TokenType.COLUMN_NAME, "telephone": TokenType.COLUMN_NAME,
        "email": TokenType.COLUMN_NAME,
        "préférences": TokenType.COLUMN_NAME, "preferences": TokenType.COLUMN_NAME,
        # Colonnes mesures
        "nomgrandeur": TokenType.COLUMN_NAME,
        "grandeur": TokenType.COLUMN_NAME,
        "unité": TokenType.COLUMN_NAME, "unite": TokenType.COLUMN_NAME,
        # Colonnes consultation
        "sujet": TokenType.COLUMN_NAME,
        "mode": TokenType.COLUMN_NAME,
        # Colonnes technicien
        "numéro": TokenType.COLUMN_NAME, "numero": TokenType.COLUMN_NAME,
        "rôle": TokenType.COLUMN_NAME, "role": TokenType.COLUMN_NAME,
        # Colonnes participation
        "heure": TokenType.COLUMN_NAME,
        # Colonnes rapports IA
        "diagnostic": TokenType.COLUMN_NAME,
        "solution": TokenType.COLUMN_NAME,
        "confiance": TokenType.COLUMN_NAME,
        # Colonnes véhicule
        "propriété": TokenType.COLUMN_NAME, "propriete": TokenType.COLUMN_NAME,
        # Colonnes ID (termes techniques)
        "uuid": TokenType.COLUMN_NAME, "id": TokenType.COLUMN_NAME,

        # ── Préférences citoyen (filtre LIKE) ──
        "vélo": TokenType.IDENTIFIER, "velo": TokenType.IDENTIFIER,
        "marche": TokenType.IDENTIFIER,
        "transport": TokenType.IDENTIFIER,
        "ia": TokenType.IDENTIFIER,
        "artificielle": TokenType.IDENTIFIER,
        # ── Zones géographiques ──
        "nord": TokenType.IDENTIFIER, "sud": TokenType.IDENTIFIER,
        "est": TokenType.IDENTIFIER, "ouest": TokenType.IDENTIFIER,
        "centre": TokenType.IDENTIFIER,

        # ── Énergie véhicule ──
        "électrique": TokenType.ADJECTIVE, "electrique": TokenType.ADJECTIVE,
        "électriques": TokenType.ADJECTIVE, "electriques": TokenType.ADJECTIVE,
        "hybride": TokenType.ADJECTIVE, "hybrides": TokenType.ADJECTIVE,
        "hydrogène": TokenType.ADJECTIVE, "hydrogene": TokenType.ADJECTIVE,

        # ── Noms de grandeur (mesures) ──
        "no2": TokenType.GRANDEUR, "co2": TokenType.GRANDEUR,
        "pm10": TokenType.GRANDEUR, "pm2.5": TokenType.GRANDEUR,
        "so2": TokenType.GRANDEUR, "o3": TokenType.GRANDEUR,
        "ozone": TokenType.GRANDEUR,

        # ── Mots du domaine Smart City ──
        "qualité": TokenType.IDENTIFIER, "qualite": TokenType.IDENTIFIER,
        "air": TokenType.IDENTIFIER,
        "service": TokenType.IDENTIFIER,
        "hors": TokenType.IDENTIFIER,
        "route": TokenType.IDENTIFIER,
        "seuil": TokenType.IDENTIFIER, "seuils": TokenType.IDENTIFIER,
        "donné": TokenType.IDENTIFIER, "données": TokenType.IDENTIFIER,
        "résultat": TokenType.IDENTIFIER, "résultats": TokenType.IDENTIFIER,
        "information": TokenType.IDENTIFIER, "informations": TokenType.IDENTIFIER,
        "alerte": TokenType.IDENTIFIER, "alertes": TokenType.IDENTIFIER,
        "rapport": TokenType.TABLE_NAME, "rapports": TokenType.TABLE_NAME,

        # ── Verbes supplémentaires du domaine ──
        "dépassent": TokenType.VERB, "dépasse": TokenType.VERB,
        "dépassant": TokenType.ADJECTIVE,
        "supérieur": TokenType.ADJECTIVE, "supérieure": TokenType.ADJECTIVE,
        "inférieur": TokenType.ADJECTIVE, "inférieure": TokenType.ADJECTIVE,

        # ── Groupement ──
        "par": TokenType.GROUP_KEYWORD,
        "chaque": TokenType.GROUP_KEYWORD,
        "selon": TokenType.GROUP_KEYWORD,
        "groupé": TokenType.GROUP_KEYWORD,
        "grouper": TokenType.GROUP_KEYWORD,

        # ── Pronoms ──
        "moi": TokenType.PRONOUN, "me": TokenType.PRONOUN,
        "nous": TokenType.PRONOUN, "je": TokenType.PRONOUN,

        # ── Auxiliaires ──
        "sont": TokenType.AUXILIARY, "est": TokenType.AUXILIARY,
        "ont": TokenType.AUXILIARY, "a": TokenType.AUXILIARY,
        "avoir": TokenType.AUXILIARY, "être": TokenType.AUXILIARY,
        "fait": TokenType.AUXILIARY, "font": TokenType.AUXILIARY,

        # ── Négation ──
        "ne": TokenType.NEGATION, "pas": TokenType.NEGATION,
        "n": TokenType.NEGATION, "aucun": TokenType.NEGATION,
        "aucune": TokenType.NEGATION, "jamais": TokenType.NEGATION,
    }

    # Table name recognition (French words → table name token)
    TABLE_WORDS = {
        "capteur", "capteurs", "sensor", "sensors", "sonde", "sondes",
        "détecteur", "détecteurs",
        "mesure", "mesures", "mesures1", "mesures2", "relevé", "relevés",
        "zone", "zones",
        "intervention", "interventions", "réparation", "réparations",
        "citoyen", "citoyens", "habitant", "habitants", "personne", "personnes",
        "utilisateur", "utilisateurs",
        "consultation", "consultations", "sondage", "sondages",
        "participation", "participations",
        "technicien", "techniciens", "tech", "techs",
        "propriétaire", "propriétaires", "proprietaire", "proprietaires",
        "proprio", "proprios",
        "véhicule", "véhicules", "vehicule", "vehicules",
        "voiture", "voitures", "bus", "camion", "camions",
        "trajet", "trajets", "itinéraire", "itinéraires", "parcours",
        "supervision", "supervisions",
        "history",
        "log", "logs", "journal", "journaux", "audit",
        "rapport", "rapports",
        "événement", "evenement", "événements", "evenements",
        "rapports_ia", "diagnostics",
    }

    # Grandeur names (mesures1.NomGrandeur values)
    GRANDEUR_WORDS = {
        "luminosité", "luminosite", "température", "temperature",
        "humidité", "humidite", "bruit", "pression",
        "vent", "courant", "tension", "puissance",
        "vitesse",
    }

    # Multi-word status expressions
    MULTI_WORD_EXPR = {
        "hors service": ("STATUS", "hors_service"),
        "en maintenance": ("STATUS", "en_maintenance"),
        "en route": ("STATUS", "en_route"),
        "en panne": ("STATUS", "en_panne"),
        "en cours": ("STATUS", "en_cours"),
        "en ligne": ("STATUS", "en_ligne"),
        "qualité de l'air": ("TYPE_CAPTEUR", "qualité_air"),
        "qualite de l'air": ("TYPE_CAPTEUR", "qualité_air"),
        "qualité d'air": ("TYPE_CAPTEUR", "qualité_air"),
        "qualite d'air": ("TYPE_CAPTEUR", "qualité_air"),
        "qualité air": ("TYPE_CAPTEUR", "qualité_air"),
        "date installation": ("COLUMN_NAME", "date_installation"),
        "énergie utilisée": ("COLUMN_NAME", "énergie_utilisée"),
        "energie utilisée": ("COLUMN_NAME", "énergie_utilisée"),
        "energie utilisee": ("COLUMN_NAME", "énergie_utilisée"),
        "economie co2": ("COLUMN_NAME", "économie_co2"),
        "économie co2": ("COLUMN_NAME", "économie_co2"),
        "taux de remplissage": ("GRANDEUR", "taux_remplissage"),
        "densité trafic": ("GRANDEUR", "densité_trafic"),
    }

    OPERATORS = {"<", ">", "=", "!=", "<>", ">=", "<="}

    def __init__(self, text: str):
        self.original_text = text.strip()
        self.text = text.lower().strip()
        self.position = 0
        self.tokens: List[Token] = []
        self.errors: List[str] = []      # Erreurs lexicales détectées
        self.unknown_words: List[str] = []  # Mots non reconnus

    def _char(self) -> Optional[str]:
        return self.text[self.position] if self.position < len(self.text) else None

    def _peek(self, n: int = 1) -> Optional[str]:
        p = self.position + n
        return self.text[p] if p < len(self.text) else None

    def _advance(self, n: int = 1):
        self.position += n

    def _skip_ws(self):
        while self._char() and self._char().isspace():
            self._advance()

    def _remaining(self) -> str:
        return self.text[self.position:]

    def tokenize(self) -> List[Token]:
        """Tokenise l'entrée complète"""
        self.tokens = []
        self.position = 0

        while self.position < len(self.text):
            self._skip_ws()
            if self.position >= len(self.text):
                break

            ch = self._char()

            # Check multi-word expressions first (longest match)
            matched_multi = False
            for expr, (tok_type_str, tok_val) in sorted(
                self.MULTI_WORD_EXPR.items(), key=lambda x: -len(x[0])
            ):
                if self._remaining().startswith(expr):
                    end = self.position + len(expr)
                    if end >= len(self.text) or not self.text[end].isalnum():
                        tt = getattr(TokenType, tok_type_str)
                        self.tokens.append(Token(tt, tok_val, self.position, expr))
                        self._advance(len(expr))
                        matched_multi = True
                        break
            if matched_multi:
                continue

            # Numbers (including decimals like 2.5)
            if ch.isdigit():
                start = self.position
                num = ""
                while self._char() and (self._char().isdigit() or self._char() == "."):
                    num += self._char()
                    self._advance()
                self.tokens.append(Token(TokenType.NUMBER, num, start))

            # Words (including accented chars, hyphens)
            elif ch.isalpha() or ch in ("é", "è", "ê", "ë", "à", "â", "ù", "û", "ô", "î", "ï", "ç"):
                start = self.position
                word = ""
                while self._char() and (self._char().isalnum() or self._char() in "-_'éèêëàâùûôîïçÉÈÊËÀÂÙÛÔÎÏÇ"):
                    # Handle contractions like "l'", "d'", "n'"
                    if self._char() == "'" and word in ("l", "d", "n", "j", "s", "c", "qu"):
                        word += self._char()
                        self._advance()
                        base = word.rstrip("'")
                        tok_type = self.KEYWORDS.get(base, TokenType.IDENTIFIER)
                        self.tokens.append(Token(tok_type, base, start))
                        word = ""
                        start = self.position
                        continue
                    word += self._char()
                    self._advance()

                if word:
                    tok_type = self._classify_word(word)
                    self.tokens.append(Token(tok_type, word, start))

            # Strings
            elif ch in ("'", '"'):
                start = self.position
                quote = ch
                self._advance()
                s = ""
                while self._char() and self._char() != quote:
                    s += self._char()
                    self._advance()
                if self._char() == quote:
                    self._advance()
                self.tokens.append(Token(TokenType.STRING, s, start))

            # Operators
            elif ch in ("<", ">", "!", "="):
                start = self.position
                op = ch
                self._advance()
                if self._char() and self._char() in ("=", ">"):
                    op += self._char()
                    self._advance()
                self.tokens.append(Token(TokenType.OPERATOR, op, start))

            # Punctuation
            elif ch == "(":
                self.tokens.append(Token(TokenType.LPAREN, ch, self.position))
                self._advance()
            elif ch == ")":
                self.tokens.append(Token(TokenType.RPAREN, ch, self.position))
                self._advance()
            elif ch == ",":
                self.tokens.append(Token(TokenType.COMMA, ch, self.position))
                self._advance()
            elif ch == "?":
                self.tokens.append(Token(TokenType.QUESTION_MARK, ch, self.position))
                self._advance()
            else:
                # État d'erreur: caractère non reconnu (cf. Cours 6, fail())
                self.errors.append(f"Caractère inconnu '{ch}' à la position {self.position}")
                self._advance()

        self.tokens.append(Token(TokenType.EOF, "", self.position))
        return self.tokens

    def _classify_word(self, word: str) -> TokenType:
        """
        Classifier un mot via la table des symboles (cf. Cours 6, install_id).
        Les mots non reconnus sont marqués UNKNOWN → erreur lexicale.
        """
        w = word.lower()

        # 1. Check keywords first (mots-clés réservés)
        if w in self.KEYWORDS:
            return self.KEYWORDS[w]

        # 2. Check table names (entités du schéma BD)
        if w in self.TABLE_WORDS:
            return TokenType.TABLE_NAME

        # 3. Check grandeur names (noms de mesures physiques)
        if w in self.GRANDEUR_WORDS:
            return TokenType.GRANDEUR

        # 4. Mot non reconnu → UNKNOWN (erreur lexicale)
        # Conforme au cours 6 : la fonction fail() signale les mots
        # qui ne correspondent à aucun automate de reconnaissance
        self.unknown_words.append(w)
        self.errors.append(f"Mot non reconnu: '{w}'")
        return TokenType.UNKNOWN

    def pretty_print(self) -> str:
        lines = []
        for t in self.tokens:
            if t.type != TokenType.EOF:
                lines.append(f"  {t.type.value:15s} │ {t.value}")
        return "\n".join(lines)
