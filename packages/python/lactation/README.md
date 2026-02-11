# lactationcurve (Python)

A toolkit for fitting **dairy cow lactation curves**, evaluating **lactation curve characteristics (LCCs)** (time to peak, peak yield, cumulative yield, persistency), and computing **305‑day milk yield** using the **ICAR guideline**.

> **Contact:** Meike van Leerdam, mbv32@cornell.edu

> **Initial authored:** 2025‑08‑12

> **Updated:** 2026‑02‑11

---


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


## Models & Formulas

* **Wood** : `y(t) = a * t^b * exp(-c * t)`
* **Wilmink** : `y(t) = a + b * t + c * exp(k * t)` with fixed `k = -0.05`
* **Ali & Schaeffer** : let `t_scaled = t / 340`, `L = ln(340 / t)`

  `y(t) = a + b*t_scaled + c*t_scaled^2 + d*L + k*L^2`

* **Fischer** : `y(t) = a - b*t - a*exp(-c*t)`
* **MilkBot** : `y(t) = a * (1 - exp((c - t)/b) / 2) * exp(-d*t)`

Additional models available for symbolic LCC derivations:
 **Brody** ,  **Sikka** ,  **Nelder** ,  **Dhanoa** ,  **Emmans** ,  **Hayashi** ,  **Rook** ,  **Dijkstra** ,  **Prasad** .


## API Overview


### `lactationcurve/fitting/lactation_curve_fitting.py`

**`fit_lactation_curve(dim, milkrecordings, model="wood", fitting="frequentist", breed="H", parity=3, continent="USA", key=None) -> np.ndarray`**

Fit and return predicted yields for DIM `1..305` (or up to `max(dim)` if greater).

* Models (frequentist): `"wood" | "wilmink" | "ali_schaeffer" | "fischer" | "milkbot"`
* Methods: `"frequentist"` (default) or `"bayesian"` (MilkBot only)
* Bayesian args: `breed`, `parity`, `continent`, `key` (API key)

**`get_lc_parameters(dim, milkrecordings, model="wood") -> tuple[float, ...]`**

Return fitted parameters (numerical):

* wood: `(a, b, c)`
* wilmink: `(a, b, c, k)` with `k = -0.05`
* ali_schaeffer: `(a, b, c, d, k)`
* fischer: `(a, b, c)`
* milkbot: `(a, b, c, d)`

**`get_lc_parameters_least_squares(dim, milkrecordings, model="milkbot") -> (a, b, c, d)`**

Return fitted parameters (algabraic)

**`bayesian_fit_milkbot_single_lactation(...) -> dict`**

Calls MilkBot API; normalized result keys: `{"scale","ramp","decay","offset","nPoints"}`.

`continent` selects priors: `"USA" | "EU" | "CHEN"` (CHEN uses published priors).



### `lactationcurve/characteristics0/lactation_curve_characteristics.py`

**`lactation_curve_characteristic_function(model='wood', characteristic=None, lactation_length=305)`**

Derive (and cache) a symbolic **expression** and a lambdified **function** for:
`"time_to_peak"`, `"peak_yield"`, `"cumulative_milk_yield"`, `"persistency"`.

Returns `(expr, params, func)`; if `characteristic=None`, returns a dict of all
(‘persistency’ may be `None` for some models).

**`calculate_characteristic(dim, milkrecordings, model='wood', characteristic='cumulative_milk_yield', fitting='frequentist', key=None, parity=3, breed='H', continent='USA', persistency_method='derived', lactation_length=305) -> float`**

End‑to‑end evaluation from data. Tries **symbolic** first; falls back to **numeric** if needed.

Numeric fallbacks:

* `numeric_time_to_peak(...) -> int`
* `numeric_peak_yield(...) -> float`
* `numeric_cumulative_yield(..., lactation_length=305) -> float`

Persistency utilities:

* `"derived"`: average slope after peak → end (works for all supported models).
* `"literature"`: closed forms for Wood and MilkBot.

* `persistency_wood(b, c) -> float` (Wood closed form)
* `persistency_milkbot(d) -> float` (MilkBot closed form)
* `persistency_fitted_curve(..., lactation_length=305) -> float` (average slope from peak → end)



### `lactationcurve/characteristics0/test_interval_method.py`

**`test_interval_method(df, days_in_milk_col=None, milking_yield_col=None, test_id_col=None, default_test_id=1) -> pd.DataFrame`**

Compute **305‑day total** per `TestId` using the ICAR  **Test Interval Method** :

* **Start** : Linear projection from calving (DIM=0) to first test day
* **Intermediate** : Trapezoidal rule between test days
* **End** : Linear projection from last test day to DIM=305 (uses `306 - last_DIM`)

Column flexibility (case‑insensitive aliases):

* DIM: `["daysinmilk", "dim", "testday"]`
* Yield: `["milkingyield", "testdaymilkyield", "milkyield", "yield"]`
* Id: `["animalid", "testid", "id"]`

Returns: `["TestId", "Total305Yield"]`.


## Bayesian (MilkBot API)

* Set `fitting="bayesian"` and `model="milkbot"` in `fit_lactation_curve` or `calculate_characteristic`.
* Provide an **API key** via .env
* Choose priors via `continent="USA" | "EU" | "CHEN"` (CHEN supplies published priors from literature).
* The helper `bayesian_fit_milkbot_single_lactation(...)` normalizes differing API responses.


# License

MIT License

Copyright (c) 2025 Bovi-Analytics

Permission is hereby granted, free of charge, to any person obtaining a copy

of this software and associated documentation files (the "Software"), to deal

in the Software without restriction, including without limitation the rights

to use, copy, modify, merge, publish, distribute, sublicense, and/or sell

copies of the Software, and to permit persons to whom the Software is

furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all

copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR

IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,

FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE

AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER

LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,

OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE

SOFTWARE.
