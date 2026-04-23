"""

A package for fitting **dairy animal lactation curves**, evaluating
**lactation curve characteristics (LCCs)** (time to peak, peak yield,
cumulative yield, persistency), and computing **305-day milk yield**
using the **ICAR guideline**.

> **Contact:** Meike van Leerdam, mbv32@cornell.edu
>
> **Authors:** Meike van Leerdam, Douwe de Kok, Judith Osei-Tete, Lucia Trapanese

> **Initial authored:** 2025‑08‑12

> **Updated:** 2026‑04‑23

---

## Main Lactation curve models implemented:

MilkBot: Flexible four-parameter model describing rise, peak,
and decline. (Both frequentist and Bayesian fitting available)

Wood: Incomplete gamma function; most popular due to its simplicity,
its stability in the presence of missing data, and its
computational ease.

Wilmink: Linear–exponential hybrid model, with fixed or estimated decay rate.

Ali & Schaeffer: Polynomial-logarithmic model with a linear
regression component for more complex curve shapes.

Fischer: Simple exponential decay model.

Additional models available for a.o. symbolic LCC derivations:
**Brody**, **Sikka**, **Nelder**, **Dhanoa**, **Emmans**,
**Hayashi**, **Rook**, **Dijkstra**, **Prasad**.

---

## Model Formulas

* **Wood** : `y(t) = a * t^b * exp(-c * t)`
* **Wilmink** : `y(t) = a + b * t + c * exp(k * t)` with default `k = -0.05`
* **Ali & Schaeffer** :  `t_scaled = t / 305`, `L = ln(305 / t)`

  `y(t) = a + b*t_scaled + c*t_scaled^2 + d*L + k*L^2`
* **Fischer** : `y(t) = a - b*t - a*exp(-c*t)`
* **MilkBot** : `y(t) = a * (1 - exp((c - t)/b) / 2) * exp(-d*t)`

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

---

## API Overview

The package is organized into three main modules:

1. `lactationcurve.fitting`
2. `lactationcurve.characteristics`
3. `lactationcurve.preprocessing`

---

## Output Types Summary Of Most Important Functions

| Function | Output |

|---------|--------|

| `fit_lactation_curve` | Predicted yields (np.ndarray) |

| `get_lc_parameters` | Tuple of numerical parameters |

| `bayesian_fit_milkbot_single_lactation` | Dict of MilkBot parameters |

| `lactation_curve_characteristic_function` | (expr, params, func) |

| `calculate_characteristic` | float (LCC value) |

| `test_interval_method` | DataFrame with 305‑day totals |

---

## Bayesian Fitting (MilkBot API)

* Set `fitting="bayesian"` and `model="milkbot"` in
  `fit_lactation_curve` or `calculate_characteristic`.
* Provide an **API key** via .env
* Choose priors via `continent="USA" | "EU" | "CHEN"`
  ([CHEN](https://github.com/Bovi-analytics/Chen-et-al-2023b)
  supplies published priors from literature).
* The helper `bayesian_fit_milkbot_single_lactation(...)`
  normalizes differing API responses.
* The key can be requested by sending an email to Jim Ehrlich
  [jehrlich@MilkBot.com](mailto:jehrlich@MilkBot.com).
* More information about the API can be found in the
  [API documentation](https://api.milkbot.com/), or in the
  corresponding
  [paper](https://peerj.com/articles/54/#MainContent).

---

## Citing the lactationcurve package

If you use the `lactationcurve` package in your research, please consider citing it as follows:

*van Leerdam, M. B., de Kok, D., Osei-Tete, J. A., &
Hostens, M. (2026). Bovi-analytics/lactation_curve_core:
v.0.1.0. (v.0.1.0). Zenodo.
https://doi.org/10.5281/zenodo.18715145*


If you also use the Bayesian fitting functionality that relies
on the MilkBot API, please also cite the following paper:

*Ehrlich, J.L., 2013. Quantifying inter-group variability
in lactation curve shape and magnitude with the MilkBot
lactation model. PeerJ 1, e54.
https://doi.org/10.7717/peerj.54*

---

## License

[MIT License](https://github.com/Bovi-analytics/lactation_curve_core/blob/master/LICENSE)


---

## Current version of the package


## Background of the project

The 305‑day yield for milk, fat, and protein is a widely used metric in
dairy production, and the International Committee for Animal Recording
(ICAR) provides guidelines outlining approved methods for its calculation.
However, a global survey of milk recording organizations revealed
substantial variation in how these methods are implemented. The Test
Interval Method is used by 74% of the organizations, reflecting a
preference for methodological simplicity, but it comes with trade-offs in
estimation accuracy. The use of the other approved methods showed wide
variation in correction factors, standard lactation curves, test‑day
definitions, minimum sample requirements, and exclusion criteria. Such
inconsistencies can introduce yield variability that complicates
comparisons, for example in international breeding value evaluation, and
limit the metric’s usefulness in universal models, such as decision
support tools. Thus, the objective of this work was to reformulate the
ICAR guideline section 2, procedure 2, into a unified, transparent, and
accessible software implementation to improve standardization, enhance
documentation, support continuous development, and increase the accuracy
of 305‑day yield estimation.


To achieve this, the ICAR guideline was converted into an open‑source,
Python package that serves as the reference implementation for 305‑day
yield calculation, with lactation‑curve modelling serving as the core of
the package. In addition to the methods described in the original
guideline, this work further incorporates 13 lactation‑curve models, with
both frequentist and Bayesian fitting options, and provides tools to
derive characteristics such as time to peak, peak yield, cumulative yield,
and persistency. These features allow the package to be imported directly
into analytical workflows, enabling users to calculate 305-day yields, fit
and compare lactation curves, and derive key lactation characteristics, by
calling a single function. Ongoing development includes an online
validation platform that will allow users to upload lactation data and
compare 305‑day yield estimates with reference calculations and observed
cumulative yield.
"""


# import submodules to make them available at the package level

from . import characteristics, fitting, preprocessing

__all__ = ["fitting", "characteristics", "preprocessing"]
# from .characteristics import (
#     calculate_characteristic,
#     lactation_curve_characteristic_function,
#     numeric_cumulative_yield,
#     numeric_peak_yield,
#     numeric_time_to_peak,
#     persistency_fitted_curve,
#     persistency_milkbot,
#     persistency_wood,
#     test_interval_method,
# )
# from .fitting import (
#     ali_schaeffer_model,
#     bayesian_fit_milkbot_single_lactation,
#     brody_model,
#     dhanoa_model,
#     dijkstra_model,
#     emmans_model,
#     fischer_model,
#     fit_lactation_curve,
#     get_chen_priors,
#     get_lc_parameters,
#     get_lc_parameters_least_squares,
#     hayashi_model,
#     milkbot_model,
#     nelder_model,
#     prasad_model,
#     rook_model,
#     sikka_model,
#     wilmink_model,
#     wood_model,
#     build_prior,
# )
# from .preprocessing import (
#     PreparedInputs,
#     standardize_lactation_columns,
#     validate_and_prepare_inputs,
# )

# __all__ = [
#     # Preprocessing
#     "PreparedInputs",
#     "standardize_lactation_columns",
#     "validate_and_prepare_inputs",
#     # Fitting
#     "ali_schaeffer_model",
#     "bayesian_fit_milkbot_single_lactation",
#     "brody_model",
#     "dhanoa_model",
#     "dijkstra_model",
#     "emmans_model",
#     "fischer_model",
#     "fit_lactation_curve",
#     "get_chen_priors",
#     "get_lc_parameters",
#     "get_lc_parameters_least_squares",
#     "hayashi_model",
#     "milkbot_model",
#     "nelder_model",
#     "prasad_model",
#     "rook_model",
#     "sikka_model",
#     "wilmink_model",
#     "wood_model",
#     # Characteristics
#     "calculate_characteristic",
#     "lactation_curve_characteristic_function",
#     "numeric_cumulative_yield",
#     "numeric_peak_yield",
#     "numeric_time_to_peak",
#     "persistency_fitted_curve",
#     "persistency_milkbot",
#     "persistency_wood",
#     "test_interval_method",
#     "build_prior",
# ]

# Expose package version (try metadata, fall back to a sensible dev string)
try:
    from importlib.metadata import PackageNotFoundError, version
except Exception:
    try:
        from importlib_metadata import PackageNotFoundError, version  # type: ignore
    except Exception:
        version = None
        PackageNotFoundError = Exception

if version:
    try:
        __version__ = version("lactationcurve")
    except PackageNotFoundError:
        __version__ = "0+dev"
else:
    __version__ = "0+dev"

__all__.append("__version__")
