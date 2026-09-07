import polars as pl

from quant_finance_os.data import LocalParquetStore


def test_local_parquet_store_registers_written_tables(tmp_path):
    store = LocalParquetStore(tmp_path)
    store.write_table("bars", pl.DataFrame({"symbol": ["AAPL"], "price": [101.0]}))

    out = store.query("SELECT symbol, price FROM bars")
    assert out.to_dict(as_series=False) == {"symbol": ["AAPL"], "price": [101.0]}


def test_local_parquet_store_blocks_non_select_query(tmp_path):
    store = LocalParquetStore(tmp_path)
    try:
        store.query("DELETE FROM bars")
    except ValueError as exc:
        assert "read-only SELECT" in str(exc)
    else:
        raise AssertionError("Expected ValueError for non-select query")


def test_local_parquet_store_blocks_multi_statement_query(tmp_path):
    store = LocalParquetStore(tmp_path)
    try:
        store.query("SELECT 1; DELETE FROM bars")
    except ValueError as exc:
        assert "read-only SELECT" in str(exc)
    else:
        raise AssertionError("Expected ValueError for multi-statement query")


def test_local_parquet_store_refreshes_existing_table_view(tmp_path):
    store = LocalParquetStore(tmp_path)
    store.write_table("bars", pl.DataFrame({"price": [1.0]}))
    assert store.query("SELECT price FROM bars").to_dict(as_series=False) == {"price": [1.0]}

    store.write_table("bars", pl.DataFrame({"price": [2.0]}))
    assert store.query("SELECT price FROM bars").to_dict(as_series=False) == {"price": [2.0]}
    assert store.query('SELECT price FROM "BARS"').to_dict(as_series=False) == {"price": [2.0]}


def test_local_parquet_store_blocks_external_read_functions(tmp_path):
    store = LocalParquetStore(tmp_path)
    external_path = tmp_path / "external.parquet"
    pl.DataFrame({"x": [1]}).write_parquet(external_path)
    try:
        store.query(f"SELECT * FROM read_parquet('{external_path}')")
    except ValueError as exc:
        assert "registered local tables" in str(exc)
    else:
        raise AssertionError("Expected ValueError for external table functions")


def test_local_parquet_store_rejects_cte_queries(tmp_path):
    store = LocalParquetStore(tmp_path)
    store.write_table("bars", pl.DataFrame({"price": [101.0, 102.0]}))
    try:
        store.query("WITH base AS (SELECT * FROM bars) SELECT avg(price) AS p FROM base")
    except ValueError as exc:
        assert "CTE queries are not supported" in str(exc)
    else:
        raise AssertionError("Expected ValueError for CTE query")


def test_local_parquet_store_blocks_commented_external_function(tmp_path):
    store = LocalParquetStore(tmp_path)
    external_path = tmp_path / "external_2.parquet"
    pl.DataFrame({"x": [1]}).write_parquet(external_path)
    try:
        store.query(f"SELECT * FROM read_/* bypass */parquet('{external_path}')")
    except ValueError as exc:
        assert "registered local tables" in str(exc) or "Invalid SELECT query" in str(exc)
    else:
        raise AssertionError("Expected ValueError for commented external table functions")


def test_local_parquet_store_allows_subquery_on_registered_table(tmp_path):
    store = LocalParquetStore(tmp_path)
    store.write_table("bars", pl.DataFrame({"price": [100.0, 101.0]}))
    out = store.query("SELECT avg(price) AS p FROM (SELECT price FROM bars) s")
    assert out["p"][0] == 100.5


def test_local_parquet_store_allows_subquery_without_table_sources(tmp_path):
    store = LocalParquetStore(tmp_path)
    out = store.query("SELECT x FROM (SELECT 1 AS x) s")
    assert out["x"][0] == 1


def test_local_parquet_store_reports_invalid_sql_consistently(tmp_path):
    store = LocalParquetStore(tmp_path)
    try:
        store.query("SELECT FROM")
    except ValueError as exc:
        assert "Invalid SELECT query for LocalParquetStore" in str(exc)
    else:
        raise AssertionError("Expected ValueError for invalid SQL")
