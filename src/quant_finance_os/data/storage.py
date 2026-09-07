from __future__ import annotations

from pathlib import Path

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
            plan = self._conn.execute(f"EXPLAIN {query}").fetchall()[0][1].upper()
        except duckdb.Error as exc:  # pragma: no cover - defensive fallback
            raise ValueError("Invalid SELECT query for LocalParquetStore") from exc

        if any(token in plan for token in ("READ_PARQUET", "READ_CSV", "READ_JSON", "READ_TEXT")):
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
            f"CREATE OR REPLACE TABLE \"{quoted_table}\" AS SELECT * FROM read_parquet('{quoted_path}')"
        )
        self._registered_tables.add(table_name_key)

    def close(self) -> None:
        self._conn.close()

    def __enter__(self) -> "LocalParquetStore":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()
