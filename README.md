# quant-finance-os

A deterministic quant research-to-live operating system foundation for solving research-to-production drift.

## Mission
`quant-finance-os` enforces one event contract across research, backtesting, validation, and live-shadow workflows so strategies can be replayed and audited deterministically before capital is put at risk.

## What is implemented
- Strong typed event contracts for market data, signals, orders, fills, position updates, and PnL updates
- Deterministic replay metadata (`run_id`, `seq`, `event_id`, `parent_event_id`)
- Event-driven backtest engine with strategy/fill/slippage interfaces and fail-fast stream ordering checks
- Minimal portfolio accounting (cash, realized/unrealized PnL, equity)
- Validation utilities: lookahead leakage checks, walk-forward split generator, deterministic bootstrap confidence intervals
- Local parquet-oriented data storage with guarded SQL query interface
- Lightweight risk metrics, analytics attribution API, and live/shadow interfaces

## Quickstart
```bash
python -m pip install -e .[dev]
pytest
```

## Package layout
- `src/quant_finance_os/core` — event contracts and sequencing metadata
- `src/quant_finance_os/backtest` — deterministic event-driven engine
- `src/quant_finance_os/portfolio` — accounting state and updates
- `src/quant_finance_os/validation` — leakage/splits/bootstrap checks
- `src/quant_finance_os/data` — local parquet store and guarded query execution
- `src/quant_finance_os/risk` — exposure/drawdown helpers
- `src/quant_finance_os/analytics` — attribution API placeholder
- `src/quant_finance_os/live` — live/shadow adapter contracts

See `/docs/architecture_quickstart.md` for architecture and extension notes.
