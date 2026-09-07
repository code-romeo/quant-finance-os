import pytest

from quant_finance_os.risk.metrics import max_drawdown


def test_max_drawdown_positive_equity_curve():
    assert round(max_drawdown([100.0, 120.0, 90.0, 110.0]), 6) == 0.25


def test_max_drawdown_requires_positive_values():
    with pytest.raises(ValueError, match="strictly positive"):
        max_drawdown([100.0, 0.0, -10.0])
