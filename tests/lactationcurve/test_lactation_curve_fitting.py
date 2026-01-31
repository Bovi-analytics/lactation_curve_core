# Tests: Functions for fitting of lactation curve models to lactation data
# Author: Lucia Trapanese, Date: 15-9-2025

import os

import numpy as np
import pytest
from dotenv import find_dotenv, load_dotenv

from lactationcurve.fitting import (
    ali_schaeffer_model,
    bayesian_fit_milkbot_single_lactation,
    brody_model,
    dhanoa_model,
    dijkstra_model,
    emmans_model,
    fischer_model,
    fit_lactation_curve,
    get_chen_priors,
    get_lc_parameters,
    hayashi_model,
    milkbot_model,
    nelder_model,
    prasad_model,
    rook_model,
    sikka_model,
    wilmink_model,
    wood_model,
)

load_dotenv(find_dotenv())


def milkbot_key() -> str:
    """Return the MilkBot API key from environment."""
    key = os.getenv("milkbot_key")
    if not key:
        raise ValueError("milkbot_key not found in environment. Check your .env file.")
    return key

# 1. Test on function models. Asses if each model return coherent values.


@pytest.mark.parametrize(
    "model, params",
    [
        (milkbot_model, (30, 50, 10, 0.01)),
        (wood_model, (20, 0.2, 0.01)),
        (wilmink_model, (30, 0.05, 5)),
        (ali_schaeffer_model, (10, 5, -2, 1, 0.5)),
        (fischer_model, (25, 0.01, 0.01)),
        (brody_model, (30, 0.01)),
        (sikka_model, (20, 0.01, 0.0001)),
        (nelder_model, (1, 0.1, 0.01)),
        (dhanoa_model, (10, 0.5, 0.01)),
        (emmans_model, (20, 0.1, 0.01, 2)),
        (hayashi_model, (2, 30, 10, 0.5)),
        (rook_model, (20, 1, 1, 0.01)),
        (dijkstra_model, (30, 0.1, 0.01, 0.01)),
        (prasad_model, (10, 0.1, 0.001, 5)),
    ],
)
def test_models_basic_output(model, params):
    """
    Test that each model produces a valid numpy array with finite values
    for a few sample DIM points.
    """
    t = np.array([1, 10, 100, 150, 200, 300])
    y = model(t, *params)
    assert isinstance(y, np.ndarray)
    assert np.all(np.isfinite(y))


# 2. Fitting tests for models with get_lc_parameters
def test_wood_fitting():
    true_params = (30, 0.2, 0.003)
    x = np.arange(1, 200)
    y = wood_model(x, *true_params)
    est_params = get_lc_parameters(x, y, model="wood")
    assert np.allclose(est_params, true_params, rtol=0.2)


def test_wilmink_fitting():
    true_params = (30, 0.1, 10, -0.05)
    x = np.arange(1, 200)
    y = wilmink_model(x, *true_params)
    est_params = get_lc_parameters(x, y, model="wilmink")
    assert np.allclose(est_params[:3], true_params[:3], rtol=0.2)


def test_ali_schaeffer_fitting():
    true_params = (25, 5, -2, 1, 0.5)
    x = np.arange(1, 200)
    y = ali_schaeffer_model(x, *true_params)
    est_params = get_lc_parameters(x, y, model="ali_schaeffer")
    assert np.allclose(est_params, true_params, rtol=0.3)


def test_fischer_fitting():
    true_params = (30, 0.01, 0.01)
    x = np.arange(1, 200)
    y = fischer_model(x, *true_params)
    est_params = get_lc_parameters(x, y, model="fischer")
    assert np.allclose(est_params, true_params, rtol=0.3)


def test_milkbot_fitting():
    true_params = (40, 30, 10, 0.005)
    x = np.arange(1, 200)
    y = milkbot_model(x, *true_params)
    est_params = get_lc_parameters(x, y, model="milkbot")
    assert np.allclose(est_params, true_params, rtol=0.5)


# 2.1 Edge cases for input
# It works for all models
def test_empty_input():
    with pytest.raises(ValueError):
        get_lc_parameters([], [], model="wilmink")


# 2.2 Add min points [Make sure that there are at least the number of points equal to the number of parameters - add lines 290 - 300]
# It works for all models
def test_single_point():
    x: list[int] = [1]
    y: list[int] = [10]
    with pytest.raises(ValueError):
        get_lc_parameters(x, y, model="Milkbot")


# 2.3 Ordered DIM
# It works for all models
def test_non_ordered_dim():
    x = [100, 1, 50, 10]
    y = [10, 30, 20, 15]
    est_params = get_lc_parameters(x, y, model="milkbot")
    assert np.all(np.isfinite(est_params))


# 2.4
# It works for all models
def test_negative_milk_values():
    x = np.arange(1, 10)
    y = np.array([-1, 0, 5, 10, -3, 7, 8, 9, 0])
    est_params = get_lc_parameters(x, y, model="wood")
    assert np.all(np.isfinite(est_params))


# 2.5
# It works for all models
def test_fitting_with_noise():
    x = np.arange(1, 200)
    y = wood_model(x, 30, 0.2, 0.003)
    y_noisy = y + np.random.normal(0, 0.5, size=y.shape)
    est_params = get_lc_parameters(x, y_noisy, model="MILKBOT")
    assert np.all(np.isfinite(est_params))


# 2.6
# test missing milk yields
def test_missing_yields_nan_in_y_is_dropped():
    x = [1.0, 10.0, 15.0, 20.0]
    y = [10.0, 15.0, np.nan, 25.0]

    result = get_lc_parameters(x, y)

    assert result is not None


# 2.7
# test missing days in milk


def test_missing_dim_nan_in_x_is_dropped():
    x = [1.0, np.nan, 15.0, 20.0]
    y = [10.0, 15.0, 20.0, 25.0]

    result = get_lc_parameters(x, y)

    assert result is not None


def test_all_values_nan_raises():
    x = [np.nan, np.nan]
    y = [np.nan, np.nan]

    with pytest.raises(
        ValueError, match="At least two non missing points are required to fit a lactation curve"
    ):
        get_lc_parameters(x, y)


def test_single_valid_point_raises():
    x = [1.0, np.nan, np.nan]
    y = [10.0, np.nan, np.nan]

    with pytest.raises(
        ValueError, match="At least two non missing points are required to fit a lactation curve"
    ):
        get_lc_parameters(x, y)


# 3 Tests for get_milkbot_data
# 3.1 milkbot key  - Asses if all works
def key() -> str:
    return milkbot_key()


def test_fit_lactation_curve_milkbot_real():
    dim = [1, 5, 10, 20, 50, 100, 150, 200, 250, 300]
    milkrecordings = [10, 12, 15, 18, 22, 25, 23, 20, 18, 15]

    y = fit_lactation_curve(
        dim,
        milkrecordings,
        model="milkbot",
        fitting="bayesian",
        key=milkbot_key(),
        parity=2,
        breed="H",
        continent="USA",
    )

    # Asses valid results
    assert isinstance(y, np.ndarray)
    assert np.all(np.isfinite(y))
    assert len(y) >= max(dim)


# 4. Tests for fit_lactation_curve

# The tests ensure that fit_lactation_curve raises a ValueError when an invalid model name is provided.
# Without this check, the function would silently return None,
# which could lead to confusing behavior or silent errors in downstream code.

# 4.1 Model


def test_invalid_model_name():
    dim = np.arange(1, 10)
    milkrecordings = np.random.uniform(20, 40, size=len(dim))

    with pytest.raises(Exception) as excinfo:
        fit_lactation_curve(dim, milkrecordings, model="nomodel")
    assert "Unknown model" in str(excinfo.value)


# 4.2 Breed
def test_invalid_breed():
    dim = np.arange(1, 200)
    milkrecordings = np.random.uniform(20, 40, size=len(dim))
    # Breed validation is performed in the Bayesian priors lookup
    with pytest.raises(Exception) as excinfo:
        fit_lactation_curve(
            dim, milkrecordings, model="milkbot", fitting="bayesian", key=milkbot_key(), breed="W"
        )
    assert "Breed must be either Holstein = 'H' or Jersey 'J'" in str(excinfo.value)


# 4.3 Continent
def test_invalid_continent():
    dim = np.arange(1, 10)
    milkrecordings = np.random.uniform(20, 40, size=len(dim))
    with pytest.raises(Exception) as excinfo:
        fit_lactation_curve(
            dim,
            milkrecordings,
            model="milkbot",
            fitting="bayesian",
            key=milkbot_key(),
            continent="EW",
        )
    assert "continent must be 'USA', 'EU', or 'CHEN'" in str(excinfo.value)


# 4.4 Fitting method


def test_invalid_model_raises_wrong_model_type():
    dim = np.arange(1, 10)
    milk = np.random.uniform(20, 40, size=len(dim))

    with pytest.raises(Exception) as excinfo:
        fit_lactation_curve(dim, milk, model="wood", fitting="")
    assert "Fitting method must be either frequentist or bayesian" in str(excinfo.value)


# 4.5  Non numeric output
def test_non_numeric_input():
    dim = ["a", "b", "c"]
    milkrecordings = ["x", "y", "z"]
    with pytest.raises(ValueError):
        fit_lactation_curve(dim, milkrecordings, model="wood")


# 4.6 bayesian fitting for models other then milkbot
def test_bayesian_fitting_non_milkbot():
    dim = np.arange(1, 10)
    milk = np.random.uniform(20, 40, size=len(dim))
    with pytest.raises(Exception) as excinfo:
        fit_lactation_curve(dim, milk, model="wood", fitting="bayesian")
    assert "Bayesian fitting is currently only implemented for milkbot models" in str(excinfo.value)


# 5. Tests for bayesian_fit_milkbot_single_lactation
# 5.1  Correctness of the function
def test_bayesian_output_structure():
    dim = [1, 5, 10, 20, 50]
    milkrecordings = [10, 12, 15, 18, 22]

    res = bayesian_fit_milkbot_single_lactation(dim, milkrecordings, milkbot_key())
    assert isinstance(res, dict)
    for key in ["scale", "ramp", "decay", "offset", "nPoints"]:
        assert key in res
        assert res[key] is not None


# 5.2 Unsorted DIM
def test_bayesian_unordered_dim():
    dim = [50, 1, 20, 5, 10]
    milkrecordings = [22, 10, 18, 12, 15]

    res = bayesian_fit_milkbot_single_lactation(dim, milkrecordings, milkbot_key())

    for key in ["scale", "ramp", "decay", "offset"]:
        assert isinstance(res[key], (float, int))


# 5.3  Min input
def test_bayesian_minimal_points():
    dim = [1, 5, 13, 67]
    milkrecordings = [10, 12, 15, 30]

    res = bayesian_fit_milkbot_single_lactation(dim, milkrecordings, milkbot_key())
    assert isinstance(res["scale"], float)


# 5.4 Missing Key
def test_bayesian_invalid_key():
    dim = [1, 5, 13, 67]
    milkrecordings = [10, 12, 15, 30]

    with pytest.raises(Exception):
        fit_lactation_curve(
            dim, milkrecordings, model="milkbot", fitting="bayesian", key="UNCORRECT KEY"
        )


# 6 Test for get_milkbot_priors
# 6.1 Correctness of the function
def test_get_priors_output_structure():
    priors = get_chen_priors(1)
    assert isinstance(priors, dict)
