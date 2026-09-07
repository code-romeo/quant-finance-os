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
        self._register_table(path)
        return path

    def query(self, sql: str) -> pl.DataFrame:
        if not sql.lstrip().lower().startswith("select"):
            raise ValueError("Only read-only SELECT queries are allowed")

        for parquet_file in self.root.glob("*.parquet"):
            self._register_table(parquet_file)
        return self._conn.execute(sql).pl()

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

    def __del__(self) -> None:
        try:
            self._conn.close()
        except Exception:
            pass
