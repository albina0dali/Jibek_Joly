# Shared Movement Index

`web/movement-index-model.json` is the single parameter source for JavaScript (`calculateMovementIndex`, `movementQuality`) and Python (`calculate_movement_index`, `quality`). All visible scores, core metrics, forecast alternatives, telemetry and exported reports use this model. Legacy `quality` remains an internal schedule-compliance contract and is not rendered as a second network score.

| Factor | Weight | Score, clamped to 0–100 |
|---|---:|---|
| Schedule adherence | 30 | 100 − priority-weighted delay seconds / 30 |
| Capacity utilization | 20 | 100 − 45 × abs(0.7 − moving / active) − 2 × conflicts |
| Energy efficiency advisory proxy | 20 | 70 + 0.05 × advisory savings percent (clamped 0–100) |
| Resource conflicts | 20 | 100 − 12 × unresolved conflicts |
| Arrival accuracy | 10 | 100 − mean projected delay seconds / 40 |

Index = sum(score × weight / 100), rounded to one decimal. NORMAL ≥ 80; ATTENTION ≥ 60; otherwise CRITICAL. The energy score is deliberately conservative: estimated advisory savings are not measured traction efficiency. Its baseline and coefficient are explicit model parameters, not hardcoded final index values. Missing energy advice contributes zero savings. Core savings use available ecoAdvice baseline/energy proxies; extension savings use mean ATO advice. Neither is a measurement.

Core delay minutes convert to seconds; priorities come from train dispatch priorities. Active means unfinished (including scheduled services). Moving requires running status and positive actual speed. Core conflicts count opposing resource queues and recorded signal violations; extension conflicts come from its independent resource validator. Thus the formula is identical, while input values differ between the six-train and sixteen-train models. When all trains finish, utilization is neutral (0.7); core retains recorded delays for the final trip score.

The existing runtime legacy weights remain compatible with stored configurations; they do not change the fixed shared index weights or thresholds. Forecast selection still minimizes weighted delay plus model energy under the original safety constraints.

The paused seed-42 scenario at 08:40 computes 91.1. Injecting delay_10 for F103 (600 seconds) computes 74.0; applying a verified replan computes 91.1. A running scenario may differ as time and energy advice advance. These values are verified by state changes, not assigned by buttons.
