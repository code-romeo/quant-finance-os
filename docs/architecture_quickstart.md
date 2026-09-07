# Architecture & quickstart

## Core contract
The system is built around explicit typed events. All downstream behavior (orders, fills, PnL) is emitted as deterministic events with replay metadata:
- `run_id`
- `seq`
- `event_id`
- `parent_event_id`

## Deterministic backtest loop
`BacktestEngine` takes ordered `MarketEvent` inputs and:
1. validates event ordering (fail fast on out-of-order streams)
2. asks strategy for `SignalEvent` outputs
3. creates `OrderEvent`s and resolves fills via fill/slippage interfaces
4. updates portfolio accounting and emits position/PnL updates

This gives replayable, auditable research behavior and a clear contract for live-shadow parity.

## Validation guardrails
- `assert_no_lookahead`: detects timestamp/horizon leakage
- `generate_walk_forward_splits`: deterministic train/test split generation with embargo
- `bootstrap_mean_ci`: deterministic bootstrap confidence intervals for quick strategy sanity checks

## Data guardrails
`LocalParquetStore` writes parquet tables locally and supports a guarded SQL interface:
- single-statement `SELECT` only
- no CTE or mutation/DDL operations
- query scope limited to registered local tables

## Running tests
```bash
python -m pip install -e .[dev]
pytest
```

## Extending the system
- Add richer fill models by implementing `FillModel`
- Add venue-specific slippage by implementing `SlippageModel`
- Extend `PortfolioLedger` for borrow/financing and multi-currency support
- Replace attribution placeholder with factor-aware attribution modules
- Implement concrete broker adapters under `live/` using `ExecutionAdapter`
