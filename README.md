# quant-finance-os

Deterministic research-to-production quant operating system foundation.

## Mission
`quant-finance-os` targets the highest-value quant infra failure mode: **research-to-production drift**.  
The same event model drives notebook-style research, backtests, paper trading, and live-readiness checks.

## v0 Foundation (this PR)
- Strongly typed event contracts for:
  - market data
  - signals
  - orders
  - fills
  - positions
  - PnL
- Deterministic event-driven backtest loop
- Minimal portfolio accounting with realized/unrealized PnL
- Execution simulation with configurable slippage/fill ratio/fees
- Validation utilities:
  - lookahead leakage detection
  - walk-forward split generation
- Local analytical storage primitive using Polars + DuckDB + Parquet

## Package layout
- `src/quant_finance_os/core/` event schemas and contracts
- `src/quant_finance_os/backtest/` engine, execution simulation, accounting
- `src/quant_finance_os/validation/` leakage and walk-forward validation tools
- `src/quant_finance_os/data/` local parquet store helper
- `src/quant_finance_os/risk/` placeholder for future exposure/drawdown modules
- `src/quant_finance_os/live/` placeholder for paper/shadow and broker adapters
- `src/quant_finance_os/analytics/` placeholder for attribution/reporting

## Quickstart
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
pytest
```

See:
- `docs/architecture.md`
- `docs/quickstart.md`
- `examples/basic_strategy.py`

## Deploy-fast path
1. Push to a PR branch and ensure the `CI` workflow passes on Python 3.12/3.13.
2. Use the uploaded `python-dist` artifact from CI for release verification.
3. Tag a release only after deterministic replay/accounting tests pass unchanged.
