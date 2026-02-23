'''
Lactation curve fitting module.

This module provides functions for fitting lactation curve models to dairy cow
lactation data and predicting milk yield.

Pre-defined lactation curve models
----------------------------------
- Models that can be fitted using frequentist statistics (numeric or least squares optimization):
    - Wood
    - Wilmink
    - Ali & Schaeffer
    - Fischer
    - MilkBot

- Models that can be fitted using Bayesian fitting:
    - MilkBot

- Models that are currently implemented but not yet available for fitting:
    - Brody
    - Sikka
    - Nelder
    - Dhanoa
    - Emmans
    - Hayashi
    - Rook
    - Dijkstra
    - Prasad

Author: Meike van Leerdam  
Date: 12-8-2025  
Last update: 11-feb-2025

Requires
--------
- numpy
- scipy
- requests
- lactationcurve.preprocessing.validate_and_prepare_inputs

Public functions
----------------
- fit_lactation_curve(dim, milkrecordings, model="wood", fitting="frequentist", breed="H", parity=3, continent="USA", key=None)  
  Fit a lactation curve to the provided data and return predicted milk yield
  for each day in milk (DIM) in the range 1–305 (or up to the maximum DIM if it exceeds 305).

- get_lc_parameters(dim, milkrecordings, model="wood")  
  Fit a lactation curve to the provided data and return model parameters using
  frequentist statistics: minimize/curve_fit.

- get_lc_parameters_least_squares(dim, milkrecordings, model="milkbot")  
  Fit a lactation curve to the provided data and return model parameters using
  least-squares estimation (frequentist).

Notes
-----
- Units: DIM in days, milk in kg or lbs.
- Input validation and normalization are delegated to
  `lactationcurve.preprocessing.validate_and_prepare_inputs`.
'''

# packages
import numpy as np
import requests
from scipy.optimize import curve_fit, least_squares, minimize
from lactationcurve.preprocessing import validate_and_prepare_inputs


# --- Models ---
def milkbot_model(t, a, b, c, d):
    """MilkBot lactation curve model.

    Args:
        t: Time since calving in days (DIM), scalar or array-like.
        a: Scale; overall level of milk production.
        b: Ramp; governs the rate of rise in early lactation.
        c: Offset; small (usually minor) correction around the theoretical start of lactation.
        d: Decay; exponential decline rate, evident in late lactation.

    Returns:
        Predicted milk yield at `t` (same shape as `t`).

    Notes:
        Formula: `y(t) = a * (1 - exp((c - t) / b) / 2) * exp(-d * t)`.
    """
    return a * (1 - np.exp((c - t) / b) / 2) * np.exp(-d * t)


def wood_model(t, a, b, c):
    """Wood lactation curve model.

    Args:
        t: Time since calving in days (DIM), scalar or array-like.
        a: Scale parameter (numerical).
        b: Shape parameter controlling rise (numerical).
        c: Decay parameter (numerical).

    Returns:
        Predicted milk yield at `t`.

    Notes:
        Formula: `y(t) = a * t**b * exp(-c * t)`.
    """
    return a * (t**b) * np.exp(-c * t)


def wilmink_model(t, a, b, c, k=-0.05):
    """Wilmink lactation curve model.

    Args:
        t: Time since calving in days (DIM), scalar or array-like.
        a: Intercept-like parameter (numerical).
        b: Linear trend coefficient (numerical).
        c: Exponential-term scale (numerical).
        k: Fixed exponential rate (numerical), default -0.05.

    Returns:
        Predicted milk yield at `t`.

    Notes:
        Formula: `y(t) = a + b * t + c * exp(k * t)`.
    """
    t = np.asarray(t)
    return a + b * t + c * np.exp(k * t)


def ali_schaeffer_model(t, a, b, c, d, k):
    """Ali & Schaeffer lactation curve model.

    Args:
        t: Time since calving in days (DIM). Use `t >= 1` to avoid `log(0)`.
        a: Intercept-like parameter (numerical).
        b: Linear coefficient on scaled time `t/305` (numerical).
        c: Quadratic coefficient on scaled time `t/305` (numerical).
        d: Coefficient on `log(305/t)` (numerical).
        k: Coefficient on `[log(305/t)]^2` (numerical).

    Returns:
        Predicted milk yield at `t`.

    Notes:
        Uses `t_scaled = t / 305` and `log_term = ln(305 / t)`.
    """
    t_scaled = t / 305
    log_term = np.log(305 / t)
    return a + b * t_scaled + c * (t_scaled**2) + d * log_term + k * (log_term**2)


def fischer_model(t, a, b, c):
    """Fischer lactation curve model.

    Args:
        t: Time since calving in days (DIM).
        a: Scale parameter (numerical).
        b: Linear decline parameter (numerical).
        c: Exponential decay parameter (numerical).

    Returns:
        Predicted milk yield at `t`.
    """
    return a - b * t - a * np.exp(-c * t)


def brody_model(t, a, k):
    """Brody lactation curve model.

    Args:
        t: Time since calving in days (DIM).
        a: Scale parameter (numerical).
        k: Decay parameter (numerical).

    Returns:
        Predicted milk yield at `t`.
    """
    return a * np.exp(-k * t)


def sikka_model(t, a, b, c):
    """Sikka lactation curve model.

    Args:
        t: Time since calving in days (DIM).
        a: Scale parameter (numerical).
        b: Growth parameter (numerical).
        c: Quadratic decay parameter (numerical).

    Returns:
        Predicted milk yield at `t`.
    """
    return a * np.exp(b * t - c * t**2)


def nelder_model(t, a, b, c):
    """Nelder lactation curve model.

    Args:
        t: Time since calving in days (DIM).
        a: Denominator intercept (numerical).
        b: Denominator linear coefficient (numerical).
        c: Denominator quadratic coefficient (numerical).

    Returns:
        Predicted milk yield at `t`.

    Notes:
        Formula: `y(t) = t / (a + b*t + c*t**2)`.
    """
    return t / (a + b * t + c * t**2)


def dhanoa_model(t, a, b, c):
    """Dhanoa lactation curve model.

    Args:
        t: Time since calving in days (DIM).
        a: Scale parameter (numerical).
        b: Shape parameter (numerical).
        c: Decay parameter (numerical).

    Returns:
        Predicted milk yield at `t`.

    Notes:
        Formula: `y(t) = a * t ** (b * c) * exp(-c * t)`.
    """
    return a * t ** (b * c) * np.exp(-c * t)


def emmans_model(t, a, b, c, d):
    """Emmans lactation curve model.

    Args:
        t: Time since calving in days (DIM).
        a: Scale parameter (numerical).
        b: Growth parameter (numerical).
        c: Decay parameter (numerical).
        d: Location parameter in nested exponential (numerical).

    Returns:
        Predicted milk yield at `t`.

    Notes:
        Formula: `y(t) = a * exp(-exp(d - b*t)) * exp(-c*t)`.
    """
    return a * np.exp(-np.exp(d - b * t)) * np.exp(-c * t)


def hayashi_model(t, a, b, c, d):
    """Hayashi lactation curve model.

    Args:
        t: Time since calving in days (DIM).
        a: Ratio parameter (> 0) (numerical).
        b: Scale parameter (numerical).
        c: Time constant for the first exponential term (numerical).
        d: Parameter retained for compatibility with literature (unused in this expression).

    Returns:
        Predicted milk yield at `t`.

    Notes:
        Formula: `y(t) = b * (exp(-t / c) - exp(-t / (a * c)))`.
    """
    return b * (np.exp(-t / c) - np.exp(-t / (a * c)))


def rook_model(t, a, b, c, d):
    """Rook lactation curve model.

    Args:
        t: Time since calving in days (DIM).
        a: Scale parameter (numerical).
        b: Shape parameter in rational term (numerical).
        c: Offset parameter in rational term (numerical).
        d: Exponential decay parameter (numerical).

    Returns:
        Predicted milk yield at `t`.

    Notes:
        Formula: `y(t) = a * (1 / (1 + b / (c + t))) * exp(-d * t)`.
    """
    return a * (1 / (1 + b / (c + t))) * np.exp(-d * t)


def dijkstra_model(t, a, b, c, d):
    """Dijkstra lactation curve model.

    Args:
        t: Time since calving in days (DIM).
        a: Scale parameter (numerical).
        b: Growth parameter (numerical).
        c: Saturation rate parameter (numerical).
        d: Decay parameter (numerical).

    Returns:
        Predicted milk yield at `t`.

    Notes:
        Formula: `y(t) = a * exp((b * (1 - exp(-c * t)) / c) - d * t)`.
    """
    return a * np.exp((b * (1 - np.exp(-c * t)) / c) - d * t)


def prasad_model(t, a, b, c, d):
    """Prasad lactation curve model.

    Args:
        t: Time since calving in days (DIM).
        a: Intercept-like parameter (numerical).
        b: Linear coefficient (numerical).
        c: Quadratic coefficient (numerical).
        d: Inverse-time coefficient (numerical).

    Returns:
        Predicted milk yield at `t`.

    Notes:
        Formula: `y(t) = a + b*t + c*t**2 + d/t`.
    """
    return a + b * t + c * t**2 + d / t


# objectives for minimize
def wood_objective(par, x, y):
    """Objective function (sum of squared errors) for the Wood model.

    Args:
        par: Parameter vector `(a, b, c)`.
        x: DIM values.
        y: Observed milk yields.

    Returns:
        Sum of squared residuals between observed values and Wood model predictions.
    """
    return np.sum((y - wood_model(x, *par)) ** 2)


def milkbot_objective(par, x, y):
    """Objective function (sum of squared errors) for the MilkBot model.

    Args:
        par: Parameter vector `(a, b, c, d)`.
        x: DIM values.
        y: Observed milk yields.

    Returns:
        Sum of squared residuals between observed values and MilkBot predictions.
    """
    return np.sum((y - milkbot_model(x, *par)) ** 2)

def residuals_milkbot(par, x, y):
    """Residuals for least-squares fitting of the MilkBot model.

    Args:
        par: Parameter vector `(a, b, c, d)`.
        x: DIM values.
        y: Observed milk yields.

    Returns:
        Vector of residuals `y - y_pred`.
    """
    return y - milkbot_model(x, *par)


def fit_lactation_curve(
    dim,
    milkrecordings,
    model="wood",
    fitting="frequentist",
    breed="H",
    parity=3,
    continent="USA",
    key=None,
):
    """Fit lactation data to a lactation curve model and return predictions.

    Depending on `fitting`:
    - **frequentist**: Fits parameters using `minimize` and/or `curve_fit`
      for the specified `model`, then predicts over DIM 1–305 (or up to `max(dim)` if greater).
    - **bayesian**: (MilkBot only) Calls the MilkBot Bayesian fitting API and
      returns predictions using the fitted parameters.

    Args:
        dim (Int): List/array of days in milk (DIM).
        milkrecordings (Float): List/array of milk recordings (kg).
        model (Str): Model name (lowercase), default "wood".
            Supported for frequentist: "wood", "wilmink", "ali_schaeffer", "fischer", "milkbot".
        fitting (Str): "frequentist" (default) or "bayesian".
            Bayesian fitting is currently implemented only for "milkbot".
        breed (Str): "H" (Holstein, default) or "J" (Jersey). Only used for Bayesian.
        parity (Int): Lactation number; all parities >= 3 considered one group in priors (Bayesian).
        continent (Str): Prior source for Bayesian, "USA" (default), "EU", or "CHEN".
        key (Str | None): API key for MilkBot (required when `fitting == "bayesian"`).

    Returns:
        List/array of predicted milk yield for DIM 1–305 (or up to the maximum DIM if > 305).

    Raises:
        Exception: If an unknown model is requested (frequentist),
            or Bayesian is requested for a non-MilkBot model,
            or `key` is missing when Bayesian fitting is requested.

    Notes:
        Uses `validate_and_prepare_inputs` for input checking and normalization.
    """
    # check and prepare input
    inputs = validate_and_prepare_inputs(
        dim,
        milkrecordings,
        model=model,
        fitting=fitting,
        breed=breed,
        parity=parity,
        continent=continent,
    )

    dim = inputs.dim
    milkrecordings = inputs.milkrecordings
    model = inputs.model
    fitting = inputs.fitting
    breed = inputs.breed
    parity = inputs.parity
    continent = inputs.continent

    if fitting == "frequentist":
        if model == "wood":
            a_w, b_w, c_w = get_lc_parameters(dim, milkrecordings, model)
            if max(dim) > 305:
                t_range = np.arange(1, (max(dim) + 1))
                y_w = wood_model(t_range, a_w, b_w, c_w)
            else:
                t_range = np.arange(1, 306)
                y_w = wood_model(t_range, a_w, b_w, c_w)
            return y_w

        elif model == "wilmink":
            a_wil, b_wil, c_wil, k_wil = get_lc_parameters(dim, milkrecordings, model)
            if max(dim) > 305:
                t_range = np.arange(1, (max(dim) + 1))
                y_wil = wilmink_model(t_range, a_wil, b_wil, c_wil, k_wil)
            else:
                t_range = np.arange(1, 306)
                y_wil = wilmink_model(t_range, a_wil, b_wil, c_wil, k_wil)
            return y_wil

        elif model == "ali_schaeffer":
            a_as, b_as, c_as, d_as, k_as = get_lc_parameters(dim, milkrecordings, model)
            if max(dim) > 305:
                t_range = np.arange(1, (max(dim) + 1))
                y_as = ali_schaeffer_model(t_range, a_as, b_as, c_as, d_as, k_as)
            else:
                t_range = np.arange(1, 306)
                y_as = ali_schaeffer_model(t_range, a_as, b_as, c_as, d_as, k_as)
            return y_as

        elif model == "fischer":
            a_f, b_f, c_f = get_lc_parameters(dim, milkrecordings, model)
            if max(dim) > 305:
                t_range = np.arange(1, (max(dim) + 1))
                y_f = fischer_model(t_range, a_f, b_f, c_f)
            else:
                t_range = np.arange(1, 306)
                y_f = fischer_model(t_range, a_f, b_f, c_f)
            return y_f

        elif model == "milkbot":
            a_mb, b_mb, c_mb, d_mb = get_lc_parameters(dim, milkrecordings, model)
            if max(dim) > 305:
                t_range = np.arange(1, (max(dim) + 1))
            else:
                t_range = np.arange(1, 306)

            y_mb = milkbot_model(t_range, a_mb, b_mb, c_mb, d_mb)
            return y_mb

        else:
            raise Exception("Unknown model")
    else:
        if model == "milkbot":
            if key == None:
                raise Exception("Key needed to use Bayesian fitting engine milkbot")
            else:
                parameters = bayesian_fit_milkbot_single_lactation(
                    dim, milkrecordings, key, parity, breed, continent
                )
                if max(dim) > 305:
                    t_range = np.arange(1, (max(dim) + 1))
                    y_mb_bay = milkbot_model(
                        t_range,
                        parameters["scale"],
                        parameters["ramp"],
                        parameters["offset"],
                        parameters["decay"],
                    )
                else:
                    t_range = np.arange(1, 306)
                    y_mb_bay = milkbot_model(
                        t_range,
                        parameters["scale"],
                        parameters["ramp"],
                        parameters["offset"],
                        parameters["decay"],
                    )
                return y_mb_bay
        else:
            raise Exception("Bayesian fitting is currently only implemented for milkbot models")


def get_lc_parameters_least_squares(dim, milkrecordings, model="milkbot"):
    """Fit lactation data and return model parameters (least squares; frequentist).

    This helper uses `scipy.optimize.least_squares` to fit the MilkBot model with bounds,
    and returns the fitted parameters. 
    Currently implemented only for the MilkBot model, as it is more complex and benefits from the robust optimization approach. 
    Other models can be fitted using `get_lc_parameters` with numerical optimisation, which is generally faster for simpler models.

    Args:
        dim (int): List/array of DIM values.
        milkrecordings (float): List/array of milk recordings (kg).
        model (str): Pre-defined model name; currently used with "milkbot".

    Returns:
        Parameters `(a, b, c, d)` as `np.float` in alphabetic order.

    """
    # check and prepare input
    inputs = validate_and_prepare_inputs(dim, milkrecordings, model=model)

    dim = inputs.dim
    milkrecordings = inputs.milkrecordings
    model = inputs.model

    # ------------------------------
    # Initial guess
    # ------------------------------
    a0 = np.max(milkrecordings)
    b0 = 50.0
    c0 = 30.0
    d0 = 0.01
    p0 = [a0, b0, c0, d0]

    # ------------------------------
    # Parameter bounds
    # ------------------------------
    lower = [np.max(milkrecordings) * 0.5, 1.0, -300.0, 1e-6]
    upper = [np.max(milkrecordings) * 8.0, 400.0, 300.0, 1.0]

    # ------------------------------
    # Fit using least-squares
    # ------------------------------
    res = least_squares(
        residuals_milkbot,
        p0,
        args=(dim, milkrecordings),
        bounds=(lower, upper),
        method="trf",  # trust region reflective, works well with bounds
    )

    # ------------------------------
    # Extract parameters
    # ------------------------------
    a_mb, b_mb, c_mb, d_mb = res.x

    return a_mb, b_mb, c_mb, d_mb


def get_lc_parameters(dim, milkrecordings, model="wood"):
    """Fit lactation data to a model and return fitted parameters (frequentist).

    Depending on `model`, this uses `scipy.optimize.minimize` and/or
    `scipy.optimize.curve_fit` with model-specific starting values and bounds.

    Args:
        dim (int): List/array of DIM values.
        milkrecordings (float): List/array of milk recordings (kg).
        model (str): One of "wood", "wilmink", "ali_schaeffer", "fischer", "milkbot".

    Returns:
        Fitted parameters as floats, in alphabetical order by parameter name:
            - wood: (a, b, c)
            - wilmink: (a, b, c, k) with k fixed at -0.05
            - ali_schaeffer: (a, b, c, d, k)
            - fischer: (a, b, c)
            - milkbot: (a, b, c, d)
    """
    # check and prepare input
    inputs = validate_and_prepare_inputs(dim, milkrecordings, model=model)

    dim = inputs.dim
    milkrecordings = inputs.milkrecordings
    model = inputs.model

    if model == "wood":
        wood_guess = [30, 0.2, 0.01]
        wood_bounds = [(1, 100), (0.01, 1.5), (0.0001, 0.1)]
        wood_res = minimize(
            wood_objective, wood_guess, args=(dim, milkrecordings), bounds=wood_bounds
        )
        a_w, b_w, c_w = wood_res.x
        return a_w, b_w, c_w

    elif model == "wilmink":
        wil_guess = [10, 0.1, 30]
        wil_params, _ = curve_fit(wilmink_model, dim, milkrecordings, p0=wil_guess)
        a_wil, b_wil, c_wil = wil_params
        k_wil = -0.05  # set fixed
        return a_wil, b_wil, c_wil, k_wil

    elif model == "ali_schaeffer":
        ali_schaeffer_guess = [10, 10, -5, 1, 1]
        ali_schaeffer_params, _ = curve_fit(
            ali_schaeffer_model, dim, milkrecordings, p0=ali_schaeffer_guess
        )
        a_as, b_as, c_as, d_as, k_as = ali_schaeffer_params
        return a_as, b_as, c_as, d_as, k_as

    elif model == "fischer":
        fischer_guess = [max(milkrecordings), 0.01, 0.01]
        fischer_bounds = [(0, 100), (0, 1), (0.0001, 1)]
        fischer_params, _ = curve_fit(
            fischer_model,
            dim,
            milkrecordings,
            p0=fischer_guess,
            bounds=np.transpose(fischer_bounds),
        )
        a_f, b_f, c_f = fischer_params
        return a_f, b_f, c_f

    elif model == "milkbot":
        mb_guess = [max(milkrecordings), 20.0, -0.7, 0.022]
        mb_bounds = [(1, 100), (1, 100), (-600, 300), (0.0001, 0.1)]
        mb_res = minimize(milkbot_objective, mb_guess, args=(dim, milkrecordings), bounds=mb_bounds)
        a_mb, b_mb, c_mb, d_mb = mb_res.x
        return a_mb, b_mb, c_mb, d_mb


def get_chen_priors(parity: int) -> dict:
    """
    Return Chen et al. priors in MilkBot format.

    Args:
        parity: Lactation number (1, 2, or >= 3).

    Returns:
        Dictionary with parameter priors:
        - "scale": {"mean", "sd"}
        - "ramp": {"mean", "sd"}
        - "decay": {"mean", "sd"}
        - "offset": {"mean", "sd"}
        - "seMilk": Standard error of milk measurement.
        - "milkUnit": Unit string (e.g., "kg").
    """
    if parity == 1:
        return {
            "scale": {"mean": 34.11, "sd": 7},
            "ramp": {"mean": 29.96, "sd": 3},
            "decay": {"mean": 0.001835, "sd": 0.000738},
            "offset": {"mean": -0.5, "sd": 0.02},
            "seMilk": 4,
            "milkUnit": "kg",
        }

    if parity == 2:
        return {
            "scale": {"mean": 44.26, "sd": 9.57},
            "ramp": {"mean": 22.52, "sd": 3},
            "decay": {"mean": 0.002745, "sd": 0.000979},
            "offset": {"mean": -0.78, "sd": 0.07},
            "seMilk": 4,
            "milkUnit": "kg",
        }

    # parity >= 3
    return {
        "scale": {"mean": 48.41, "sd": 10.66},
        "ramp": {"mean": 22.54, "sd": 8.724},
        "decay": {"mean": 0.002997, "sd": 0.000972},
        "offset": {"mean": 0.0, "sd": 0.03},
        "seMilk": 4,
        "milkUnit": "kg",
    }


def bayesian_fit_milkbot_single_lactation(
    dim, milkrecordings, key: str, parity=3, breed="H", continent="USA"
) -> dict:
    """
    Fit a single lactation using the MilkBot API.

    Args:
        dim: List/array of DIM values.
        milkrecordings: List/array of milk recordings (kg).
        key: API key for MilkBot.
        parity: Lactation number; values >= 3 are treated as one group in priors.
        breed: "H" (Holstein) or "J" (Jersey).
        continent: Prior source:
            - "USA"   → MilkBot USA priors
            - "EU"    → MilkBot EU priors
            - "CHEN"  → Chen et al. published priors

    Returns:
        Dictionary with fitted parameters and metadata:
            {
                "scale": float,
                "ramp": float,
                "decay": float,
                "offset": float,
                "nPoints": int
            }

    Raises:
        requests.HTTPError: For unsuccessful HTTP response codes.
        RuntimeError: If the response format is unexpected.

    Notes:
        - When `continent == "CHEN"`, Chen et al. priors are included in the request payload.
        - EU calls use the GCP EU endpoint; others use `milkbot.com`.
    """
    # check and prepare input
    inputs = validate_and_prepare_inputs(
        dim, milkrecordings, breed=breed, parity=parity, continent=continent
    )

    dim = inputs.dim
    milkrecordings = inputs.milkrecordings
    breed = inputs.breed
    parity = inputs.parity
    continent = inputs.continent

    # -----------------------------
    # Select server (USA vs EU)
    # -----------------------------
    if continent == "EU":
        base_url = "https://europe-west1-numeric-analogy-337601.cloudfunctions.net/milkBot-fitter"
    else:
        base_url = "https://milkbot.com"

    # -----------------------------
    # Prepare headers
    # -----------------------------
    headers = {"Content-Type": "application/json", "X-API-KEY": key}

    # -----------------------------
    # Prepare milk points
    # -----------------------------
    points = sorted(
        ({"dim": int(d), "milk": float(m)} for d, m in zip(dim, milkrecordings)),
        key=lambda p: p["dim"],
    )

    # -----------------------------
    # Lactation metadata
    # -----------------------------
    payload = {
        "lactation": {
            "lacKey": "single_lactation_fit",
            "breed": breed,
            "parity": parity,
            "points": points,
        },
        "options": {
            "returnInputData": False,
            "returnPath": False,
            "returnDiscriminatorPath": False,
            # "fitEngine": "AnnealingFitter@2.0", #comment out to use the default fitter 
            # "fitObjective": "MB2@2.0",
            "preferredMilkUnit": "kg",
        },
    }

    # -----------------------------
    # Add priors only if Chen
    # -----------------------------
    if continent == "CHEN":
        payload["priors"] = get_chen_priors(parity)

    # -----------------------------
    # Call API
    # -----------------------------
    response = requests.post(f"{base_url}/fitLactation", headers=headers, json=payload)
    response.raise_for_status()
    res = response.json()

    # -----------------------------
    # Normalize response (USA vs EU)
    # -----------------------------
    if "fittedParams" in res:
        # USA-style response
        fitted = res["fittedParams"]
    elif "params" in res:
        fitted = res["params"]
    else:
        raise RuntimeError(f"Unexpected MilkBot response format: {res}")

    # -----------------------------
    # Parse result
    # -----------------------------

    return {
        "scale": fitted["scale"],
        "ramp": fitted["ramp"],
        "decay": fitted["decay"],
        "offset": fitted["offset"],
        "nPoints": len(points),
    }
