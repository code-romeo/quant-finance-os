from __future__ import annotations

from pathlib import Path

import duckdb
import polars as pl


class LocalParquetStore:
    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def write_table(self, name: str, frame: pl.DataFrame) -> Path:
        path = self.root / f"{name}.parquet"
        frame.write_parquet(path)
        return path

    def query(self, sql: str) -> pl.DataFrame:
        with duckdb.connect() as conn:
            for parquet_file in self.root.glob("*.parquet"):
                table_name = parquet_file.stem.replace('"', '""')
                path = str(parquet_file).replace("'", "''")
                conn.execute(
                    f"CREATE OR REPLACE VIEW \"{table_name}\" AS SELECT * FROM read_parquet('{path}')"
                )
            relation = conn.execute(sql)
            columns = [col[0] for col in relation.description]
            return pl.DataFrame(relation.fetchall(), schema=columns, orient="row")
