# %% md
# In this code the LCCs of most important models are computed
#
# Updated 11-28-2025 to make it much faster
# %%
import numpy as np
from numpy import ndarray
from sympy import (
    diff,
    exp,
    integrate,
    lambdify,
    ln,
    log,
    nan,
    oo,
    simplify,
    solve,
    symbols,
    zoo,
)

from lactationcurve.fitting import (
    bayesian_fit_milkbot_single_lactation,
    fit_lactation_curve,
    get_lc_parameters,
)
from lactationcurve.preprocessing import validate_and_prepare_inputs


# safe guard for extreme expressions or weird results
def is_valid_sympy_expr(expr):
    """Return True if expr looks safe to lambdify."""
    try:
        if expr.has(oo, -oo, zoo, nan):
            return False
        # reject absurdly large expressions
        if expr.count_ops() > 5000:
            return False
        return True
    except Exception:
        return False


# Store derived function in cache so they do not need to be calculated all the time again.
_LCC_CACHE = {}


def lactation_curve_characteristic_function(
    model="wood", characteristic=None, lactation_length=305
):
    """Formula to extract lactation curve characteristics from the different mathematical models
       Return a precomputed symbolic expression and a fast numeric function for a lactation curve
        characteristic: time_to_peak, peak_yield, or cumulative_milk_yield.

        The symbolic derivation and integration are done only once per model/characteristic
        and then cached.
     Input:
      model (Str): type of model you wish to extract characteristics from. Options: milkbot, wood, wilmink, ali_schaeffer, fischer, brody, sikka, nelder, dhanoa, emmans, hayashi, rook, dijkstra, prasad.
      characteristic (Str): characteristic you wish to extract, options are time_to_peak, peak_yield (both based on where the derivate of the function equals zero) and cumulative_milk_yield (based on the integral over 305 days).
      lactation_length (Int): length of the lactation in days to calculate persistency over (default 305)

    Returns:
     expr: SymPy expression for the characteristic
     params: tuple of SymPy parameter symbols in argument order
     func: lambdified numeric function f(*params)"""

    # check the cache
    storage = (model, characteristic)
    if storage in _LCC_CACHE:
        return (
            _LCC_CACHE[storage]["expr"],
            _LCC_CACHE[storage]["params"],
            _LCC_CACHE[storage]["func"],
        )

    # make sure model is all lowercase
    model = model.lower()

    # define functions
    if model == "brody":
        # === BRODY 1 ===
        a, b, k1, k2, t = symbols("a b k1 k2 t", real=True, positive=True)
        function = a * exp(-k1 * t) - b * exp(-k2 * t)

    elif model == "sikka":
        # === SIKKA ===
        a, b, c, t = symbols("a b c t", real=True, positive=True)
        function = a * exp(b * t - c * t**2)

    elif model == "fischer":
        # === FISCHER ===
        a, b, c, t = symbols("a b c t", real=True, positive=True)
        function = a - b * t - a * exp(-c * t)

    elif model == "nelder":
        # === NELDER ===
        a, b, c, t = symbols("a b c t", real=True, positive=True)
        function = t / (a + b * t + c * t**2)

    elif model == "wood":
        # === WOOD ===
        a, b, c, t = symbols("a b c t", real=True, positive=True)
        function = a * t**b * exp(-c * t)

    elif model == "dhanoa":
        # === DHANOA ===
        a, b, c, t = symbols("a b c t", real=True, positive=True)
        function = a * t ** (b * c) * exp(-c * t)

    elif model == "emmans":
        # === EMMANS ===
        a, b, c, d, t = symbols("a b c d t")
        function = a * exp(-exp(d - b * t)) * exp(-c * t)

    elif model == "ali_schaeffer":
        # ====ALI=====
        a, b, c, d, k, t = symbols("a b c d k t", real=True, positive=True)
        function = (
            a + b * (t / 340) + c * (t / 340) ** 2 + d * log(t / 340) + k * log((340 / t) ** 2)
        )

    elif model == "wilmink":
        # === WILMINK ===
        a, b, c, k, t = symbols("a b c k t", real=True, positive=True)
        function = a + b * t + c * exp(-k * t)

    elif model == "hayashi":
        # === HAYASHI ===
        a, b, c, d, t = symbols("a b c d t", real=True, positive=True)
        function = b * (exp(-t / c) - exp(-t / (a * c)))

    elif model == "rook":
        # === ROOK ===
        a, b, c, d, t = symbols("a b c d t", real=True, positive=True)
        function = a * (1 / (1 + b / (c + t))) * exp(-d * t)

    elif model == "dijkstra":
        # === DIJKSTRA ===
        a, b, c, d, t = symbols("a b c d t", real=True, positive=True)
        function = a * exp((b * (1 - exp(-c * t)) / c) - d * t)

    elif model == "prasad":
        # === PRASAD ===
        a, b, c, d, t = symbols("a b c d t", real=True, positive=True)
        function = a + b * t + c * t**2 + d / t

    elif model == "milkbot":
        # === MILKBOT ===
        a, b, c, d, t = symbols("a b c d t", real=True, positive=True)
        function = a * (1 - exp((c - t) / b) / 2) * exp(-d * t)

    else:
        raise Exception("Unknown model")

    # find derivative
    fdiff = diff(function, t)
    # solve derivative for when it is zero to find the function for time of peak
    tpeak = solve(fdiff, t)

    # define the end of lactation
    T = lactation_length  # days in milk

    # Persistency = average slope after peak, does not work for all models so therefore try except
    persistency = None

    try:
        if tpeak:
            tmp = (function.subs(t, T) - function.subs(t, tpeak[0])) / (T - tpeak[0])

            tmp = tmp.cancel()  # light simplification
            if is_valid_sympy_expr(tmp):
                persistency = tmp
    except Exception:
        persistency = None

    if characteristic != "cumulative_milk_yield":
        if tpeak:  # Check if the list is not empty
            peak_expr = simplify(function.subs(t, tpeak[0]))
        else:
            raise Exception("No positive real solution for time to peak and peak yield found")

    # find function for cummulative milk yield over the first 305 days of the lactation
    cum_my_expr = integrate(function, (t, 0, 305))

    # Sorted parameter list (exclude t)
    params = tuple(
        sorted([s for s in function.free_symbols if s.name != "t"], key=lambda x: x.name)
    )

    # ----------------------------------------------------
    # Select requested characteristic
    # ----------------------------------------------------
    if characteristic == "time_to_peak":
        expr = tpeak[0]
    elif characteristic == "peak_yield":
        expr = peak_expr
    elif characteristic == "cumulative_milk_yield":
        expr = cum_my_expr
    elif characteristic == "persistency":
        if persistency is None:
            raise Exception("Persistency could not be computed symbolically")
        expr = persistency
    else:
        # Return all four if None or 'all'
        expr = {
            "time_to_peak": tpeak[0],
            "peak_yield": peak_expr,
            "persistency": persistency,  # possibly None
            "cumulative_milk_yield": cum_my_expr,
        }

    # ----------------------------------------------------
    # Build fast numeric function with lambdify
    # ----------------------------------------------------
    if isinstance(expr, dict):
        func = {
            name: lambdify(params, ex, modules=["numpy", "scipy"])
            for name, ex in expr.items()
            if ex is not None
        }
    else:
        func = lambdify(params, expr, modules=["numpy", "scipy"])

    # ----------------------------------------------------
    # Store in cache
    # ----------------------------------------------------
    _LCC_CACHE[storage] = {"expr": expr, "params": params, "func": func}

    return expr, params, func


def calculate_characteristic(
    dim,
    milkrecordings,
    model="wood",
    characteristic="cumulative_milk_yield",
    fitting="frequentist",
    key=None,
    parity=3,
    breed="H",
    continent="USA",
    persistency_method="derived",
    lactation_length=305,
):
    """Evaluate a lactation curve characteristic from a set of milkrecordings.

    Inputs:
        dim (Int): days in milk
        milkrecordings (Float): milk recording of the test day in kg
        characteristic (String): characteristic you want to calculate, choose between time_to_peak, peak_yield_cumulative_milk_yield.
        fitting (String): way of fitting the data, options: 'frequentist' or 'Bayesian'.

        Extra input for Bayesian fitting:
        key (String): key to use the fitting API
        parity (Int): parity of the cow, all above 3 are considered 3
        breed (String): breed of the cow H = Holstein, J = Jersey
        continent (String): continent of the cow, options USA, EU and defined by Chen et al.

        Extra input for persistency calculation:
        persistency_method (String): way of calculating persistency, options: 'derived' which gives the average slope of the lactation after the peak until the end of lactation (default) or 'literature' for the wood and milkbot model.
        Lactation_length: string or int: length of the lactation in days to calculate persistency over, options: 305 = default or 'max'  uses the maximum DIM in the data, or an integer value to set the desired lactation length.

        output: float of desired characteristic
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
        persistency_method=persistency_method,
        lactation_length=lactation_length,
    )

    dim: ndarray = inputs.dim
    milkrecordings: ndarray = inputs.milkrecordings
    model: str | None = inputs.model
    fitting: str | None = inputs.fitting
    breed: str | None = inputs.breed
    parity: int | None = inputs.parity
    continent: str | None = inputs.continent
    persistency_method: str | None = inputs.persistency_method
    lactation_length: int | str | None = inputs.lactation_length

    if model not in ["milkbot", "wood", "wilmink", "ali_schaeffer", "fischer"]:
        raise Exception(
            "this function currently only works for the milkbot, wood, wilmink, ali_schaeffer and fischer models"
        )

    characteristic_options: list[str] = [
        "time_to_peak",
        "peak_yield",
        "cumulative_milk_yield",
        "persistency",
    ]

    if characteristic in characteristic_options:
        if fitting == "frequentist":
            # Get fitted parameters from your fitting function
            fitted_params = get_lc_parameters(dim, milkrecordings, model)

            if characteristic != "persistency":
                # Try symbolic formula first
                expr, params, fn = lactation_curve_characteristic_function(
                    model, characteristic, lactation_length
                )
                with np.errstate(
                    divide="ignore", invalid="ignore"
                ):  # get rd of warnings for invalid operations
                    value = fn(*fitted_params)

                # If symbolic formula fails or is invalid (use numeric approach)
                if (
                    value is None
                    or not np.isfinite(value)
                    or (characteristic == "time_to_peak" and value <= 0)
                ):
                    if characteristic == "time_to_peak":
                        value = numeric_time_to_peak(
                            dim,
                            milkrecordings,
                            model,
                            fitting=fitting,
                            key=key,
                            parity=parity,
                            breed=breed,
                            continent=continent,
                        )
                    elif characteristic == "peak_yield":
                        value = numeric_peak_yield(
                            dim,
                            milkrecordings,
                            model,
                            fitting=fitting,
                            key=key,
                            parity=parity,
                            breed=breed,
                            continent=continent,
                        )
                    elif characteristic == "cumulative_milk_yield":
                        value = numeric_cumulative_yield(
                            dim,
                            milkrecordings,
                            model,
                            fitting=fitting,
                            lactation_length=lactation_length,
                            key=key,
                            parity=parity,
                            breed=breed,
                            continent=continent,
                        )

            else:
                if persistency_method == "derived":
                    # find lactation length from data
                    if lactation_length == "max":
                        lactation_length = max(dim)
                    elif isinstance(lactation_length, int):
                        lactation_length = lactation_length
                    else:
                        lactation_length = 305
                    value = persistency_fitted_curve(
                        dim,
                        milkrecordings,
                        model,
                        fitting="frequentist",
                        lactation_length=lactation_length,
                    )

                else:
                    if model == "wood":
                        value = persistency_wood(fitted_params[1], fitted_params[2])

                    elif model == "milkbot":
                        value = persistency_milkbot(fitted_params[3])

                    else:
                        raise Exception(
                            'Currently only the Wood model and MilkBot model have a separate model function from the literature integrated for persistency. if persistency="derived" is selected, persistency can be calculated for every model as the average slope of the lactation after the peak.'
                        )
            try:
                return float(value)
            except ValueError:
                raise Exception(
                    "Could not compute characteristic, possibly due to invalid fitted parameters"
                )

        else:
            if model == "milkbot":
                if key is None:
                    raise Exception("Key needed to use Bayesian fitting engine MilkBot")
                else:
                    fitted_params_bayes = bayesian_fit_milkbot_single_lactation(
                        dim, milkrecordings, key, parity, breed, continent
                    )
                    fitted_params_bayes = (
                        fitted_params_bayes["scale"],
                        fitted_params_bayes["ramp"],
                        fitted_params_bayes["offset"],
                        fitted_params_bayes["decay"],
                    )

                    if characteristic != "persistency":
                        # Get the symbolic expression and model parameters
                        expr, param_symbols, fn = lactation_curve_characteristic_function(
                            model, characteristic
                        )
                        value = fn(*fitted_params_bayes)

                    else:
                        if persistency_method == "derived":
                            # find lactation length from data
                            if lactation_length == "max":
                                lactation_length = max(dim)
                            elif isinstance(lactation_length, int):
                                lactation_length = lactation_length
                            else:
                                lactation_length = 305
                            value = persistency_fitted_curve(
                                dim,
                                milkrecordings,
                                model,
                                fitting="bayesian",
                                key=key,
                                parity=parity,
                                breed=breed,
                                continent=continent,
                                lactation_length=lactation_length,
                            )

                        else:
                            value = persistency_milkbot(fitted_params_bayes[3])

                    return float(value)
            else:
                raise Exception("Bayesian fitting is currently only implemented for MilkBot models")

    else:
        raise Exception("Unknown characteristic")


# also define numeric approaches as back up if symbolic functions fail or throw invalid results
def numeric_time_to_peak(
    dim,
    milkrecordings,
    model,
    fitting="frequentist",
    key=None,
    parity=3,
    breed="H",
    continent="USA",
) -> int:
    # Fit the curve to get predicted milk yields
    yields = fit_lactation_curve(
        dim,
        milkrecordings,
        model,
        fitting=fitting,
        key=key,
        parity=parity,
        breed=breed,
        continent=continent,
    )
    # Find the index of the peak yield
    peak_idx = np.argmax(yields)
    # Return the corresponding DIM
    return int(peak_idx + 1)  # +1 because DIM starts at 1, not 0


def numeric_cumulative_yield(
    dim, milkrecordings, model, fitting="frequentist", lactation_length=305, **kwargs
) -> float:
    y = fit_lactation_curve(dim, milkrecordings, model, fitting=fitting, **kwargs)
    return np.trapezoid(y[:lactation_length], dx=1)


def numeric_peak_yield(
    dim,
    milkrecordings,
    model,
    fitting="frequentist",
    key=None,
    parity=3,
    breed="H",
    continent="USA",
) -> float:
    # Fit the curve to get predicted milk yields
    yields = fit_lactation_curve(
        dim,
        milkrecordings,
        model,
        fitting=fitting,
        key=key,
        parity=parity,
        breed=breed,
        continent=continent,
    )
    # Find the peak yield
    peak_yield = np.max(yields)
    return peak_yield


def persistency_wood(b, c) -> float:
    """Calculate persistency based on Wood et al. (1984) formula: Persistency = -(b+1) * ln(c)
    Inputs:
        b (Float): parameter b of the Wood model
        c (Float): parameter c of the Wood model
    Outputs:
        persistency (Float): persistency value based on Wood et al. (1984) formula
    """
    return float(-(b + 1) * ln(c))


def persistency_milkbot(d) -> float:
    """Calculate persistency based on the MilkBot model formula from the original paper of Ehrlich (2013)
    Inputs:
        d (Float): parameter d of the MilkBot model
    Outputs:
        persistency (Float): persistency value based on MilkBot model formula
    """
    return 0.693 / d


def persistency_fitted_curve(
    dim,
    milkrecordings,
    model,
    fitting="frequentist",
    key=None,
    parity=3,
    breed="H",
    continent="USA",
    lactation_length=305,
) -> float:
    """Calculate persistency as the average slope of the lactation curve after the peak until the end of lactation. Numerical approach based on fitted curve. This is the default way of calculating persistency as symbolic derivation is not possible for all models.
    Inputs:
        dim (Int): days in milk
        milkrecordings (Float): milk recording of the test day in kg
        model (String): type of model you wish to extract characteristics from. Options: milkbot (both baysian and frequentist), wood, wilmink, ali_schaeffer and fischer
        fitting (String): way of fitting the data, options: 'frequentist' or 'Bayesian'.
        key (String): key to use the fitting API (only for Bayesian fitting)
        parity (Int): parity of the cow, all above 3 are considered 3 (only for Bayesian fitting)
        breed (String): breed of the cow H = Holstein, J = Jersey (only for Bayesian fitting)
        continent (String): continent of the cow, options USA, EU and defined by Chen et al. (only for Bayesian fitting)
        lactation_length (Int or String): length of the lactation in days to calculate persistency over, options: 305 = default or 'max'  uses the maximum DIM in the data, or an integer value to set the desired lactation length.
    Outputs:
        persistency (Float): average slope of the lactation curve after the peak until the end of lactation.
    """
    # calculate time to peak
    t_peak = numeric_time_to_peak(
        dim,
        milkrecordings,
        model,
        fitting=fitting,
        key=key,
        parity=parity,
        breed=breed,
        continent=continent,
    )

    # determine lactation length
    if lactation_length == "max":
        lactation_length = max(dim)
    elif isinstance(lactation_length, int):
        lactation_length = lactation_length
    else:
        lactation_length = 305

    # calculate milk yield at peak
    yields = fit_lactation_curve(
        dim,
        milkrecordings,
        model,
        fitting=fitting,
        key=key,
        parity=parity,
        breed=breed,
        continent=continent,
    )
    peak_yield = yields[int(t_peak) - 1]  # -1 to prevent index error
    # calculate milk yield at end of lactation
    end_yield = yields[int(lactation_length) - 1]  # -1 to prevent index error

    # calculate persistency
    persistency = (end_yield - peak_yield) / (lactation_length - t_peak)
    return persistency


# test
# import pandas as pd
# from key_milkbot import milkbot_key
# key = milkbot_key()
# df = pd.read_csv('C:\\Users\\Meike van Leerdam\\lactation-curves\\lactationcurve_package\\lactationcurve\\tests\\test_data\\l2_anim2_herd654.csv', sep =',')
# df= df.rename(columns={'TestDayMilkYield':'MilkingYield'})

# dim = df.DaysInMilk.values
# my = df.MilkingYield.values


# dim = [10,20,30]
# y = [20,35,40]

# test = persistency_fitted_curve(dim, y, model="milkbot", fitting="frequentist")
# print(test)

# print(calculate_characteristic(dim, y, model = 'MilkBot', fitting="frequentist", characteristic = 'persistency'))
# print(calculate_characteristic(
#         dim,
#         y,
#         model = 'wood',
#         characteristic = 'persistency',
#         fitting='frequentist',
#         persistency_method = 'derived'))
# dy_mb = calculate_characteristic(dim, my, model="wood", characteristic="peak_yield", persistency_method="derived", lactation_length=305)

# # loop through all characteristics for each model to see if any errors occur
# models = ['milkbot', 'wood', 'wilmink', 'ali_schaeffer', 'fischer']
# characteristics = ['time_to_peak', 'peak_yield', 'cumulative_milk_yield', 'persistency']

# for model in models:
#     for characteristic in characteristics:
#         try:
#             result = calculate_characteristic(dim, my, model=model, characteristic=characteristic, persistency_method="derived", lactation_length=200)
#             print(f'Model: {model}, Characteristic: {characteristic}, Result: {result}')
#         except Exception as e:
#             print(f'Error for Model: {model}, Characteristic: {characteristic}: {e}')


# for characteristic in characteristics:
#     try:
#         result = calculate_characteristic(dim, my, model='milkbot', fitting = 'bayesian', characteristic=characteristic, key = key, persistency_method="derived", lactation_length=200)
#         print(f'Characteristic: {characteristic}, Result: {result}')
#     except Exception as e:
#         print(f'Error for Model: bayesian milkbot, Characteristic: {characteristic}: {e}')


# %%
