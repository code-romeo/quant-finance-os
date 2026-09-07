import pytest

from quant_finance_os.risk.metrics import calculate_exposure, max_drawdown


def test_calculate_exposure_mixed_book():
    exposure = calculate_exposure({"AAPL": 10, "MSFT": -5}, {"AAPL": 100.0, "MSFT": 200.0})
    assert exposure.gross == 2000.0
    assert exposure.net == 0.0


def test_calculate_exposure_requires_all_prices():
    with pytest.raises(ValueError, match="missing price"):
        calculate_exposure({"AAPL": 10}, {})


def test_max_drawdown_positive_equity_curve():
    assert round(max_drawdown([100.0, 120.0, 90.0, 110.0]), 6) == 0.25


def test_max_drawdown_requires_positive_values():
    with pytest.raises(ValueError, match="strictly positive"):
        max_drawdown([100.0, 0.0, -10.0])
