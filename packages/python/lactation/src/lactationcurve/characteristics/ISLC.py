"""Interpolation using Standard Lactation Curves (ISLC).

This module implements the ISLC (Iterative Standard Lactation Curve)
method for estimating 305-day milk production from intermittent test-day
records. The implementation follows the CRV/ICAR approach based on Wilmink-
style standard lactation curves and correlation-based deviation corrections.

The main entry points are:
- ``ISLC_method``: compute a single lactation's estimated 305-d yield from
    interpolated grid measurements.
- ``ISLC``: apply ``ISLC_method`` per `TestId` in a pandas DataFrame.
- ``interpolation_standard_lc``: interpolate measured test-day yields onto
    the DIM grid using the standard lactation curve to guide slopes.
- ``linear_interpd_all_to_grid`` and ``linear_interpd_closest_to_grid``:
    alternative linear interpolation helpers.

Notes
-----
- This method only uses milksamples from days of the grid. 
    As milk samples are taken on random DIM, these measurements need to be interpolated to the grid days.
    There are three different ways implemented to do interpolation. 
    We recommend interpolation_standard_lc as it is most consistent with the original method.
    Interpolation_standard_lc require that you provide a standard lactation curve first. 
    You could use the lactation curve package to fit a curve to your data and use this as your standard lactationcurve


Author: Meike
Date: 20 October 2025
Added: 03 March 2026
"""

# Import packages
from pandas.core.frame import DataFrame
from pandas.core.frame import DataFrame
from typing import Protocol
import numpy as np
from scipy.interpolate import interp1d
import pandas as pd
import numpy.typing as npt

from lactationcurve.fitting import fit_lactation_curve


#get the standard lactation curve ingredients back from the data storage: 
# CORR_MATRIX = pd.read_pickle( "data/corr_matrix.pkl")
CORR_MATRIX = pd.read_pickle( "packages/python/lactation/src/lactationcurve/characteristics/data/corr_matrix.pkl")
STDs = np.load( "packages/python/lactation/src/lactationcurve/characteristics/data/std_per_grid_day.npy")
STANDARD_CURVE = np.load("packages/python/lactation/src/lactationcurve/characteristics/data/standard_lc_grid.npy")


class InterpolationMethod(Protocol):
    """Protocol for milk-yield interpolation methods.

    Defines the signature expected by functions that interpolate test-day
    yields onto a predefined DIM grid.
    """

    def __call__(
        self,
        group: pd.DataFrame,
        column_name_dim: str,
        column_name_milk_yield: str,
        standard_lc: pd.Series | None = None,
    ) -> pd.DataFrame:
        """Interpolate yields for a single lactation onto the DIM grid.

        Args:
            group: Test-day records for a single animal.
            column_name_dim: Column name containing days in milk (DIM).
            column_name_milk_yield: Column name containing milk yields.
            standard_lc: Optional standard lactation curve to guide
                interpolation (method-dependent).

        Returns:
            A DataFrame with interpolated yields, typically including
            columns ``GridDay`` and ``MilkYieldInterp``.
        """
        ...


# the amount of estimations of milk yields depends on the availibility of measured milk yields
# lactation yield is sum(known measurements (p) + estimated measurements (q))

def ISLC_method(
    df: pd.DataFrame,
    standard_lc: npt.NDArray[np.float64],
    correlation_matrix: pd.DataFrame,
    std_per_grid_day: npt.NDArray[np.float64],
) -> float:
    """Estimate 305-day milk yield for a single interpolated lactation.

    This function computes an estimated 305-day yield by combining three
    components: known production from interpolated measurements, the
    population mean for missing grid days (from ``standard_lc``), and a
    correlation-based deviation correction derived from ``correlation_matrix``.

    Args:
        df: DataFrame containing at least the columns ``GridDay`` and
            ``MilkYieldInterp`` (values already interpolated onto the grid).
        standard_lc: Standard lactation curve values indexed by grid day.
        correlation_matrix: Correlation coefficients between grid-day yields
            (matrix-like, rows/columns ordered as the grid).
        std_per_grid_day: 1-D array of standard deviations for each grid day.

    Returns:
        A float with the estimated 305-day milk yield.

    Raises:
        ValueError: if any measured day in ``df`` is not present in the
            expected global ``grid``.

    Notes:
        - The routine assumes fixed recording intervals of 20 days, except
          that the final interval (if day 290 is present) is 25 days.
        - The implementation expects a global ``grid`` variable to be
          defined and aligned with ``standard_lc`` and
          ``std_per_grid_day``.
    """
    # define the grid
    grid = [10, 30, 50, 70, 90, 110, 130, 150, 170, 190, 210, 230, 250, 270, 290]

    # --- Validate that all measurements lie on the expected grid -------
    measured_days = df["GridDay"].values
    if any(day not in grid for day in measured_days):
        raise ValueError("At least one DIM in the input df is not part of the grid.")

    # --- Prepare basic components -------------------------------------
    df = df.sort_values("GridDay")

    # days missing from measurement → need prediction
    days_to_predict = [day for day in grid if day not in measured_days]
    pred_idx = [list(grid).index(d) for d in days_to_predict]

    # mean expected milk yield from standard curve
    mean_lc = pd.Series([standard_lc[g] for g in grid], index=grid)

    # --- Compute known production (sum of actual measurements) ---------
    if 290 in measured_days:
        # special last interval: 25 days
        known_prod = df["MilkYieldInterp"][:-1].sum() * 20 + df["MilkYieldInterp"].iloc[-1] * 25
    else:
        known_prod = df["MilkYieldInterp"].sum() * 20

    # --- Compute population mean for missing days ----------------------
    pop_mean_missing = mean_lc.loc[days_to_predict]

    if 290 in pop_mean_missing.index:
        population_mean = (
            pop_mean_missing.iloc[:-1].sum() * 20 +
            pop_mean_missing.iloc[-1] * 25
        )
    else:
        population_mean = pop_mean_missing.sum() * 20

    # --- Compute correlation-based correction --------------------------
    days_to_predict_np = np.array(days_to_predict)
    measured_days_np = np.array(measured_days)

    # for each missing day: find closest measured day
    closest_measured = [
        measured_days_np[np.argmin(np.abs(measured_days_np - g))]
        for g in days_to_predict_np
    ]
    closest_idx = [list(grid).index(d) for d in closest_measured]

    b_star_list = []
    for pi, qi in zip(closest_idx, pred_idx):
        bpj = correlation_matrix.iloc[pi, qi]
        stdj = std_per_grid_day[qi]
        stdp = std_per_grid_day[pi]
        b_star_list.append(bpj * stdj / stdp)

    # scale correction by interval lengths
    if 290 in measured_days:
        # last interval belongs to prediction group
        correction_weighted = sum(b_star_list[:-1]) * 20
    else:
        correction_weighted = (
            sum(b_star_list[:-1]) * 20 +
            b_star_list[-1] * 25
        )

    last_day = df["GridDay"].iloc[-1]
    last_yield = df["MilkYieldInterp"].iloc[-1]
    mean_last = mean_lc.loc[last_day]

    correction = correction_weighted * (last_yield - mean_last)

    # --- Final sum -----------------------------------------------------
    final_milk_yield = known_prod + population_mean + correction
    return float(final_milk_yield)



def ISLC(
    df: pd.DataFrame,
    column_name_days_in_milk: str,
    column_name_milk_yield: str,
    standard_lc_305: npt.NDArray[np.float64] = STANDARD_CURVE,
    correlation_matrix: pd.DataFrame=CORR_MATRIX,
    std_per_grid_day: npt.NDArray[np.float64] =STDs
) -> pd.DataFrame:
    """Compute estimated 305-day milk yields for lactations in a DataFrame.

    The function groups ``df`` by ``TestId`` (or treats the entire frame as a
    single lactation if no ``TestId`` column exists), interpolates observed
    yields onto the DIM grid, and applies :func:`ISLC_method` to each
    lactation to produce an estimated 305-d yield.

    Args:
        df: Input pandas DataFrame containing test-day records. Rows with ``DaysInMilk``
            > 305 are dropped.
        column_name_days_in_milk: Column name in ``df`` that contains DIM.
        column_name_milk_yield: Column name in ``df`` that contains measured
            milk yield for the corresponding DIM.
        standard_lc_305: Standard lactation curve values aligned to the grid
            (default: module ``STANDARD_CURVE``).
        correlation_matrix: Correlation matrix for grid-day yields
            (default: module ``CORR_MATRIX``).
        std_per_grid_day: Standard deviations per grid day (default: module
            ``STDs``).

    Returns:
        A DataFrame with columns ``305_milk_yield`` and ``TestId`` where each
        row corresponds to a unique lactation (``TestId``) from the input.

    Notes:
        If ``TestId`` is absent in ``df``, a single TestId==0 is created and
        the entire input is processed as one lactation.
    """
    # drop all milkyields above 305
    df = df[df[column_name_days_in_milk] <= 305]

    #If there is no TestId column, create one with all 0 values > this asumes there is only one lactation in the df
    if "TestId" not in df.columns:
        df["TestId"] = 1

    #interpolate measurements to days on the grid 
    df_interpolated = (
        df.groupby("TestId", group_keys=False)
        .apply(
            lambda group: interpolation_standard_lc(
                group, column_name_days_in_milk, column_name_milk_yield, standard_lc_305
            )
        )
        .reset_index(drop=True)
    )


    #find all unique TestId's
    unique_test_ids = df["TestId"].unique()
    result = np.zeros(len(unique_test_ids))

    #calculate for each TestId the 305 milkyield 
    for i, test_id in enumerate(unique_test_ids):
        lactation = df_interpolated[df_interpolated["TestId"] == test_id]
        cummulative_yield = ISLC_method(lactation, standard_lc_305, correlation_matrix, std_per_grid_day)
        result[i] = cummulative_yield

    # convert result to panda df
    result = pd.DataFrame(result, columns=["305_milk_yield"])
    result["TestId"] = unique_test_ids
    return result


#create your own standard lactation curve, correlation matrix and standard deviations per grid days: 

# step 1 interpolate to the days on the grid
# Based on the CRV e-documents E2 the interpolation is not linear but instead depends on the standard lactation curve. 
def interpolation_standard_lc(
    group: pd.DataFrame,
    column_name_dim: str,
    column_name_milk_yield: str,
    standard_lc:  pd.Series   
) -> pd.DataFrame:
    """Interpolate a single lactation onto the DIM grid guided by a standard curve.

    The function interpolates measured yields for one animal onto the
    predefined grid of DIM values. When a grid day coincides with a measured
    DIM the observed yield is used; otherwise the interpolation adjusts the
    linear slope between neighboring measurements by the difference in the
    standard curve, following the CRV E2 approach.

    The interpolation formula applied for a grid day ``gday`` between two
    measured points (x1,y1) and (x2,y2) is::

        slope = ((y2 - y1) - (g2 - g1)) / (x2 - x1)
        yi = gi + (slope * (gday - x1) + (y1 - g1))

    Args:
        group: DataFrame with test-day records for a single animal. Must
            contain columns named by ``column_name_dim`` and `  column_name_milk_yield``.
        column_name_dim: Name of the DIM column in ``group``.
        column_name_milk_yield: Name of the milk-yield column in ``group``.
        standard_lc: A Series indexed by DIM providing the expected yield on
            each grid day; used to guide the interpolation shape.

    Returns:
        A DataFrame with one row per interpolated grid day containing the
        original identifying columns (from the first row of ``group``), plus
        the columns ``GridDay`` and ``MilkYieldInterp``.

    Notes:
        - No interpolation is performed outside the range bounded by the
          first and last measured DIM for the lactation (those grid days are
          skipped).
        - The implementation defines a local default ``grid`` of
          [10, 30, ..., 290].
    """
    # define the grid

    grid = [10, 30, 50, 70, 90, 110, 130, 150, 170, 190, 210, 230, 250, 270, 290]

    # Sort and ensure unique DIMs
    group = group.sort_values(column_name_dim).drop_duplicates(column_name_dim)
    dims = group[column_name_dim].tolist()

    rows = []

    #loop over the grid days 
    for gday in grid:

        # --- CASE 1: Exact measured day ---------------------------
        if gday in dims:
            y_val = group.loc[group[column_name_dim] == gday,   column_name_milk_yield].iloc[0]

            row = group.iloc[0].to_dict()
            row["GridDay"] = gday
            row["MilkYieldInterp"] = float(y_val)
            rows.append(row)
            continue

        # --- CASE 2: interpolate between measured days -------------
        before = group[group[column_name_dim] < gday].tail(1)
        after  = group[group[column_name_dim] > gday].head(1)

        # Cannot interpolate before the first or after the last measurement
        if before.empty or after.empty:
            continue

        x1 = before[column_name_dim].iloc[0]
        y1 = before[column_name_milk_yield].iloc[0]
        x2 = after[column_name_dim].iloc[0]
        y2 = after[column_name_milk_yield].iloc[0]

        # expected yields from standard lactation curve
        g1 = standard_lc.loc[int(x1)]
        g2 = standard_lc.loc[int(x2)]
        gi = standard_lc.loc[int(gday)]

        # Wilmink-based interpolation formula
        slope = ((y2 - y1) - (g2 - g1)) / (x2 - x1)
        yi = gi + (slope * (gday - x1) + (y1 - g1))

        row = group.iloc[0].to_dict()
        row["GridDay"] = gday
        row["MilkYieldInterp"] = float(yi)
        rows.append(row)

    return pd.DataFrame(rows)





def linear_interpd_all_to_grid(   
    group: pd.DataFrame,
    column_name_dim: str,
    column_name_milk_yield: str,
    standard_lc: pd.Series | None = None,
) -> pd.DataFrame:    
    """Linearly interpolate all grid days for a lactation.

    This helper uses linear interpolation (with extrapolation) to produce
    milk-yield values for every grid day regardless of whether the grid day
    lies between measured observations.

    Args:
        group: DataFrame containing measured DIM and yield values for one
            lactation.
        column_name_days_in_milk: Name of the DIM column.
        column_name_milk_yield: Name of the milk-yield column.

    Returns:
        A DataFrame with identifying columns copied from ``group``'s first
        row and columns ``GridDay`` and ``MilkYieldInterp`` containing the
        interpolated (or extrapolated) yields for every grid day.
    """
    # define the grid

    grid = [10, 30, 50, 70, 90, 110, 130, 150, 170, 190, 210, 230, 250, 270, 290]
    group = group.sort_values(column_name_dim).drop_duplicates(
        subset=column_name_days_in_milk
    )
    f = interp1d(
        group[column_name_dim],
        group[column_name_milk_yield],
        kind="linear",
        fill_value="extrapolate",
    )

    base = {
        col: group[col].iloc[0]
        for col in group.columns
        if col not in [column_name_days_in_milk, column_name_milk_yield]
    }
    base["GridDay"] = grid
    base["MilkYieldInterp"] = f(grid)

    return pd.DataFrame(base)





# Create an interpolation function that only outputs the griddays that are between two milk measurements using linear interpolation.
def linear_interpd_closest_to_grid(
        group: pd.DataFrame,
    column_name_dim: str,
    column_name_milk_yield: str,
    standard_lc:  pd.Series   
) -> pd.DataFrame:
    """Linearly interpolate grid days between measured observations.

    This helper returns interpolated yields only for grid days that lie
    between the first and last measured DIM for the lactation. If no grid
    days fall within the measured range the function returns ``None``.

    Args:
        group: DataFrame for a single lactation.
        column_name_days_in_milk: Name of the DIM column.
        column_name_milk_yield: Name of the milk-yield column.

    Returns:
        A DataFrame with identifying columns plus ``GridDay`` and
        ``MilkYieldInterp``, or ``None`` if there are no grid days within
        the measured range.
    """
    # define grid 
    grid = [10, 30, 50, 70, 90, 110, 130, 150, 170, 190, 210, 230, 250, 270, 290]


    group = group.sort_values(column_name_dim).drop_duplicates(
        subset=column_name_dim
    )

    # Find the range of interpolatable DIM
    min_dim = group[column_name_dim].min()
    max_dim = group[column_name_dim].max()
    grid_in_range = [g for g in grid if min_dim <= g <= max_dim]

    # apply linear interpolation
    if not grid_in_range:
        return None
    f = interp1d(
        group[column_name_dim],
        group[column_name_milk_yield],
        kind="linear",
        fill_value="nan",
    )


    # create a new dataframe with the newly created columns
    base = {
        col: group[col].iloc[0]
        for col in group.columns
        if col not in [column_name_dim, column_name_milk_yield]
    }
    base["GridDay"] = grid_in_range
    base["MilkYieldInterp"] = f(grid_in_range)

    return pd.DataFrame(base)

 
# Attempt to recreate math of Wilmink paper with the idea of multiple regression (Wilmink et al. 1987)
def create_standard_lc_representation(
    df: pd.DataFrame,
    standard_lactation_curve: pd.Series,
    column_name_dim: str,
    col_milk_yield: str,
    interpolation_method: InterpolationMethod = interpolation_standard_lc,
) -> tuple[pd.DataFrame, npt.NDArray[np.float64], pd.Series]:
    """Create a standard lactation curve with correlation matrix from data.

    This function estimates the correlation structure and standard deviations
    of milk yields across grid days, and refits a Wilmink lactation curve to
    the interpolated data. The outputs can be used as inputs to the
    ``ISLC_method`` or ``ISLC`` functions for predicting 305-d yields.

    The process standardizes yields per animal and computes row-wise
    (per-animal) statistics, then derives relationships across grid days.

    Args:
        df: Input DataFrame containing test-day records. Must include a
            ``TestId`` column to identify unique lactations. Also requires
            columns specified by ``column_name_dim`` and ``col_milk_yield``.
        standard_lactation_curve: A Series providing a reference lactation
            curve (e.g., the fitted Wilmink curve on which to base
            interpolation).
        column_name_dim: Name of the column in ``df`` containing days in milk (DIM).
        col_milk_yield: Name of the column in ``df`` containing measured
            milk yields.
        interpolation_method: An interpolation method conforming to
            ``InterpolationMethod`` protocol (default: ``interpolation_standard_lc``).
            Must be callable with signature (group, column_name_dim,    column_name_milk_yield, standard_lc).

    Returns:
        A tuple of three elements:
        - corr (pd.DataFrame): Correlation matrix between grid-day yields.
        - std_per_grid_day (np.ndarray): Standard deviations of standardized
          yields per grid day.
        - standard_lactation_curve_grid (pd.Series): Refitted Wilmink model
          indexed by DIM (1–305).

    Notes:
        - Expects ``df`` to have a ``TestId`` column to group lactations.
        - Performs standardization per animal (row-wise), so output
          correlations and standard deviations reflect between-day variation
          within standardized animal profiles.
        - Uses ``fit_lactation_curve`` from the ``lactationcurve`` package
          with model='Wilmink' and fitting='frequentist'.
    """
    if "TestId" not in df.columns:
        raise ValueError("DataFrame must contain a 'TestId' column.")
    if column_name_dim not in df.columns or col_milk_yield not in df.columns:
        raise ValueError(f"Columns '{column_name_dim}' and '{col_milk_yield}' must be in df.")


    df_grid = (
        df.groupby("TestId")
        .apply(
            interpolation_method,
            column_name_dim=column_name_dim,
            column_name_milk_yield=col_milk_yield,
            standard_lc=standard_lactation_curve,
        )
        .reset_index(drop=True)
    )

    # define Znp
    # pivot df to make GridDay the columns
    # Z should be the unscaled pivot table (TestId × GridDay)
    Z = df_grid.pivot(index="TestId", columns="GridDay", values="MilkYieldInterp")

    # Standardize records per cow (so each row has mean=0, std=1)                               
    Z_std = (Z.sub(Z.mean(axis=1), axis=0)).div(Z.std(axis=1), axis=0)

    # Convert to NumPy array
    Znp = Z_std.to_numpy()

    # calculate correlation matrix
    corr = pd.DataFrame(Znp, columns=Z.columns).corr()

    # calculate standard deviations for each grid day from the Znp matrix               
    std_per_grid_day = np.nanstd(Znp, axis=0) #ignores NaN 

    # fit Wilmink model to get mean values and std for each cow
    standard_lactation_curve_grid = pd.Series(
        fit_lactation_curve(
            df_grid["GridDay"].values,
            df_grid["MilkYieldInterp"].values,
            model="Wilmink",
            fitting="frequentist",
        ),
        index=range(1, 306)
    )
    return corr, std_per_grid_day, standard_lactation_curve_grid




#test 
#do a test with a complete lactation dataset
df_test = pd.read_csv(
    r"C:\Users\Meike van Leerdam\lactation-curve-research\test_data\L2Anim2Herd654.csv",
    sep=",",
)

#rename some columns 
df_test['MilkingYield'] = df_test['TestDayMilkYield']
df_test.drop(columns=['TestDayMilkYield'], inplace=True)
# df_test['TestId'] = 1

#calculate true 305 
df_test = df_test[df_test['DaysInMilk'] <= 305]
actual_305 = sum(df_test['MilkingYield'])

print(df_test.head())

#calculate using ISLC
islc = ISLC(df=df_test, column_name_days_in_milk="DaysInMilk", column_name_milk_yield="MilkingYield")
print(f"True 305: {actual_305}")
print(f"ISLC: {islc['305_milk_yield'].values[0]}")
print(f'Difference: {actual_305 - islc["305_milk_yield"].values[0]}')
print(f'Percentage error: {(actual_305 - islc["305_milk_yield"].values[0])/actual_305 * 100:.2f}%')


# # Create two copies and assign artificial TestId values
# df_test_3 = df_test.copy()
# df_test_3["TestId"] = 0

# df_test_4 = df_test.copy()
# df_test_4["TestId"] = 1
# # corrupt measurements
# df_test_4["MilkingYield"] = df_test_4["MilkingYield"] * 10

# # Concatenate the two DataFrames
# df_test_combined = pd.concat([df_test_3, df_test_4], ignore_index=True)


# matrix, std_list, slc = create_standard_lc_representation(df_test, STANDARD_CURVE, 'DaysInMilk', 'MilkingYield')

# #apply ISLC 
# islc_own_slc = ISLC(df_test_combined, 'DaysInMilk', 'MilkingYield', slc , std_list, matrix)
# print(islc_own_slc)



