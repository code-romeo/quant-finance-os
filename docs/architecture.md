# Architecture

`drift-guard-quant-os` uses a deterministic event model as the system boundary.

## Core design principles
1. One typed event schema across research/backtest/paper/live.
2. Deterministic sequencing for replay and debugging.
3. Explicit execution assumptions (slippage/fills/fees).
4. Validation as a first-class step before deployment.

## Current implemented path
- `MarketDataEvent -> Strategy -> OrderEvent -> FillEvent -> Portfolio updates -> PnLEvent`
- Events are ordered by `(timestamp, seq, event_id)` and re-numbered in the engine for deterministic replay.

## Next expansions
- richer instrument model
- corporate actions and survivorship-safe loaders
- exposure/factor risk modules
- live paper/shadow adapters using same event contracts
