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
