# %% md
# Functions for fitting of lactation curve models to lactation data
# %% md
# Author: Meike van Leerdam, Date: 12-8-2025
# %%

# packages
import numpy as np
import requests
from scipy.optimize import curve_fit, least_squares, minimize

from lactationcurve.preprocessing import validate_and_prepare_inputs


# --- Models ---
def milkbot_model(t, a, b, c, d):
    """MilkBot lactation curve model

    Input variables:
        t = time since calving in days (DIM)
        a = scale, the overall level of milk production
        b = ramp, governs the rate of the rise in early lactation
        c = offset is a small (usually insignificant) correction for time between calving and the theoretical start of lactation
        d = decay is the rate of exponential decline, most apparent in late lactation

    output: milk yield at time t
    """
    return a * (1 - np.exp((c - t) / b) / 2) * np.exp(-d * t)


def wood_model(t, a, b, c):
    """Wood Lactation curve model
    Input variables:
        t = time since calving in days (DIM)
        a,b,c = parameters Wood model (numerical)

    Output: milk yield at time t
    """
    return a * (t**b) * np.exp(-c * t)


def wilmink_model(t, a, b, c, k=-0.05):
    """Wilmink Lactation curve model
    Input variables:
        t = time since calving in days (DIM)
        a,b,c = parameters Wilmink model, (numerical)
        k = parameter Wilmink function (numerical), with default value -0.05
    Output: milk yield at time t
    """
    t = np.asarray(t)
    return a + b * t + c * np.exp(k * t)


def ali_schaeffer_model(t, a, b, c, d, k):
    """Ali & Schaeffer Lactation curve model
    Input variables:
        t = time since calving in days (DIM)
        a,b,c,d,k = parameters Ali & Schaeffer model (numerical)

    Output: milk yield at time t
    """
    t_scaled = t / 340
    log_term = np.log(340 / t)
    return a + b * t_scaled + c * (t_scaled**2) + d * log_term + k * (log_term**2)


def fischer_model(t, a, b, c):
    """Fischer Lactation curve model
    Input variables:
        t = time since calving in days (DIM)
        a,b,c,d,k = parameters Wood model (numerical)

    Output: milk yield at time t
    """
    return a - b * t - a * np.exp(-c * t)


def brody_model(t, a, k):
    """Brody Lactation curve model
    Input variables:
        t = time since calving in days (DIM)
        a,k = parameters Brody model (numerical)

    Output: milk yield at time t
    """
    return a * np.exp(-k * t)


def sikka_model(t, a, b, c):
    """Sikka Lactation curve model
    Input variables:
    t = time since calving in days (DIM)
    a,b,c= parameters Sikka model (numerical)

    Output: milk yield at time t
    """
    return a * np.exp(b * t - c * t**2)


def nelder_model(t, a, b, c):
    """Nelder Lactation curve model
    Input variables:
    t = time since calving in days (DIM)
    a,b,c= parameters Nelder model (numerical)

    Output: milk yield at time t
    """
    return t / (a + b * t + c * t**2)


def dhanoa_model(t, a, b, c):
    """Dhanoa Lactation curve model
    Input variables:
    t = time since calving in days (DIM)
    a,b,c= parameters Dhanoa model (numerical)

    Output: milk yield at time t
    """
    return a * t ** (b * c) * np.exp(-c * t)


def emmans_model(t, a, b, c, d):
    """Emmans Lactation curve model
    Input variables:
    t = time since calving in days (DIM)
    a,b,c,d = parameters Emmans model (numerical)

    Output: milk yield at time t
    """
    return a * np.exp(-np.exp(d - b * t)) * np.exp(-c * t)


def hayashi_model(t, a, b, c, d):
    """Hayashi Lactation curve model
    Input variables:
    t = time since calving in days (DIM)
    a,b,c,d = parameters Hayashi model (numerical)

    Output: milk yield at time t
    """
    return b * (np.exp(-t / c) - np.exp(-t / (a * c)))


def rook_model(t, a, b, c, d):
    """Rook Lactation curve model
    Input variables:
    t = time since calving in days (DIM)
    a,b,c,d = parameters Rook model (numerical)

    Output: milk yield at time t
    """
    return a * (1 / (1 + b / (c + t))) * np.exp(-d * t)


def dijkstra_model(t, a, b, c, d):
    """Dijkstra Lactation curve model
    Input variables:
    t = time since calving in days (DIM)
    a,b,c,d = parameters Dijkstra model (numerical)

    Output: milk yield at time t
    """
    return a * np.exp((b * (1 - np.exp(-c * t)) / c) - d * t)


def prasad_model(t, a, b, c, d):
    """Prasad Lactation curve model
    Input variables:
    t = time since calving in days (DIM)
    a,b,c,d = parameters Prasad model (numerical)

    Output: milk yield at time t
    """
    return a + b * t + c * t**2 + d / t


# objectives for minimize
def wood_objective(par, x, y):
    return np.sum((y - wood_model(x, *par)) ** 2)


def milkbot_objective(par, x, y):
    return np.sum((y - milkbot_model(x, *par)) ** 2)


def milkbot_constraint(par, dim):
    a, b, c, d = par
    preds = milkbot_model(dim, a, b, c, d)
    return np.min(preds)


def residuals_milkbot(par, x, y):
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
    """Fit lactation data to a lactation curve model using sklearn minimize or curvefit or the MilkBot Bayesian fitting API
    Input variables:
    dim (Int) = list of dim
    milkrecordings (Float) = list of milk recordings
    model (Str)= type of pre-defined model function, default = Wood model. Model name is all lowercase
    fitting (Str) = method of fitting the data to the curve using optimalization either frequentist(curvefit/minimize) or Bayesian, default is frequentist. In the current version only for the MilkBot model Bayesian fitting is available.

    Only relevant if fitting is Bayesian
        breed (Str): either H or J, H = Holstein and is the default, J = Jersey
        Parity (Int): lactionnumber, default = 3, all parities >= 3 are considered as one group
        Continent (Str): source of the default priors, can be USA (default), EU or from Chen et al.
        key (Str): key for the milkbot API  Mandatory to use fitting API. For a free API Key, contact Jim Ehrlich jehrlich@MilkBot.com

    Output (list of floats): list of milk yield for range 1-305 or until the maximum day in milk when this is more than 305"""

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
    """Fit lactation data to a lactation curve model and return the model parameters using least square estimation and frequentist statistics.
    Input variables:
    dim (int) = list of dim
    milkrecordings (float) = list of milk recordings
    model (str) = type of pre-defined model function, default = Wood model. Model name is all lowercase

    output: parameters as np.float in alphabetic order"""
    # check and prep input
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

    # ------------------------------
    # Debug / quality info
    # ------------------------------
    print("success:", res.success)
    print("message:", res.message)
    print("params:", a_mb, b_mb, c_mb, d_mb)
    print("f(0) =", milkbot_model(0, a_mb, b_mb, c_mb, d_mb))
    print("predicted peak:", np.max(milkbot_model(dim, a_mb, b_mb, c_mb, d_mb)))
    print("measured max:", np.max(milkrecordings))

    return a_mb, b_mb, c_mb, d_mb


def get_lc_parameters(dim, milkrecordings, model="wood"):
    """Fit lactation data to a lactation curve model and return the model parameters using frequetist statistics: sklearn minimize and curvefit
    Input variables:
    dim (int) = list of dim
    milkrecordings (float) = list of milk recordings
    model (str) = type of pre-defined model function, default = Wood model. Model name is all lowercase

    output: parameters as np.float in alphabetic order"""
    # check and prepare input
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
        mb_guess = [max(milkrecordings), 50.0, 30.0, 0.01]
        mb_bounds = [(1, 100), (1, 100), (-600, 300), (0.0001, 0.1)]
        # constraint = {
        # 'type': 'ineq',
        # 'fun': lambda p: milkbot_constraint(p, dim)
        # }
        mb_res = minimize(milkbot_objective, mb_guess, args=(dim, milkrecordings), bounds=mb_bounds)
        #   constraints = constraint, method='SLSQP')
        a_mb, b_mb, c_mb, d_mb = mb_res.x
        return a_mb, b_mb, c_mb, d_mb


def get_chen_priors(parity: int) -> dict:
    """
    Return Chen et al. priors in MilkBot v2.0 ND format.
    """
    if parity == 1:
        return {
            "scale": {"mean": 34.11, "sd": 6.891},
            "ramp": {"mean": 29.96, "sd": 1.53},
            "decay": {"mean": 0.001835, "sd": 0.000738},
            "offset": {"mean": -0.5, "sd": 0.002},
            "seMilk": 1.91,
            "milkUnit": "kg",
        }

    if parity == 2:
        return {
            "scale": {"mean": 44.26, "sd": 9.57},
            "ramp": {"mean": 22.52, "sd": 0.9999},
            "decay": {"mean": 0.002745, "sd": 0.000979},
            "offset": {"mean": -0.78, "sd": 0.007},
            "seMilk": 2.19,
            "milkUnit": "kg",
        }

    # parity >= 3
    return {
        "scale": {"mean": 48.41, "sd": 10.66},
        "ramp": {"mean": 22.54, "sd": 8.724},
        "decay": {"mean": 0.002997, "sd": 0.000972},
        "offset": {"mean": 0.0, "sd": 0.03},
        "seMilk": 2.14,
        "milkUnit": "kg",
    }


def bayesian_fit_milkbot_single_lactation(
    dim, milkrecordings, key: str, parity=3, breed="H", continent="USA"
) -> dict:
    """
    Fit a single lactation using the MilkBot API (v2.0).

    continent:
        - "USA"   → MilkBot USA priors
        - "EU"    → MilkBot EU priors
        - "CHEN"  → Chen et al. published priors
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
            "fitEngine": "AnnealingFitter@2.0",
            "fitObjective": "MB2@1.0",
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
