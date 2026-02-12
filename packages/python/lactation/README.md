# lactationcurve (Python)

A toolkit for fitting **dairy cow lactation curves**, evaluating **lactation curve characteristics (LCCs)** (time to peak, peak yield, cumulative yield, persistency), and computing **305‑day milk yield** using the **ICAR guideline**.

> **Contact:** Meike van Leerdam, mbv32@cornell.edu
>
> **Authors:** Judith Osei-Tete, Douwe de Kok, Lucia Trapanese & Meike van Leerdam

> **Initial authored:** 2025‑08‑12

> **Updated:** 2026‑02‑11

---

## Main Lactation curve models implemented:

_MilkBot_ – Flexible four-parameter model describing rise, peak, and decline. (Both frequentist and Bayesian fitting
available)

_Wood_ – Classic three-parameter gamma function model.

_Wilmink_ – Linear–exponential hybrid model, with fixed or estimated decay rate.

_Ali & Schaeffer_ – Polynomial–logarithmic model for complex curve shapes.

_Fischer_ – Simplified exponential decay model.

Additional models available for a.o. symbolic LCC derivations:
**Brody** ,  **Sikka** ,  **Nelder** ,  **Dhanoa** ,  **Emmans** ,  **Hayashi** ,  **Rook** ,  **Dijkstra** ,  **Prasad** .

## Model Formulas

* **Wood** : `y(t) = a * t^b * exp(-c * t)`
* **Wilmink** : `y(t) = a + b * t + c * exp(k * t)` with default `k = -0.05`
* **Ali & Schaeffer** :  `t_scaled = t / 340`, `L = ln(340 / t)`

  `y(t) = a + b*t_scaled + c*t_scaled^2 + d*L + k*L^2`
* **Fischer** : `y(t) = a - b*t - a*exp(-c*t)`
* **MilkBot** : `y(t) = a * (1 - exp((c - t)/b) / 2) * exp(-d*t)`

## Features

- **Frequentist fitting** (numeric optimization & least squares):
  - Wood, Wilmink, Ali & Schaeffer, Fischer, MilkBot
- **Bayesian fitting via MilkBot API**:
  - MilkBot
- **Lactation Curve Characteristics** — symbolic + numeric:
  - time_to_peak, peak_yield, cumulative_milk_yield, persistency
- **ICAR procedures cumulative milk yield:**
  - Test Interval Method
- Input validation/normalization via `validate_and_prepare_inputs`
- Caching of symbolic expressions for performance

## API Overview

The package is organized into three main modules:

1. `lactationcurve.fitting`
2. `lactationcurve.characteristics`
3. `lactationcurve.preprocessing`

Below is a unified API reference for the core public functions.

---

## 1. `lactationcurve/fitting/lactation_curve_fitting.py`

### `fit_lactation_curve(dim, milkrecordings, model="wood", fitting="frequentist", breed="H", parity=3, continent="USA", key=None) -> np.ndarray`

Fit a lactation curve model to DIM and milk-yield records and return predicted daily milk yield.

**Args:**

- `dim` (list[int] | np.ndarray): Days in milk.
- `milkrecordings` (list[float] | np.ndarray): Milk yield per test day (kg or lbs).
- `model` (str): `"wood"`, `"wilmink"`, `"ali_schaeffer"`, `"fischer"`, `"milkbot"`.
- `fitting` (str): `"frequentist"` (default) or `"bayesian"` (MilkBot only).
- `breed` (str): `"H"` or `"J"` (Bayesian only).
- `parity` (int): Cow parity (≥3 treated as a single group for priors) (Bayesian only).
- `continent` (str): `"USA" | "EU" | "CHEN"` (Bayesian only).
- `key` (str | None): MilkBot API key for Bayesian fitting.

**Returns:**

- `np.ndarray`: Predicted daily yields for DIM 1–305 (or the highest DIM >305).

---

### `get_lc_parameters(dim, milkrecordings, model="wood") -> tuple[float, ...]`

Fit a lactation model using frequentist numerical optimization and return model parameters.

**Supported model outputs:**

- Wood → `(a, b, c)`
- Wilmink → `(a, b, c, k)` with `k = -0.05`
- Ali & Schaeffer → `(a, b, c, d, k)`
- Fischer → `(a, b, c)`
- MilkBot → `(a, b, c, d)`

---

### `get_lc_parameters_least_squares(dim, milkrecordings, model="milkbot") -> tuple[float, float, float, float]`

Return MilkBot parameters estimated using **least-squares** (constrained) optimization.

**Returns:**

- `(a, b, c, d)` in alphabetical order.

---

### `bayesian_fit_milkbot_single_lactation(dim, milkrecordings, key, parity=3, breed="H", continent="USA") -> dict`

Fit MilkBot parameters via **Bayesian estimation** using the official MilkBot API.

**Args:**

- `key` (str): Required API key.
- `continent` (str): `"USA"`, `"EU"`, or `"CHEN"` (Chen et al. priors).

**Returns (dict):**

- `{"scale": float, "ramp": float, "decay": float, "offset": float, "nPoints": int}`

---

## 2. `lactationcurve/characteristics/lactation_curve_characteristics.py`

### `lactation_curve_characteristic_function(model="wood", characteristic=None, lactation_length=305)`

Generate symbolic formulas and fast numeric functions for LCCs.

**Models supported (14 total):**

`milkbot, wood, wilmink, ali_schaeffer, fischer, brody, sikka, nelder, dhanoa, emmans, hayashi, rook, dijkstra, prasad`

**Characteristics:**

- `"time_to_peak"`
- `"peak_yield"`
- `"cumulative_milk_yield"`
- `"persistency"`

**Returns:**

- `expr`: SymPy expression (or dict)
- `params`: Tuple of SymPy parameter symbols
- `func`: Lambdified numeric function

---

### `calculate_characteristic(dim, milkrecordings, model, characteristic, fitting="frequentist", key=None, parity=3, breed="H", continent="USA", persistency_method="derived", lactation_length=305) -> float`

Evaluate a lactation curve characteristic from actual test‑day data.

**Args:**

- `dim` (list[int]): Days in milk.
- `milkrecordings` (list[float]): Test‑day yields (kg).
- `model` (str): `"milkbot"`, `"wood"`, `"wilmink"`, `"ali_schaeffer"`, `"fischer"`.
- `characteristic` (str): `"time_to_peak" | "peak_yield" | "cumulative_milk_yield" | "persistency"`.
- `fitting` (str): `"frequentist"` or `"bayesian"`.
- `persistency_method` (str): `"derived"` (default) or `"literature"`.
- `lactation_length` (int | "max"): Horizon for cumulative yield or persistency.

**Returns:**

- `float`: The requested characteristic value.

**Notes:**

- Attempts symbolic formula first; uses numeric fallback when needed.
- For `"literature"` persistency:

  - Wood → `persistency_wood`
  - MilkBot → `persistency_milkbot`

Numeric fallback functions:

- `numeric_time_to_peak(...)`
- `numeric_peak_yield(...)`
- `numeric_cumulative_yield(...)`
- `persistency_fitted_curve(...)`

---

## 3. `lactationcurve/characteristics0/test_interval_method.py`

### `test_interval_method(df, days_in_milk_col=None, milking_yield_col=None, test_id_col=None, default_test_id=1) -> pd.DataFrame`

Compute **305‑day milk yield** using the ICAR **Test Interval Method (TIM)**.

**Args:**

- `df` (pd.DataFrame): Must contain DIM and yield columns.
- Column overrides or autodetection supported for:

  - `"DaysInMilk"` → aliases: `"dim"`, `"testday"`, ...
  - `"MilkingYield"` → aliases: `"yield"`, `"milkyield"`, ...
  - `"TestId"` → aliases: `"id"`, `"animalid"`, ...

**Returns:**

- DataFrame with:

  - `"TestId"`
  - `"Total305Yield"`

**Algorithm:**

- Linear projection from DIM=0 → first test
- Trapezoidal integration between test days
- Linear projection from last test → DIM 305

**Requirement:**

- At least **two** data points per TestId (three recommended).

---

## Output Types Summary

| Function | Output |

|---------|--------|

| `fit_lactation_curve` | Predicted yields (np.ndarray) |

| `get_lc_parameters` | Tuple of numerical parameters |

| `bayesian_fit_milkbot_single_lactation` | Dict of MilkBot parameters |

| `lactation_curve_characteristic_function` | (expr, params, func) |

| `calculate_characteristic` | float (LCC value) |

| `test_interval_method` | DataFrame with 305‑day totals |

## Bayesian (MilkBot API)

* Set `fitting="bayesian"` and `model="milkbot"` in `fit_lactation_curve` or `calculate_characteristic`.
* Provide an **API key** via .env
* Choose priors via `continent="USA" | "EU" | "CHEN"` ([CHEN](https://github.com/Bovi-analytics/Chen-et-al-2023b) supplies published priors from literature).
* The helper `bayesian_fit_milkbot_single_lactation(...)` normalizes differing API responses.
* The key can be requested by sending an email to Jim Ehrlich [jehrlich@MilkBot.com](mailto:jehrlich@MilkBot.com).
* More information about the API can be found [here](https://api.milkbot.com/).

# License

[MIT License](https://github.com/Bovi-analytics/lactation_curve_core/blob/master/LICENSE)
