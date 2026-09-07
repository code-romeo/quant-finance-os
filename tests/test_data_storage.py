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
    try:
        store.query("SELECT * FROM read_parquet('/tmp/any.parquet')")
    except ValueError as exc:
        assert "registered local tables" in str(exc)
    else:
        raise AssertionError("Expected ValueError for external table functions")


def test_local_parquet_store_allows_cte_over_registered_table(tmp_path):
    store = LocalParquetStore(tmp_path)
    store.write_table("bars", pl.DataFrame({"price": [101.0, 102.0]}))
    out = store.query("WITH base AS (SELECT * FROM bars) SELECT avg(price) AS p FROM base")
    assert out["p"][0] == 101.5


def test_local_parquet_store_blocks_commented_external_function(tmp_path):
    store = LocalParquetStore(tmp_path)
    try:
        store.query("SELECT * FROM read_/* bypass */parquet('/tmp/any.parquet')")
    except ValueError as exc:
        assert "registered local tables" in str(exc)
    else:
        raise AssertionError("Expected ValueError for commented external table functions")
