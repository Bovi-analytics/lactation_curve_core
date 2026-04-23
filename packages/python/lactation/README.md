# lactationcurve (Python)

A toolkit for fitting **dairy cow lactation curves**, evaluating **lactation curve characteristics (LCCs)** (time to peak, peak yield, cumulative yield, persistency), and computing **305‑day milk yield** using the **ICAR guideline**.

> **Contact:** Meike van Leerdam, mbv32@cornell.edu
>
> **Authors:** Judith Osei-Tete, Douwe de Kok, Lucia Trapanese & Meike van Leerdam

> **Initial authored:** 2025‑08‑12

> **Updated:** 2026‑04‑23

---

## Background

The 305‑day yield for milk, fat, and protein is a widely used metric in dairy production, and the International Committee for Animal Recording (ICAR) provides guidelines outlining approved methods for its calculation. However, a global survey of milk recording organizations revealed substantial variation in how these methods are implemented. The Test Interval Method is used by 74% of the organizations, reflecting a preference for methodological simplicity, but it comes with trade-offs in estimation accuracy. The use of the other approved methods showed wide variation in correction factors, standard lactation curves, test‑day definitions, minimum sample requirements, and exclusion criteria. Such inconsistencies can introduce yield variability that complicates comparisons, for example in international breeding value evaluation, and limit the metric’s usefulness in universal models, such as decision support tools. Thus, the objectiveof this work was to reformulate the ICAR guideline section 2, procedure 2, into a unified, transparent, and accessible software implementation to improve standardization, enhance documentation, support continuous development, and increase the accuracy of 305‑day yield estimation.

---

To achieve this, the ICAR guideline was converted into an open‑source, Python package that serves as the reference implementation for 305‑day yield calculation, with lactation‑curve modelling serving as the core of the package. In addition to the methods described in the original guideline, this work further incorporates 13 lactation‑curve models, with both frequentist and Bayesian fitting options, and provides tools to derive characteristics such as time to peak, peak yield, cumulative yield, and persistency. These features allow the package to be imported directly into analytical workflows, enabling users to calculate 305-day yields, fit and compare lactation curves, and derive key lactation characteristics, by calling a single function. Ongoing development includes an online validation platform that will allow users to upload lactation data and compare 305‑day yield estimates with reference calculations and observed cumulative yield.

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

# Citation

**Citing the lactationcurve package**

If you use the `lactationcurve` package in your research, please consider citing it as follows:

*van Leerdam, M. B., de Kok, D., Osei-Tete, J. A., & Hostens, M. (2026). Bovi-analytics/lactation_curve_core: v.0.1.0. (v.0.1.0).*

*Zenodo. https://doi.org/10.5281/zenodo.18715145*

BibTex:

@software{van_leerdam_2026_lactation_curve_core,

  author       = {van Leerdam, Meike Beatrijs and de Kok, D. and Osei-Tete, J. A. and Hostens, M.},

  title        = {Bovi-analytics/lactation\_curve\_core: v.0.1.0},

  version      = {0.1.0},

  year         = {2026},

  publisher    = {Zenodo},

  doi          = {10.5281/zenodo.18715145},

  url          = {https://doi.org/10.5281/zenodo.18715145}

}

``

A machine-readable citation is included in `CITATION.cff

If you also use the Bayesian fitting functionality that relies on the MilkBot API, please also cite the following paper:

*Ehrlich, J.L., 2013. Quantifying inter-group variability in lactation curve shape and magnitude with the MilkBot® lactation model. PeerJ 1, e54.*

*https://doi.org/10.7717/peerj.54*

# License

[MIT License](https://github.com/Bovi-analytics/lactation_curve_core/blob/master/LICENSE)
