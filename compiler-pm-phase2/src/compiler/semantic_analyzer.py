"""
Semantic Analyzer — Analyse sémantique post-parsing
Version universelle: utilise SchemaRegistry pour validation.

Pipeline: AST → Validation sémantique → Avertissements + Suggestions
"""

from typing import List, Optional
from .parser import ASTNode, SelectQuery, CountQuery, AggregateQuery, Condition
from .schema_registry import SchemaRegistry


class SemanticWarning:
    """Un avertissement sémantique (pas bloquant)"""
    def __init__(self, level: str, message: str, suggestion: str = ""):
        self.level = level        # "info", "warning", "error"
        self.message = message
        self.suggestion = suggestion

    def __repr__(self):
        return f"[{self.level.upper()}] {self.message}" + (f" → {self.suggestion}" if self.suggestion else "")


class SemanticAnalyzer:
    """
    Analyseur sémantique universel pour le compilateur NL→SQL.

    Vérifie:
      1. Noms de tables valides (existent dans le schéma)
      2. Noms de colonnes valides pour la table ciblée
      3. Cohérence conditions (valeurs de statut, types)
      4. Suggestions de reformulation
    """

    def __init__(self):
        self.schema = SchemaRegistry.get_instance()

    def analyze(self, ast: ASTNode) -> List[SemanticWarning]:
        """Analyser l'AST et retourner la liste des avertissements"""
        warnings = []

        if isinstance(ast, SelectQuery):
            warnings.extend(self._check_query(ast))
        elif isinstance(ast, CountQuery):
            warnings.extend(self._check_query(ast))
        elif isinstance(ast, AggregateQuery):
            warnings.extend(self._check_query(ast))

        return warnings

    def _check_query(self, q) -> List[SemanticWarning]:
        warnings = []

        # Check main table
        main_table = q.table
        if not self.schema.table_exists(main_table):
            warnings.append(SemanticWarning(
                "error",
                f"Table '{main_table}' non reconnue dans le schéma.",
                f"Tables disponibles: {', '.join(sorted(self.schema.get_all_table_names()))}"
            ))

        # Check join tables
        if hasattr(q, 'joins'):
            for j in q.joins:
                if not self.schema.table_exists(j.table):
                    warnings.append(SemanticWarning(
                        "warning",
                        f"Table de jointure '{j.table}' non reconnue.",
                        f"Tables disponibles: {', '.join(sorted(self.schema.get_all_table_names()))}"
                    ))

        # Check conditions
        if hasattr(q, 'conditions'):
            for cond in q.conditions:
                col = cond.left
                table = cond.left_table or main_table

                if table and self.schema.table_exists(table):
                    if not self.schema.column_exists(table, col):
                        # Try resolution
                        resolved = self.schema.resolve_column(col, table)
                        if not resolved:
                            available = self.schema.get_table_columns(table)
                            warnings.append(SemanticWarning(
                                "info",
                                f"Colonne '{col}' non trouvée dans la table '{table}'.",
                                f"Colonnes disponibles: {', '.join(available[:10])}"
                            ))

                # Check status values
                if col.lower() in ("statut", "status"):
                    status_val = cond.right
                    clean_val = str(status_val).strip("'\"")

                    # 1) Check against actual enum_values from the schema column definition
                    is_valid_enum = False
                    if table and self.schema.table_exists(table):
                        col_def = self.schema.tables[table].get_column(col)
                        if col_def and col_def.enum_values:
                            if clean_val in col_def.enum_values:
                                is_valid_enum = True

                    # 2) Check if it's a known resolved synonym value
                    if not is_valid_enum:
                        is_valid_enum = clean_val in self.schema._status_synonyms.values()

                    # 3) Try to resolve via synonym lookup
                    if not is_valid_enum:
                        norm_val = clean_val.lower().replace(" ", "_")
                        resolved = self.schema.resolve_status(norm_val)
                        if resolved:
                            is_valid_enum = True

                    # 4) Also check all tables that have a Statut column
                    if not is_valid_enum:
                        for tname, tdef in self.schema.tables.items():
                            for cname, cdef in tdef.columns.items():
                                if cname.lower() in ("statut", "status") and cdef.enum_values:
                                    if clean_val in cdef.enum_values:
                                        is_valid_enum = True
                                        break
                            if is_valid_enum:
                                break

        # Check order by columns
        if hasattr(q, 'order_by') and q.order_by:
            order_list = q.order_by if isinstance(q.order_by, list) else [q.order_by]
            for ob in order_list:
                col = ob.column
                table = ob.table or main_table if hasattr(ob, 'table') else main_table
                if table and self.schema.table_exists(table):
                    if not self.schema.column_exists(table, col):
                        resolved = self.schema.resolve_column(col, table)
                        if not resolved:
                            warnings.append(SemanticWarning(
                                "info",
                                f"Colonne de tri '{col}' non trouvée dans '{table}'.",
                                "Le tri peut ne pas fonctionner comme attendu."
                            ))

        return warnings

    def get_suggestions(self, original_text: str) -> List[str]:
        """Suggérer des reformulations si la requête est ambiguë"""
        suggestions = []
        lower = original_text.lower()

        if "capteur" in lower and "mesure" in lower:
            suggestions.append(
                "Précisez: voulez-vous les capteurs ou les mesures ? "
                "Ex: 'Affiche les capteurs actifs' ou 'Affiche les mesures de NO2'"
            )

        if "score" in lower and "citoyen" not in lower:
            suggestions.append(
                "Précisez 'score des citoyens' pour éviter l'ambiguïté."
            )

        if "date" in lower and not any(t in lower for t in
            ("trajet", "mesure", "intervention", "capteur", "participation", "installation")):
            suggestions.append(
                "Précisez la table visée: 'date des trajets', 'date des mesures', "
                "'date de participation'."
            )

        if "co2" in lower and "trajet" not in lower and "intervention" not in lower:
            suggestions.append(
                "CO2 peut désigner ImpactCO2 (intervention) ou ÉconomieCO2 (trajet). "
                "Précisez: 'impact CO2 des interventions' ou 'économie CO2 des trajets'."
            )

        return suggestions
