# Swing Reversion Grid Submission Package

This bundle contains the complete deliverables for the Swing Reversion Grid
strategy, ready for contest submission. It mirrors the Adaptive Momentum
submission layout so each strategy remains fully self-contained.

## Contents

- `your-strategy-template/` – runnable strategy implementation with Docker
  assets and documentation.
- `analysis/` – standalone backtest harness plus configuration presets.
- `reports/` – generated metrics, trade logs, and equity curves (produced after
  running the analysis script).

## Regenerating Reports

```powershell
python swing-grid-submission/analysis/backtest_runner.py `
  --symbols BTC-USD,ETH-USD `
  --config-file swing-grid-submission/analysis/configs/swing_grid_best.json `
  --output swing-grid-submission/reports/backtest-report.md
```

Outputs will refresh inside `swing-grid-submission/reports/`:

- `backtest-report.md`
- `backtest_summary.json`
- `btc_usd_trades.csv`, `btc_usd_equity_curve.csv`
- `eth_usd_trades.csv`, `eth_usd_equity_curve.csv`

Package these files (along with `your-strategy-template/`) into a zip for final
submission when satisfied with performance.
