from __future__ import annotations

import re
from pathlib import Path

import duckdb
import pyarrow as pa
import pyarrow.parquet as pq


class LocalParquetStore:
    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self._tables: dict[str, Path] = {}

    def write_table(self, name: str, rows: list[dict]) -> Path:
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name):
            raise ValueError("table name must start with letter/underscore and contain only alphanumerics/underscore")
        if not rows:
            raise ValueError("rows must be non-empty")

        path = self.root / f"{name}.parquet"
        pq.write_table(pa.Table.from_pylist(rows), path)
        self._tables[name] = path
        return path

    def read_table(self, name: str) -> list[dict]:
        path = self._tables.get(name)
        if path is None or not path.exists():
            raise ValueError(f"unknown table '{name}'")
        return pq.read_table(path).to_pylist()

    def query(self, sql: str) -> list[dict]:
        statement = sql.strip()
        if statement.endswith(";"):
            statement = statement[:-1].strip()
        lowered = statement.lower()

        if lowered.startswith("with "):
            raise ValueError("CTE queries are not allowed; use direct SELECT")
        if not lowered.startswith("select "):
            raise ValueError("Only SELECT queries are allowed")
        if ";" in statement:
            raise ValueError("Only a single SQL statement is allowed")
        if " join " in lowered:
            raise ValueError("JOIN queries are not allowed in LocalParquetStore.query")
        if re.search(r"\b(union|intersect|except|pragma|attach|copy|call)\b", lowered):
            raise ValueError("Unsupported SQL construct in LocalParquetStore.query")
        if re.search(r"\bread_(?:parquet|csv|json|json_auto|ndjson|text)\s*\(", lowered):
            raise ValueError("Direct file-reading functions are not allowed; query registered local tables only")

        match = re.match(r'^\s*select[\s\S]+?\sfrom\s+"?([A-Za-z_][A-Za-z0-9_]*)"?(\s|$)', statement, flags=re.IGNORECASE)
        if not match:
            raise ValueError("Query must select from a registered local table")
        table_name = match.group(1)
        if table_name not in self._tables:
            raise ValueError("Query references unknown table(s); only registered local tables are allowed")

        con = duckdb.connect(database=":memory:")
        try:
            for table_name, table_path in self._tables.items():
                safe_path = str(table_path).replace("'", "''")
                safe_identifier = table_name.replace('"', '""')
                con.execute(f'CREATE VIEW "{safe_identifier}" AS SELECT * FROM read_parquet(\'{safe_path}\')')

            result = con.execute(statement)
            rows = result.fetchall()
            cols = [d[0] for d in result.description]
            return [dict(zip(cols, row)) for row in rows]
        finally:
            con.close()
