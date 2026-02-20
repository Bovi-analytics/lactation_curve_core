import math
from pathlib import Path

import pandas as pd
import pytest
import sympy as sp

from lactationcurve.characteristics import (
    calculate_characteristic,
    lactation_curve_characteristic_function,
    numeric_cumulative_yield,
    numeric_peak_yield,
    numeric_time_to_peak,
    persistency_fitted_curve,
    persistency_milkbot,
    persistency_wood,
)


@pytest.fixture
def test_df():
    data_path = Path(__file__).parent.parent / "test_data" / "l2_anim2_herd654.csv"
    df = pd.read_csv(data_path, sep=",")
    dim = df.DaysInMilk.values
    my = df.TestDayMilkYield.values
    return dim, my


# tests for the lactation_curve_characteristic_function
def test_invalid_model_raises():
    with pytest.raises(Exception, match="Unknown model"):
        lactation_curve_characteristic_function(model="not_a_model")


def test_wood_time_to_peak_returns_expr_params_and_func():
    expr, params, func = lactation_curve_characteristic_function(
        model="wood", characteristic="time_to_peak"
    )
    assert isinstance(expr, sp.Expr)
    assert all(isinstance(s, sp.Symbol) for s in params)
    assert {s.name for s in params} == {"a", "b", "c"}
    assert callable(func)


def test_wood_peak_yield_returns_expr_params_and_func():
    expr, params, func = lactation_curve_characteristic_function(
        model="wood", characteristic="peak_yield"
    )
    assert isinstance(expr, sp.Expr)
    assert {s.name for s in params} == {"a", "b", "c"}
    assert callable(func)


def test_wood_cumulative_returns_expr_params_and_func():
    expr, params, func = lactation_curve_characteristic_function(
        model="wood", characteristic="cumulative_milk_yield"
    )
    assert isinstance(expr, sp.Expr)
    assert {s.name for s in params} == {"a", "b", "c"}
    assert callable(func)


def test_default_returns_dict_with_all_four():
    result, params, func = lactation_curve_characteristic_function(model="wood")
    assert isinstance(result, dict)
    assert set(result.keys()) == {
        "time_to_peak",
        "peak_yield",
        "cumulative_milk_yield",
        "persistency",
    }
    assert all(isinstance(v, (sp.Expr, type(None))) for v in result.values())
    assert {s.name for s in params} == {"a", "b", "c"}
    assert isinstance(func, dict)
    assert callable(list(func.values())[0])


def test_brody_cumulative_returns_expr_params_and_func():
    expr, params, func = lactation_curve_characteristic_function(
        "brody", characteristic="cumulative_milk_yield"
    )
    assert isinstance(expr, sp.Expr)
    assert {s.name for s in params} == {"a", "b", "k1", "k2"}
    assert callable(func)


@pytest.mark.parametrize(
    "model,expected_symbols",
    [
        ("sikka", {"a", "b", "c"}),
        ("wilmink", {"a", "b", "c", "k"}),
        ("ali_schaeffer", {"a", "b", "c", "d", "k"}),
    ],
)
def test_models_return_expected_symbols(model, expected_symbols):
    _, params, func = lactation_curve_characteristic_function(
        model=model, characteristic="time_to_peak"
    )
    assert {s.name for s in params} == expected_symbols
    assert callable(func)


# tests for persistency functions
def test_persistency_wood_basic():
    # known input/output check
    result = persistency_wood(2, 0.5)
    expected = -(2 + 1) * math.log(0.5)  # = -3 * ln(0.5)
    assert pytest.approx(result, rel=1e-9) == expected


def test_persistency_wood_type():
    result = persistency_wood(1, 0.8)
    assert isinstance(result, float)


def test_persistency_milkbot_basic():
    result = persistency_milkbot(2)
    expected = 0.693 / 2
    assert pytest.approx(result, rel=1e-9) == expected


def test_persistency_milkbot_type():
    result = persistency_milkbot(5)
    assert isinstance(result, float)


def test_persistency_milkbot_zero_division():
    with pytest.raises(ZeroDivisionError):
        persistency_milkbot(0)


# Tests for calculate_characteristic
# Frequentist fitting tests
def test_time_to_peak_frequentist_wood(test_df):
    dim, my = test_df
    result = calculate_characteristic(dim, my, model="wood", characteristic="time_to_peak")
    expected = 45
    assert isinstance(result, float)
    # sanity check: peak time should be within the lactation period
    assert 0 < result < 305
    # value check
    assert pytest.approx(result, abs=1) == expected


def test_peak_yield_frequentist_wood(test_df):
    dim, my = test_df
    result = calculate_characteristic(dim, my, model="wood", characteristic="peak_yield")
    expected = 46.40100132439492
    assert isinstance(result, float)
    assert result > 0  # milk yield should be positive
    assert pytest.approx(result, abs=1e-3) == expected


def test_cumulative_frequentist_wood(test_df):
    dim, my = test_df
    result = calculate_characteristic(dim, my, model="wood", characteristic="cumulative_milk_yield")
    expected = 10644.871485478427
    assert isinstance(result, float)
    assert result > 0  # cumulative yield must be positive
    assert pytest.approx(result, abs=2) == expected


def test_cumulative_frequentist_wood_with_lactation_length(test_df):
    dim, my = test_df
    result = calculate_characteristic(
        dim, my, model="wood", characteristic="cumulative_milk_yield", lactation_length=200
    )
    assert isinstance(result, float)
    assert result > 0  # cumulative yield must be positive


def test_persistency_frequentist_wood(test_df):
    dim, my = test_df
    result = calculate_characteristic(
        dim, my, model="wood", characteristic="persistency", persistency_method="literature"
    )
    assert isinstance(result, float)


def test_persistency_derived_wood(test_df):
    dim, my = test_df
    result = calculate_characteristic(
        dim, my, model="wood", characteristic="persistency", persistency_method="derived"
    )
    assert isinstance(result, float)


def test_persistency_derived_with_lactation_length(test_df):
    dim, my = test_df
    result = calculate_characteristic(
        dim,
        my,
        model="wood",
        characteristic="persistency",
        persistency_method="derived",
        lactation_length=200,
    )
    assert isinstance(result, float)


# Bayesian fitting tests
def test_time_to_peak_bayesian_milkbot(test_df, key):
    dim, my = test_df
    result = calculate_characteristic(
        dim, my, model="milkbot", characteristic="time_to_peak", fitting="Bayesian", key=key
    )
    expected = 38
    assert isinstance(result, float)
    assert 0 < result < 305
    assert (
        pytest.approx(result, abs=5) == expected
    )  # wider range due to the inherent randomness of Bayesian fitting


def test_peak_yield_bayesian_milkbot(test_df, key):
    dim, my = test_df
    result = calculate_characteristic(
        dim, my, model="milkbot", characteristic="peak_yield", fitting="Bayesian", key=key
    )
    expected = 48
    assert isinstance(result, float)
    assert result > 0
    assert (
        pytest.approx(result, abs=2) == expected
    )  # wider range due to the inherent randomness of Bayesian fitting


def test_cumulative_bayesian_milkbot(test_df, key):
    dim, my = test_df
    result = calculate_characteristic(
        dim,
        milkrecordings=my,
        model="milkbot",
        characteristic="cumulative_milk_yield",
        fitting="Bayesian",
        key=key,
    )
    expected = 10550
    assert isinstance(result, float)
    assert result > 0
    assert (
        pytest.approx(result, abs=50) == expected
    )  # wider range due to the inherent randomness of Bayesian fitting


def test_persistency_bayesian_milkbot(test_df, key):
    dim, my = test_df
    result = calculate_characteristic(
        dim,
        my,
        model="milkbot",
        characteristic="persistency",
        fitting="Bayesian",
        key=key,
        persistency_method="literature",
    )
    assert isinstance(result, float)


def test_persistency_derived_bayesian_milkbot(test_df, key):
    dim, my = test_df
    result = calculate_characteristic(
        dim,
        my,
        model="milkbot",
        characteristic="persistency",
        fitting="Bayesian",
        key=key,
        persistency_method="derived",
    )
    assert isinstance(result, float)


# Error handling
def test_invalid_characteristic_raises(test_df):
    dim, my = test_df
    with pytest.raises(Exception, match="Unknown characteristic"):
        calculate_characteristic(dim, my, model="wood", characteristic="foobar")


def test_invalid_model_in_calculate_characteristic_raises(test_df):
    dim, my = test_df
    with pytest.raises(Exception, match="currently only works for"):
        calculate_characteristic(dim, my, model="brody", characteristic="cumulative_milk_yield")


def test_bayesian_requires_key(test_df):
    dim, my = test_df
    with pytest.raises(Exception, match="Key needed"):
        calculate_characteristic(
            dim, my, model="milkbot", characteristic="time_to_peak", fitting="Bayesian"
        )


def test_bayesian_non_milkbot_raises(test_df, key):
    dim, my = test_df
    with pytest.raises(
        Exception, match="Bayesian fitting is currently only implemented for MilkBot"
    ):
        calculate_characteristic(
            dim, my, model="wood", characteristic="time_to_peak", fitting="Bayesian", key=key
        )


# Tests for numeric helper functions
def test_numeric_time_to_peak(test_df):
    dim, my = test_df
    result = numeric_time_to_peak(dim, my, model="wood")
    assert isinstance(result, (float, int))
    assert 0 < result < 305


def test_numeric_peak_yield(test_df):
    dim, my = test_df
    result = numeric_peak_yield(dim, my, model="wood")
    assert isinstance(result, (float, int))
    assert result > 0


def test_numeric_cumulative_yield(test_df):
    dim, my = test_df
    result = numeric_cumulative_yield(dim, my, model="wood")
    assert isinstance(result, (float, int))
    assert result > 0


def test_numeric_cumulative_yield_with_lactation_length(test_df):
    dim, my = test_df
    result = numeric_cumulative_yield(dim, my, model="wood", lactation_length=200)
    assert isinstance(result, (float, int))
    assert result > 0


# Tests for persistency_fitted_curve
def test_persistency_fitted_curve_wood(test_df):
    dim, my = test_df
    result = persistency_fitted_curve(dim, my, model="wood", fitting="frequentist")
    assert isinstance(result, (float, int))
