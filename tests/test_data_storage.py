import polars as pl

from quant_finance_os.data import LocalParquetStore


def test_local_parquet_store_registers_written_tables(tmp_path):
    store = LocalParquetStore(tmp_path)
    store.write_table("bars", pl.DataFrame({"symbol": ["AAPL"], "price": [101.0]}))

    out = store.query("SELECT symbol, price FROM bars")
    assert out.to_dict(as_series=False) == {"symbol": ["AAPL"], "price": [101.0]}
