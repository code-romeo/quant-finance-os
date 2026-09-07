from __future__ import annotations

from pathlib import Path
import re

import duckdb
import polars as pl


class LocalParquetStore:
    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self._conn = duckdb.connect()
        self._registered_tables: set[str] = set()

    def write_table(self, name: str, frame: pl.DataFrame) -> Path:
        path = self.root / f"{name}.parquet"
        frame.write_parquet(path)
        self._register_table(path, force=True)
        return path

    def query(self, sql: str) -> pl.DataFrame:
        statements = duckdb.extract_statements(sql)
        if len(statements) != 1 or statements[0].type != duckdb.StatementType.SELECT:
            raise ValueError("Only read-only SELECT queries are allowed")

        for parquet_file in self.root.glob("*.parquet"):
            self._register_table(parquet_file)
        query = statements[0].query

        try:
            table_refs = {name.split(".")[-1].strip('"').lower() for name in duckdb.get_table_names(query)}
        except duckdb.Error as exc:
            raise ValueError("Invalid SELECT query for LocalParquetStore") from exc

        cte_refs = _extract_leading_cte_names(query)
        table_refs = {table_name for table_name in table_refs if table_name not in cte_refs}
        has_from_or_join = re.search(r"\b(from|join)\b", query, flags=re.IGNORECASE) is not None
        if has_from_or_join and not table_refs:
            raise ValueError("Query source must be registered local tables only")
        if any(table_name not in self._registered_tables for table_name in table_refs):
            raise ValueError("Query source must be registered local tables only")

        return self._conn.execute(query).pl()

    def _register_table(self, parquet_file: Path, force: bool = False) -> None:
        table_name = parquet_file.stem
        table_name_key = table_name.lower()
        if table_name_key in self._registered_tables and not force:
            return
        quoted_table = table_name.replace('"', '""')
        quoted_path = str(parquet_file).replace("'", "''")
        self._conn.execute(
            f"CREATE OR REPLACE VIEW \"{quoted_table}\" AS SELECT * FROM read_parquet('{quoted_path}')"
        )
        self._registered_tables.add(table_name_key)

    def close(self) -> None:
        self._conn.close()

    def __enter__(self) -> "LocalParquetStore":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()


def _extract_leading_cte_names(query: str) -> set[str]:
    stripped = query.lstrip()
    if not stripped.lower().startswith("with"):
        return set()

    depth = 0
    main_select_idx = None
    for idx, char in enumerate(stripped):
        if char == "(":
            depth += 1
        elif char == ")":
            depth = max(0, depth - 1)
        elif depth == 0 and stripped[idx : idx + 6].lower() == "select":
            main_select_idx = idx
            break

    with_clause = stripped[:main_select_idx] if main_select_idx is not None else stripped
    return {
        ref.strip('"').lower()
        for ref in re.findall(
            r"(?:\bwith|,)\s+((?:\"[^\"]+\")|(?:[A-Za-z_][A-Za-z0-9_]*))\s+as\s*\(",
            with_clause,
            flags=re.IGNORECASE,
        )
    }
