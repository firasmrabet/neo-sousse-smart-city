"""
Code Generator — Transformation AST → SQL
Version universelle: utilise SchemaRegistry pour résolution dynamique.

Mapping vers le schéma réel de la BD sousse_smart_city_projet_module.
Supporte les 17 tables, jointures automatiques, colonnes avec backticks.
"""

from typing import List, Optional
from .parser import (
    ASTNode, SelectQuery, CountQuery, AggregateQuery,
    ColumnRef, Condition, JoinClause, OrderBy, GroupByClause,
)
from .schema_registry import SchemaRegistry


class CodeGenerator:
    """
    Générateur de code SQL à partir de l'AST.
    Utilise SchemaRegistry pour résolution dynamique des noms.
    """

    FUNCTION_MAP = {
        "nombre": "COUNT", "count": "COUNT",
        "moyenne": "AVG", "avg": "AVG",
        "total": "SUM", "somme": "SUM", "sum": "SUM",
        "min": "MIN", "minimum": "MIN",
        "max": "MAX", "maximum": "MAX",
    }

    def __init__(self):
        self.schema = SchemaRegistry.get_instance()

    def generate(self, ast: ASTNode) -> str:
        """Generate SQL from AST node"""
        if isinstance(ast, SelectQuery):
            return self._gen_select(ast)
        elif isinstance(ast, CountQuery):
            return self._gen_count(ast)
        elif isinstance(ast, AggregateQuery):
            return self._gen_aggregate(ast)
        else:
            raise ValueError(f"Type de nœud AST inconnu: {type(ast).__name__}")

    # ── Helper: resolve column to SQL name ─────────────────────

    def _col_sql(self, col_name: str, table: str = "", with_table_prefix: bool = False) -> str:
        """Resolve a column name to its SQL representation"""
        # Try schema-based resolution
        resolved = self.schema.resolve_column(col_name, table)
        if resolved:
            t, c = resolved
            sql_name = self.schema.get_column_sql_name(t, c)
            if with_table_prefix and t:
                return f"{t}.{sql_name}"
            return sql_name

        # Direct column in table
        if table and self.schema.column_exists(table, col_name):
            return self.schema.get_column_sql_name(table, col_name)

        # Fallback: return as-is, with backticks if spaces
        if " " in col_name:
            return f"`{col_name}`"
        return col_name

    def _resolve_function(self, name: str) -> str:
        return self.FUNCTION_MAP.get(name.lower(), name.upper())

    def _resolve_status(self, val: str) -> str:
        resolved = self.schema.resolve_status(val)
        return resolved if resolved else val

    def _needs_table_prefix(self, ast) -> bool:
        """Check if we need table prefixes (multi-table query)"""
        has_joins = hasattr(ast, 'joins') and ast.joins
        return has_joins

    def _get_all_tables(self, ast) -> List[str]:
        """Get all tables involved in a query"""
        tables = [ast.table]
        if hasattr(ast, 'joins'):
            for j in ast.joins:
                if j.table not in tables:
                    tables.append(j.table)
        return tables

    # ── SELECT ────────────────────────────────────────────────────

    def _gen_select(self, q: SelectQuery) -> str:
        parts = []
        use_prefix = self._needs_table_prefix(q)
        all_tables = self._get_all_tables(q)

        # SELECT clause
        if q.group_by:
            # GROUP BY query: select group column + aggregate
            cols_sql = []
            for c in q.columns:
                if c.function:
                    func = self._resolve_function(c.function)
                    col = self._col_sql(c.name, c.table or q.table, use_prefix)
                    alias = c.alias or "total"
                    cols_sql.append(f"{func}({col}) AS {alias}")
                else:
                    col = self._col_sql(c.name, c.table or q.table, use_prefix)
                    cols_sql.append(col)
            parts.append(f"SELECT {', '.join(cols_sql)}")
        elif q.columns and q.columns[0].name != "*":
            cols = []
            for c in q.columns:
                col = self._col_sql(c.name, c.table or q.table, use_prefix)
                if c.function:
                    func = self._resolve_function(c.function)
                    cols.append(f"{func}({col})")
                else:
                    cols.append(col)
            parts.append(f"SELECT {', '.join(cols)}")
        else:
            parts.append("SELECT *")

        # FROM
        parts.append(f"FROM {q.table}")

        # JOINS
        if q.joins:
            parts.append(self._gen_joins(q.joins))

        # WHERE
        where = self._gen_conditions(q.conditions, q.table, all_tables)
        if where:
            parts.append(f"WHERE {where}")

        # GROUP BY
        if q.group_by:
            gb_parts = []
            for gb in q.group_by:
                col = self._col_sql(gb.column, gb.table or q.table, use_prefix)
                gb_parts.append(col)
            parts.append(f"GROUP BY {', '.join(gb_parts)}")

        # ORDER BY
        if q.order_by:
            ob_parts = []
            for o in q.order_by:
                col = self._col_sql(o.column, o.table or q.table, use_prefix)
                ob_parts.append(f"{col} {o.direction}")
            parts.append(f"ORDER BY {', '.join(ob_parts)}")

        # LIMIT
        if q.limit:
            parts.append(f"LIMIT {q.limit}")

        return " ".join(parts)

    # ── COUNT ─────────────────────────────────────────────────────

    def _gen_count(self, q: CountQuery) -> str:
        use_prefix = self._needs_table_prefix(q)
        all_tables = self._get_all_tables(q)

        if q.group_by:
            # COUNT with GROUP BY
            gb_parts = []
            for gb in q.group_by:
                col = self._col_sql(gb.column, gb.table or q.table, use_prefix)
                gb_parts.append(col)

            sql = f"SELECT {', '.join(gb_parts)}, COUNT(*) AS total FROM {q.table}"
        else:
            sql = f"SELECT COUNT(*) AS total FROM {q.table}"

        if q.joins:
            sql += f" {self._gen_joins(q.joins)}"

        where = self._gen_conditions(q.conditions, q.table, all_tables)
        if where:
            sql += f" WHERE {where}"

        if q.group_by:
            gb_sql = []
            for gb in q.group_by:
                col = self._col_sql(gb.column, gb.table or q.table, use_prefix)
                gb_sql.append(col)
            sql += f" GROUP BY {', '.join(gb_sql)}"

        return sql

    # ── AGGREGATE ─────────────────────────────────────────────────

    def _gen_aggregate(self, q: AggregateQuery) -> str:
        func = self._resolve_function(q.function)
        use_prefix = self._needs_table_prefix(q)
        all_tables = self._get_all_tables(q)
        col = self._col_sql(q.column, q.column_table or q.table, use_prefix)

        if q.group_by:
            gb_parts = []
            for gb in q.group_by:
                gb_col = self._col_sql(gb.column, gb.table or q.table, use_prefix)
                gb_parts.append(gb_col)
            sql = f"SELECT {', '.join(gb_parts)}, {func}({col}) AS result FROM {q.table}"
        else:
            sql = f"SELECT {func}({col}) AS result FROM {q.table}"

        if q.joins:
            sql += f" {self._gen_joins(q.joins)}"

        where = self._gen_conditions(q.conditions, q.table, all_tables)
        if where:
            sql += f" WHERE {where}"

        if q.group_by:
            gb_sql = []
            for gb in q.group_by:
                gb_col = self._col_sql(gb.column, gb.table or q.table, use_prefix)
                gb_sql.append(gb_col)
            sql += f" GROUP BY {', '.join(gb_sql)}"

        if q.order_by:
            ob_col = self._col_sql(q.order_by.column, q.order_by.table or q.table, use_prefix)
            sql += f" ORDER BY {ob_col} {q.order_by.direction}"

        if q.limit:
            sql += f" LIMIT {q.limit}"

        return sql

    # ── JOINS ─────────────────────────────────────────────────────

    def _gen_joins(self, joins: List[JoinClause]) -> str:
        if not joins:
            return ""

        parts = []
        for j in joins:
            from_table = j.from_table
            to_table = j.table
            from_col = self.schema.get_column_sql_name(from_table, j.from_col)
            to_col = self.schema.get_column_sql_name(to_table, j.to_col)
            parts.append(
                f"INNER JOIN {to_table} ON {from_table}.{from_col} = {to_table}.{to_col}"
            )

        return " ".join(parts)

    # ── Conditions ────────────────────────────────────────────────

    def _gen_conditions(self, conditions: List[Condition], main_table: str,
                        all_tables: List[str] = None) -> str:
        if not conditions:
            return ""

        use_prefix = len(all_tables or []) > 1

        # Separate Nature conditions (may need OR grouping) from other conditions
        nature_conditions = []
        other_conditions = []
        for c in conditions:
            if c.left == "Nature" and c.left_table == "intervention":
                nature_conditions.append(c)
            else:
                other_conditions.append(c)

        parts = []

        # Generate non-nature conditions
        for c in other_conditions:
            parts.append(self._render_single_condition(c, main_table, use_prefix))

        # Generate nature conditions (OR-grouped if multiple)
        if nature_conditions:
            nat_parts = []
            for c in nature_conditions:
                nat_parts.append(self._render_single_condition(c, main_table, use_prefix))
            if len(nat_parts) > 1:
                parts.append(f"({' OR '.join(nat_parts)})")
            else:
                parts.append(nat_parts[0])

        return " AND ".join(parts)

    def _render_single_condition(self, c: Condition, main_table: str,
                                  use_prefix: bool) -> str:
        """Render a single condition to SQL string"""
        # Resolve left side (column)
        left_table = c.left_table or main_table
        col_name = c.left

        # Try to resolve via schema
        if left_table and self.schema.column_exists(left_table, col_name):
            sql_col = self.schema.get_column_sql_name(left_table, col_name)
        else:
            # Try resolving via synonym
            resolved = self.schema.resolve_column(col_name, left_table)
            if resolved:
                left_table, col_name = resolved
                sql_col = self.schema.get_column_sql_name(left_table, col_name)
            else:
                sql_col = col_name if " " not in col_name else f"`{col_name}`"

        if use_prefix and left_table:
            left_sql = f"{left_table}.{sql_col}"
        else:
            left_sql = sql_col

        # Operator
        op = c.operator
        if op == "<>":
            op = "!="

        # Right side (value)
        right = c.right

        # Try to resolve as status (only for Statut/statut columns)
        if col_name.lower() in ("statut", "status"):
            resolved_status = self._resolve_status(right)
            if resolved_status != right:
                right = resolved_status

        # Quote strings, leave numbers bare
        if c.right_is_number:
            val = right
        else:
            try:
                float(right)
                val = right
            except ValueError:
                val = f"'{right}'"

        return f"{left_sql} {op} {val}"

