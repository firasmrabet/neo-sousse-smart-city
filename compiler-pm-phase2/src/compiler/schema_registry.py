"""
Schema Registry — Registre centralisé du schéma BD sousse_smart_city_projet_module

Contient:
  - Toutes les tables et colonnes (17 tables)
  - Toutes les clés étrangères (FK)
  - Graphe de relations pour résolution automatique des JOIN (BFS)
  - Synonymes français exhaustifs (mots → tables, mots → colonnes)
  - Valeurs d'enum connues pour chaque colonne enum
"""

from typing import Dict, List, Set, Tuple, Optional
from collections import deque


# ═══════════════════════════════════════════════════════════════════
# Table and Column definitions
# ═══════════════════════════════════════════════════════════════════

class ColumnDef:
    """Définition d'une colonne"""
    def __init__(self, name: str, col_type: str = "varchar",
                 is_pk: bool = False, is_fk: bool = False,
                 fk_table: str = "", fk_column: str = "",
                 enum_values: List[str] = None,
                 needs_backtick: bool = False):
        self.name = name
        self.col_type = col_type
        self.is_pk = is_pk
        self.is_fk = is_fk
        self.fk_table = fk_table
        self.fk_column = fk_column
        self.enum_values = enum_values or []
        self.needs_backtick = needs_backtick

    @property
    def sql_name(self) -> str:
        if self.needs_backtick:
            return f"`{self.name}`"
        return self.name


class TableDef:
    """Définition d'une table"""
    def __init__(self, name: str, columns: List[ColumnDef]):
        self.name = name
        self.columns = {c.name: c for c in columns}
        self.pk = [c for c in columns if c.is_pk]
        self.fks = [c for c in columns if c.is_fk]

    def has_column(self, name: str) -> bool:
        return name in self.columns or name.lower() in {c.lower() for c in self.columns}

    def get_column(self, name: str) -> Optional[ColumnDef]:
        if name in self.columns:
            return self.columns[name]
        for cname, cdef in self.columns.items():
            if cname.lower() == name.lower():
                return cdef
        return None

    def column_names(self) -> List[str]:
        return list(self.columns.keys())


# ═══════════════════════════════════════════════════════════════════
# Schema Registry
# ═══════════════════════════════════════════════════════════════════

class SchemaRegistry:
    """
    Registre centralisé du schéma de la BD.
    Source unique de vérité pour tables, colonnes, FK, synonymes.
    """

    _instance = None

    @classmethod
    def get_instance(cls) -> 'SchemaRegistry':
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        self.tables: Dict[str, TableDef] = {}
        self._adjacency: Dict[str, Dict[str, Tuple[str, str]]] = {}
        self._word_to_tables: Dict[str, List[str]] = {}
        self._word_to_columns: Dict[str, List[Tuple[str, str]]] = {}
        self._value_synonyms: Dict[str, Dict[str, str]] = {}
        self._grandeur_synonyms: Dict[str, str] = {}
        self._type_capteur_synonyms: Dict[str, str] = {}
        self._nature_intervention_synonyms: Dict[str, str] = {}
        self._status_synonyms: Dict[str, str] = {}
        self._build_schema()
        self._build_graph()
        self._build_synonyms()

    # ── Schema definition ──────────────────────────────────────

    def _build_schema(self):
        """Définir toutes les tables et colonnes de la BD"""

        self._register_table(TableDef("capteur", [
            ColumnDef("UUID", "char(36)", is_pk=True),
            ColumnDef("Type", "enum", enum_values=["Éclairage", "Déchets", "Trafic", "Énergie", "Qualité de l'air"]),
            ColumnDef("Latitude", "decimal"),
            ColumnDef("Longitude", "decimal"),
            ColumnDef("Statut", "enum", enum_values=["Actif", "En Maintenance", "Hors Service", "Signalé"]),
            ColumnDef("Date Installation", "datetime", needs_backtick=True),
            ColumnDef("IDP", "int", is_fk=True, fk_table="propriétaire", fk_column="IDP"),
        ]))

        self._register_table(TableDef("mesures1", [
            ColumnDef("IDM", "int", is_pk=True),
            ColumnDef("NomGrandeur", "varchar", is_fk=True, fk_table="mesures2", fk_column="NomGrandeur"),
            ColumnDef("Valeur", "decimal"),
            ColumnDef("UUID", "char(36)", is_fk=True, fk_table="capteur", fk_column="UUID"),
        ]))

        self._register_table(TableDef("mesures2", [
            ColumnDef("NomGrandeur", "varchar", is_pk=True),
            ColumnDef("Unité", "varchar"),
        ]))

        self._register_table(TableDef("intervention", [
            ColumnDef("IDIn", "int", is_pk=True),
            ColumnDef("DateHeure", "datetime"),
            ColumnDef("Nature", "enum", enum_values=["Prédictive", "Corrective", "Curative"]),
            ColumnDef("Durée", "int"),
            ColumnDef("Coût", "decimal"),
            ColumnDef("ImpactCO2", "decimal"),
            ColumnDef("UUID", "char(36)", is_fk=True, fk_table="capteur", fk_column="UUID"),
            ColumnDef("statut", "enum", enum_values=["Demande", "Tech1_Assigné", "Tech2_Valide", "IA_Valide", "Terminée"]),
            ColumnDef("technicien_1_id", "int", is_fk=True, fk_table="technicien", fk_column="IDT"),
            ColumnDef("technicien_2_id", "int", is_fk=True, fk_table="technicien", fk_column="IDT"),
            ColumnDef("rapport_tech1", "text"),
            ColumnDef("rapport_tech2", "text"),
        ]))

        self._register_table(TableDef("citoyen", [
            ColumnDef("IDCI", "int", is_pk=True),
            ColumnDef("Nom", "varchar"),
            ColumnDef("Adresse", "text"),
            ColumnDef("Téléphone", "varchar"),
            ColumnDef("Email", "varchar"),
            ColumnDef("Score", "int"),
            ColumnDef("Préférences", "text"),
        ]))

        self._register_table(TableDef("consultation", [
            ColumnDef("IDCO", "int", is_pk=True),
            ColumnDef("IDCI", "int", is_fk=True, fk_table="citoyen", fk_column="IDCI"),
            ColumnDef("Sujet", "varchar"),
            ColumnDef("Mode", "enum", enum_values=["En ligne", "Présentiel", "Mixte"]),
        ]))

        self._register_table(TableDef("participation", [
            ColumnDef("IDPA", "int", is_pk=True),
            ColumnDef("IDCI", "int", is_fk=True, fk_table="citoyen", fk_column="IDCI"),
            ColumnDef("IDCO", "int", is_fk=True, fk_table="consultation", fk_column="IDCO"),
            ColumnDef("Date", "date"),
            ColumnDef("Heure", "varchar"),
        ]))

        self._register_table(TableDef("technicien", [
            ColumnDef("IDT", "int", is_pk=True),
            ColumnDef("Nom", "varchar"),
            ColumnDef("Numero", "varchar"),
        ]))

        self._register_table(TableDef("propriétaire", [
            ColumnDef("IDP", "int", is_pk=True),
            ColumnDef("Nom", "varchar"),
            ColumnDef("Adresse", "text"),
            ColumnDef("Téléphone", "varchar"),
            ColumnDef("Email", "varchar"),
            ColumnDef("Propriété", "enum", enum_values=["Municipalité", "Privé"]),
        ]))

        self._register_table(TableDef("véhicule", [
            ColumnDef("Plaque", "varchar", is_pk=True),
            ColumnDef("Type", "varchar"),
            ColumnDef("Énergie Utilisée", "enum", needs_backtick=True,
                       enum_values=["Électrique", "Hybride", "Hydrogène"]),
            ColumnDef("Statut", "enum", enum_values=["Stationné", "En Route", "Arrivé", "En Panne"]),
            ColumnDef("Latitude", "decimal"),
            ColumnDef("Longitude", "decimal"),
        ]))

        self._register_table(TableDef("trajet", [
            ColumnDef("IDTR", "int", is_pk=True),
            ColumnDef("Origine", "varchar"),
            ColumnDef("Destination", "varchar"),
            ColumnDef("Durée", "int"),
            ColumnDef("ÉconomieCO2", "decimal"),
            ColumnDef("Plaque", "varchar", is_fk=True, fk_table="véhicule", fk_column="Plaque"),
            ColumnDef("Date", "timestamp"),
        ]))

        self._register_table(TableDef("supervision", [
            ColumnDef("IDIn", "int", is_pk=True, is_fk=True, fk_table="intervention", fk_column="IDIn"),
            ColumnDef("IDT", "int", is_pk=True, is_fk=True, fk_table="technicien", fk_column="IDT"),
            ColumnDef("Rôle", "enum", enum_values=["Intervenant", "Validateur"]),
        ]))

        self._register_table(TableDef("capteurs_history", [
            ColumnDef("id", "int", is_pk=True),
            ColumnDef("sensor_uuid", "char(36)"),
            ColumnDef("old_statut", "varchar"),
            ColumnDef("new_statut", "varchar"),
            ColumnDef("event", "varchar"),
            ColumnDef("created_at", "timestamp"),
        ]))

        self._register_table(TableDef("interventions_history", [
            ColumnDef("id", "int", is_pk=True),
            ColumnDef("intervention_id", "int", is_fk=True, fk_table="intervention", fk_column="IDIn"),
            ColumnDef("old_statut", "varchar"),
            ColumnDef("new_statut", "varchar"),
            ColumnDef("actor_id", "int"),
            ColumnDef("actor_role", "varchar"),
            ColumnDef("timestamp", "datetime"),
        ]))

        self._register_table(TableDef("vehicles_history", [
            ColumnDef("id", "int", is_pk=True),
            ColumnDef("vehicle_plaque", "varchar"),
            ColumnDef("old_statut", "varchar"),
            ColumnDef("new_statut", "varchar"),
            ColumnDef("latitude", "decimal"),
            ColumnDef("longitude", "decimal"),
            ColumnDef("created_at", "timestamp"),
        ]))

        self._register_table(TableDef("logs_automata", [
            ColumnDef("id", "int", is_pk=True),
            ColumnDef("automata_type", "varchar"),
            ColumnDef("entity_id", "varchar"),
            ColumnDef("entity_type", "varchar"),
            ColumnDef("old_state", "varchar"),
            ColumnDef("new_state", "varchar"),
            ColumnDef("timestamp", "datetime"),
            ColumnDef("user_id", "int"),
            ColumnDef("trigger_reason", "varchar"),
        ]))

        self._register_table(TableDef("rapports_ia", [
            ColumnDef("id", "int", is_pk=True),
            ColumnDef("intervention_id", "int", is_fk=True, fk_table="intervention", fk_column="IDIn"),
            ColumnDef("diagnostic", "text"),
            ColumnDef("solution_principale", "varchar"),
            ColumnDef("solution_2", "varchar"),
            ColumnDef("solution_3", "varchar"),
            ColumnDef("confiance", "int"),
            ColumnDef("duree_estimee_heures", "decimal"),
            ColumnDef("cout_estime", "decimal"),
            ColumnDef("llm_provider", "varchar"),
            ColumnDef("model_used", "varchar"),
            ColumnDef("timestamp", "datetime"),
        ]))

    def _register_table(self, table: TableDef):
        self.tables[table.name] = table

    # ── Relationship Graph ─────────────────────────────────────

    def _build_graph(self):
        """Construire le graphe d'adjacence à partir des FK"""
        self._adjacency = {t: {} for t in self.tables}

        for tname, tdef in self.tables.items():
            for col in tdef.fks:
                if col.fk_table and col.fk_table in self.tables:
                    target = col.fk_table
                    target_col = col.fk_column
                    # Edge: tname --(col.name = target.target_col)--> target
                    self._adjacency[tname][target] = (col.name, target_col)
                    # Reverse edge
                    self._adjacency[target][tname] = (target_col, col.name)

    def find_join_path(self, tables: List[str]) -> List[Tuple[str, str, str, str]]:
        """
        Trouver le chemin de jointure entre plusieurs tables via BFS.

        Retourne: [(table_from, table_to, col_from, col_to), ...]
        """
        if len(tables) <= 1:
            return []

        # Normalize table names
        resolved = [self.resolve_table_name(t) or t for t in tables]
        resolved = list(dict.fromkeys(resolved))  # dedupe preserving order

        if len(resolved) <= 1:
            return []

        joins = []
        visited = {resolved[0]}

        for target in resolved[1:]:
            if target in visited:
                continue
            path = self._bfs_path(visited, target)
            if path:
                for (t_from, t_to, c_from, c_to) in path:
                    joins.append((t_from, t_to, c_from, c_to))
                    visited.add(t_to)
            else:
                # No FK path found — skip
                pass

        return joins

    def _bfs_path(self, sources: Set[str], target: str) -> List[Tuple[str, str, str, str]]:
        """BFS du graphe FK pour trouver le plus court chemin"""
        queue = deque()
        visited_bfs = set()

        for s in sources:
            queue.append((s, []))
            visited_bfs.add(s)

        while queue:
            current, path = queue.popleft()
            if current == target:
                return path

            for neighbor, (col_from, col_to) in self._adjacency.get(current, {}).items():
                if neighbor not in visited_bfs:
                    visited_bfs.add(neighbor)
                    new_path = path + [(current, neighbor, col_from, col_to)]
                    queue.append((neighbor, new_path))

        return []

    # ── French Synonyms ────────────────────────────────────────

    def _build_synonyms(self):
        """Construire les dictionnaires de synonymes français"""

        # ── Mots → Tables ──
        self._word_to_tables = {
            # capteur
            "capteur": ["capteur"], "capteurs": ["capteur"], "sensor": ["capteur"],
            "sensors": ["capteur"], "sonde": ["capteur"], "sondes": ["capteur"],
            "détecteur": ["capteur"], "détecteurs": ["capteur"],
            # mesures
            "mesure": ["mesures1"], "mesures": ["mesures1"], "mesures1": ["mesures1"],
            "mesures2": ["mesures2"], "measurement": ["mesures1"],
            "relevé": ["mesures1"], "relevés": ["mesures1"],
            "grandeur": ["mesures2"], "grandeurs": ["mesures2"],
            "unité": ["mesures2"], "unités": ["mesures2"],
            # zone (implicitement mesures1 car les "zones" = capteurs avec mesures)
            "zone": ["mesures1"], "zones": ["mesures1"],
            # intervention
            "intervention": ["intervention"], "interventions": ["intervention"],
            "maintenance": ["intervention"], "réparation": ["intervention"],
            "réparations": ["intervention"],
            # citoyen
            "citoyen": ["citoyen"], "citoyens": ["citoyen"],
            "habitant": ["citoyen"], "habitants": ["citoyen"],
            "personne": ["citoyen"], "personnes": ["citoyen"],
            "utilisateur": ["citoyen"], "utilisateurs": ["citoyen"],
            # consultation
            "consultation": ["consultation"], "consultations": ["consultation"],
            "sondage": ["consultation"], "sondages": ["consultation"],
            # participation
            "participation": ["participation"], "participations": ["participation"],
            # technicien
            "technicien": ["technicien"], "techniciens": ["technicien"],
            "tech": ["technicien"], "techs": ["technicien"],
            "ingénieur": ["technicien"], "ingénieurs": ["technicien"],
            # propriétaire
            "propriétaire": ["propriétaire"], "propriétaires": ["propriétaire"],
            "proprietaire": ["propriétaire"], "proprietaires": ["propriétaire"],
            "owner": ["propriétaire"], "proprio": ["propriétaire"],
            # véhicule
            "véhicule": ["véhicule"], "véhicules": ["véhicule"],
            "vehicule": ["véhicule"], "vehicules": ["véhicule"],
            "voiture": ["véhicule"], "voitures": ["véhicule"],
            "bus": ["véhicule"], "camion": ["véhicule"], "camions": ["véhicule"],
            # trajet
            "trajet": ["trajet"], "trajets": ["trajet"],
            "itinéraire": ["trajet"], "itinéraires": ["trajet"],
            "parcours": ["trajet"], "route": ["trajet"], "routes": ["trajet"],
            # supervision
            "supervision": ["supervision"], "supervisions": ["supervision"],
            "superviseur": ["supervision"], "superviseurs": ["supervision"],
            # history tables
            "historique": ["capteurs_history"],
            "history": ["capteurs_history"],
            "historique_capteurs": ["capteurs_history"],
            "événement": ["capteurs_history"], "événements": ["capteurs_history"],
            "evenement": ["capteurs_history"], "evenements": ["capteurs_history"],
            "historique_interventions": ["interventions_history"],
            "historique_véhicules": ["vehicles_history"],
            "historique_vehicules": ["vehicles_history"],
            # logs
            "log": ["logs_automata"], "logs": ["logs_automata"],
            "journal": ["logs_automata"], "journaux": ["logs_automata"],
            "audit": ["logs_automata"],
            # rapports IA
            "rapport": ["rapports_ia"], "rapports": ["rapports_ia"],
            "rapport_ia": ["rapports_ia"], "rapports_ia": ["rapports_ia"],
            "diagnostique": ["rapports_ia"], "diagnostic": ["rapports_ia"],
        }

        # ── Mots → Colonnes (table, column) ──
        self._word_to_columns = {
            # Identifiants
            "uuid": [("capteur", "UUID"), ("mesures1", "UUID"), ("intervention", "UUID")],
            "id": [("capteur", "UUID")],
            "idm": [("mesures1", "IDM")],
            "idin": [("intervention", "IDIn")],
            "idci": [("citoyen", "IDCI")],
            "idco": [("consultation", "IDCO")],
            "idpa": [("participation", "IDPA")],
            "idt": [("technicien", "IDT")],
            "idp": [("propriétaire", "IDP")],
            "idtr": [("trajet", "IDTR")],
            "plaque": [("véhicule", "Plaque"), ("trajet", "Plaque")],

            # Noms / textes
            "nom": [("citoyen", "Nom"), ("technicien", "Nom"), ("propriétaire", "Nom")],
            "name": [("citoyen", "Nom"), ("technicien", "Nom"), ("propriétaire", "Nom")],
            "adresse": [("citoyen", "Adresse"), ("propriétaire", "Adresse")],
            "téléphone": [("citoyen", "Téléphone"), ("propriétaire", "Téléphone")],
            "telephone": [("citoyen", "Téléphone"), ("propriétaire", "Téléphone")],
            "email": [("citoyen", "Email"), ("propriétaire", "Email")],
            "mail": [("citoyen", "Email"), ("propriétaire", "Email")],

            # Score / préférences
            "score": [("citoyen", "Score")],
            "score_écologique": [("citoyen", "Score")],
            "score_ecologique": [("citoyen", "Score")],
            "écologique": [("citoyen", "Score")],
            "ecologique": [("citoyen", "Score")],
            "préférences": [("citoyen", "Préférences")],
            "preferences": [("citoyen", "Préférences")],
            "préférence": [("citoyen", "Préférences")],

            # Capteur specific
            "type": [("capteur", "Type"), ("véhicule", "Type")],
            "type_capteur": [("capteur", "Type")],
            "latitude": [("capteur", "Latitude"), ("véhicule", "Latitude")],
            "longitude": [("capteur", "Longitude"), ("véhicule", "Longitude")],
            "statut": [("capteur", "Statut"), ("intervention", "statut"), ("véhicule", "Statut")],
            "status": [("capteur", "Statut"), ("intervention", "statut"), ("véhicule", "Statut")],
            "état": [("capteur", "Statut"), ("intervention", "statut"), ("véhicule", "Statut")],
            "date_installation": [("capteur", "Date Installation")],
            "installation": [("capteur", "Date Installation")],

            # Mesures
            "valeur": [("mesures1", "Valeur")],
            "value": [("mesures1", "Valeur")],
            "grandeur": [("mesures1", "NomGrandeur")],
            "nom_grandeur": [("mesures1", "NomGrandeur")],
            "nomgrandeur": [("mesures1", "NomGrandeur")],
            "unité": [("mesures2", "Unité")],
            "unite": [("mesures2", "Unité")],

            # Intervention
            "dateheure": [("intervention", "DateHeure")],
            "date_heure": [("intervention", "DateHeure")],
            "nature": [("intervention", "Nature")],
            "durée": [("intervention", "Durée"), ("trajet", "Durée")],
            "duree": [("intervention", "Durée"), ("trajet", "Durée")],
            "coût": [("intervention", "Coût")],
            "cout": [("intervention", "Coût")],
            "cost": [("intervention", "Coût")],
            "prix": [("intervention", "Coût")],
            "impactco2": [("intervention", "ImpactCO2")],
            "impact_co2": [("intervention", "ImpactCO2")],
            "co2": [("intervention", "ImpactCO2"), ("trajet", "ÉconomieCO2")],
            "rapport_tech1": [("intervention", "rapport_tech1")],
            "rapport_tech2": [("intervention", "rapport_tech2")],

            # Trajet
            "origine": [("trajet", "Origine")],
            "destination": [("trajet", "Destination")],
            "économie_co2": [("trajet", "ÉconomieCO2")],
            "economie_co2": [("trajet", "ÉconomieCO2")],
            "économieco2": [("trajet", "ÉconomieCO2")],
            "économique": [("trajet", "ÉconomieCO2")],
            "economique": [("trajet", "ÉconomieCO2")],
            "économie": [("trajet", "ÉconomieCO2")],
            "economie": [("trajet", "ÉconomieCO2")],

            # Véhicule
            "énergie": [("véhicule", "Énergie Utilisée")],
            "energie": [("véhicule", "Énergie Utilisée")],
            "énergie_utilisée": [("véhicule", "Énergie Utilisée")],

            # Consultation
            "sujet": [("consultation", "Sujet")],
            "mode": [("consultation", "Mode")],

            # Participation
            "heure": [("participation", "Heure")],

            # Supervision
            "rôle": [("supervision", "Rôle")],
            "role": [("supervision", "Rôle")],

            # Propriétaire
            "propriété": [("propriétaire", "Propriété")],
            "propriete": [("propriétaire", "Propriété")],

            # Technicien
            "numero": [("technicien", "Numero")],
            "numéro": [("technicien", "Numero")],

            # History
            "event": [("capteurs_history", "event")],
            "événement": [("capteurs_history", "event")],
            "evenement": [("capteurs_history", "event")],
            "old_statut": [("capteurs_history", "old_statut"), ("interventions_history", "old_statut")],
            "new_statut": [("capteurs_history", "new_statut"), ("interventions_history", "new_statut")],
            "ancien_statut": [("capteurs_history", "old_statut")],
            "nouveau_statut": [("capteurs_history", "new_statut")],

            # Rapports IA
            "confiance": [("rapports_ia", "confiance")],
            "solution": [("rapports_ia", "solution_principale")],
            "diagnostique": [("rapports_ia", "diagnostic")],
            "llm": [("rapports_ia", "llm_provider")],
            "modèle": [("rapports_ia", "model_used")],
            "model": [("rapports_ia", "model_used")],

            # Logs automata
            "automata_type": [("logs_automata", "automata_type")],
            "entity_id": [("logs_automata", "entity_id")],
            "entity_type": [("logs_automata", "entity_type")],
            "old_state": [("logs_automata", "old_state")],
            "new_state": [("logs_automata", "new_state")],
            "trigger_reason": [("logs_automata", "trigger_reason")],

            # Date (ambigu)
            "date": [("participation", "Date"), ("trajet", "Date")],
        }

        # ── NomGrandeur values → normalized ──
        self._grandeur_synonyms = {
            "no2": "NO2", "co2_air": "CO2", "co2": "CO2",
            "pm10": "PM10", "pm2.5": "PM2.5", "pm25": "PM2.5",
            "luminosité": "Luminosité", "luminosite": "Luminosité",
            "température": "Température", "temperature": "Température",
            "humidité": "Humidité", "humidite": "Humidité",
            "bruit": "Bruit", "son": "Bruit", "noise": "Bruit",
            "pression": "Pression",
            "vent": "Vent", "vitesse_vent": "Vent",
            "ozone": "Ozone", "o3": "Ozone",
            "so2": "SO2",
            "courant": "Courant", "tension": "Tension",
            "puissance": "Puissance", "énergie_kwh": "Énergie",
            "poids": "Poids", "taux_remplissage": "Taux de remplissage",
            "densité_trafic": "Densité trafic", "vitesse": "Vitesse",
        }

        # ── Type de capteur ──
        self._type_capteur_synonyms = {
            "éclairage": "Éclairage", "eclairage": "Éclairage",
            "lumière": "Éclairage", "lampadaire": "Éclairage",
            "déchets": "Déchets", "dechets": "Déchets",
            "poubelle": "Déchets", "ordure": "Déchets", "ordures": "Déchets",
            "trafic": "Trafic", "circulation": "Trafic", "traffic": "Trafic",
            "énergie": "Énergie", "energie": "Énergie",
            "électricité": "Énergie", "electricite": "Énergie",
            "qualité_air": "Qualité de l'air", "qualite_air": "Qualité de l'air",
            "air": "Qualité de l'air", "pollution": "Qualité de l'air",
        }

        # ── Nature intervention ──
        self._nature_intervention_synonyms = {
            "prédictive": "Prédictive", "predictive": "Prédictive",
            "prédictives": "Prédictive", "predictives": "Prédictive",
            "corrective": "Corrective", "correctives": "Corrective",
            "curative": "Curative", "curatives": "Curative",
        }

        # ── Statut (toutes tables) ──
        self._status_synonyms = {
            # Capteur
            "actif": "Actif", "actifs": "Actif", "active": "Actif", "actives": "Actif",
            "en_maintenance": "En Maintenance", "maintenance": "En Maintenance",
            "hors_service": "Hors Service", "hs": "Hors Service",
            "panne": "Hors Service",
            "signalé": "Signalé", "signale": "Signalé",
            # Véhicule
            "stationné": "Stationné", "stationne": "Stationné",
            "garé": "Stationné", "gare": "Stationné", "parqué": "Stationné",
            "en_route": "En Route", "roulant": "En Route",
            "arrivé": "Arrivé", "arrive": "Arrivé",
            "en_panne": "En Panne",
            # Intervention
            "demande": "Demande",
            "tech1_assigné": "Tech1_Assigné", "tech1_assigne": "Tech1_Assigné",
            "assigné": "Tech1_Assigné", "assigne": "Tech1_Assigné",
            "tech2_valide": "Tech2_Valide", "validé": "Tech2_Valide",
            "ia_valide": "IA_Valide",
            "terminée": "Terminée", "terminee": "Terminée",
            "fini": "Terminée", "finie": "Terminée",
            "complété": "Terminée", "complete": "Terminée",
            # Consultation
            "en_ligne": "En ligne", "en ligne": "En ligne",
            "présentiel": "Présentiel", "presentiel": "Présentiel",
            "mixte": "Mixte",
        }

    # ── Public API ─────────────────────────────────────────────

    def resolve_table_name(self, word: str) -> Optional[str]:
        """Résoudre un mot en nom de table"""
        w = word.lower().strip()
        if w in self.tables:
            return w
        hits = self._word_to_tables.get(w, [])
        return hits[0] if hits else None

    def resolve_tables_from_words(self, words: List[str]) -> List[str]:
        """Extraire toutes les tables mentionnées par une liste de mots"""
        tables = []
        for w in words:
            t = self.resolve_table_name(w)
            if t and t not in tables:
                tables.append(t)
        return tables

    def resolve_column(self, word: str, table_context: str = "") -> Optional[Tuple[str, str]]:
        """
        Résoudre un mot en (table, colonne).
        Si table_context est fourni, priorise cette table.
        """
        w = word.lower().strip()
        hits = self._word_to_columns.get(w, [])

        if not hits:
            # Try direct match against table columns
            if table_context and table_context in self.tables:
                tdef = self.tables[table_context]
                col = tdef.get_column(word)
                if col:
                    return (table_context, col.name)
            return None

        if table_context:
            for (t, c) in hits:
                if t == table_context:
                    return (t, c)

        return hits[0]

    def resolve_column_for_tables(self, word: str, tables: List[str]) -> Optional[Tuple[str, str]]:
        """Résoudre une colonne en priorisant les tables données"""
        w = word.lower().strip()
        hits = self._word_to_columns.get(w, [])

        for (t, c) in hits:
            if t in tables:
                return (t, c)

        if hits:
            return hits[0]

        # Direct column match
        for tname in tables:
            if tname in self.tables:
                col = self.tables[tname].get_column(word)
                if col:
                    return (tname, col.name)
        return None

    def resolve_grandeur(self, word: str) -> Optional[str]:
        """Résoudre un nom de grandeur (NO2, CO2, Luminosité, etc.)"""
        w = word.lower().strip()
        return self._grandeur_synonyms.get(w)

    def resolve_type_capteur(self, word: str) -> Optional[str]:
        """Résoudre un type de capteur"""
        w = word.lower().strip()
        return self._type_capteur_synonyms.get(w)

    def resolve_nature_intervention(self, word: str) -> Optional[str]:
        """Résoudre une nature d'intervention"""
        w = word.lower().strip()
        return self._nature_intervention_synonyms.get(w)

    def resolve_status(self, word: str) -> Optional[str]:
        """Résoudre un statut"""
        w = word.lower().strip()
        return self._status_synonyms.get(w)

    def get_column_sql_name(self, table: str, col_name: str) -> str:
        """Obtenir le nom SQL de la colonne (avec backticks si nécessaire)"""
        if table in self.tables:
            cdef = self.tables[table].get_column(col_name)
            if cdef:
                return cdef.sql_name
        # Fallback
        if " " in col_name:
            return f"`{col_name}`"
        return col_name

    def get_table_columns(self, table: str) -> List[str]:
        """Obtenir la liste des colonnes d'une table"""
        if table in self.tables:
            return self.tables[table].column_names()
        return []

    def table_exists(self, name: str) -> bool:
        return name in self.tables

    def column_exists(self, table: str, col: str) -> bool:
        if table in self.tables:
            return self.tables[table].has_column(col)
        return False

    def get_all_table_names(self) -> List[str]:
        return list(self.tables.keys())

    def get_tables_for_word(self, word: str) -> List[str]:
        """Returns tables associated with a French word"""
        return self._word_to_tables.get(word.lower(), [])
