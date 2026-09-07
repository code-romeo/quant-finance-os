from pathlib import Path

import pytest

from quant_finance_os.data.storage import LocalParquetStore


def test_local_parquet_store_query_guardrails(tmp_path: Path):
    store = LocalParquetStore(tmp_path)
    store.write_table("bars", [{"symbol": "AAPL", "price": 100.0}, {"symbol": "MSFT", "price": 200.0}])

    result = store.query("SELECT symbol, price FROM bars")
    assert result == [{"symbol": "AAPL", "price": 100.0}, {"symbol": "MSFT", "price": 200.0}]

    assert store.query("SELECT symbol FROM bars;") == [{"symbol": "AAPL"}, {"symbol": "MSFT"}]

    with pytest.raises(ValueError, match="table name"):
        store.write_table("123bad", [{"v": 1}])

    with pytest.raises(ValueError, match="single SQL statement"):
        store.query("SELECT * FROM bars; SELECT * FROM bars")

    with pytest.raises(ValueError, match="CTE"):
        store.query("WITH cte AS (SELECT * FROM bars) SELECT * FROM cte")

    with pytest.raises(ValueError, match="Only SELECT"):
        store.query("DELETE FROM bars")

    with pytest.raises(ValueError, match="unknown table"):
        store.query("SELECT * FROM missing")
