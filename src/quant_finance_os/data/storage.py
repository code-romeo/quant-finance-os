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
        self._registered_tables.discard(name)
        self._register_table(path)
        return path

    def query(self, sql: str) -> pl.DataFrame:
        statements = duckdb.extract_statements(sql)
        if len(statements) != 1 or statements[0].type != duckdb.StatementType.SELECT:
            raise ValueError("Only read-only SELECT queries are allowed")
        forbidden_tokens = (
            "read_csv",
            "read_json",
            "read_parquet(",
            "read_text",
            "httpfs",
            "postgres_scan",
            "mysql_scan",
            "sqlite_scan",
            "attach",
            "pragma",
            "copy ",
            "call ",
            "install ",
            "load ",
        )
        lowered_query = statements[0].query.lower()
        if any(token in lowered_query for token in forbidden_tokens):
            raise ValueError("Query source must be registered local tables only")

        for parquet_file in self.root.glob("*.parquet"):
            self._register_table(parquet_file)
        return self._conn.execute(statements[0].query).pl()

    def _register_table(self, parquet_file: Path) -> None:
        table_name = parquet_file.stem
        if table_name in self._registered_tables:
            return
        quoted_table = table_name.replace('"', '""')
        quoted_path = str(parquet_file).replace("'", "''")
        self._conn.execute(
            f"CREATE OR REPLACE VIEW \"{quoted_table}\" AS SELECT * FROM read_parquet('{quoted_path}')"
        )
        self._registered_tables.add(table_name)

    def close(self) -> None:
        self._conn.close()

    def __enter__(self) -> "LocalParquetStore":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()
