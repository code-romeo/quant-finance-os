# Quickstart

## 1) Install
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
```

## 2) Run tests
```bash
pytest
```

## 3) Run the example strategy
```bash
python examples/basic_strategy.py
```

The example prints deterministic event output and final PnL snapshots.
