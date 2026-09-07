from __future__ import annotations

import re
from pathlib import Path

import duckdb
import polars as pl


class LocalParquetStore:
    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self._conn = duckdb.connect()
        self._registered_tables: set[str] = set()
        self.refresh()

    def write_table(self, name: str, frame: pl.DataFrame) -> Path:
        path = self.root / f"{name}.parquet"
        frame.write_parquet(path)
        self._register_table(path, force=True)
        return path

    def query(self, sql: str) -> pl.DataFrame:
        try:
            statements = duckdb.extract_statements(sql)
        except duckdb.Error as exc:
            raise ValueError("Invalid SELECT query for LocalParquetStore") from exc
        if len(statements) != 1 or statements[0].type != duckdb.StatementType.SELECT:
            raise ValueError("Only read-only SELECT queries are allowed")

        normalized_query = statements[0].query
        if normalized_query.lstrip().lower().startswith("with"):
            raise ValueError("CTE queries are not supported; query registered tables directly")

        try:
            table_refs = {
                name.split(".")[-1].strip('"').lower()
                for name in duckdb.get_table_names(normalized_query)
            }
        except duckdb.Error as exc:
            raise ValueError("Invalid SELECT query for LocalParquetStore") from exc

        has_from_or_join = re.search(r"\b(from|join)\b", normalized_query, flags=re.IGNORECASE) is not None
        if has_from_or_join and not table_refs:
            raise ValueError("Query source must be registered local tables only")
        if any(table_name not in self._registered_tables for table_name in table_refs):
            raise ValueError("Query source must be registered local tables only")

        try:
            return self._conn.execute(normalized_query).pl()
        except duckdb.Error as exc:
            raise ValueError("Invalid SELECT query for LocalParquetStore") from exc

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

    def refresh(self) -> None:
        for parquet_file in self.root.glob("*.parquet"):
            self._register_table(parquet_file)

    def close(self) -> None:
        self._conn.close()

    def __enter__(self) -> "LocalParquetStore":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()
