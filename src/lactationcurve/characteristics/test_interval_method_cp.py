# %% md
# Testing the different ICAR methods to calculate 305-d milk production based on Procedure 2 of Section 2 of ICAR Guidelines – Computing of Accumulated Lactation Yield.
#
# %% md
# The Test Interval Method of ICAR
# %% md
# Author: Meike van Leerdam, Date: 07-31-2025
# %%

import pandas as pd

# make the package a bit more flexible for different column names


def test_interval_method(
    df, days_in_milk_col=None, milking_yield_col=None, test_id_col=None, default_test_id=1
):
    """
    Calculate the total 305-day milk yield using the trapezoidal rule
    for interim days, and linear projection for start and end beyond the sampling period.

    Parameters:
        df (DataFrame): Input DataFrame
        days_in_milk_col (str): Optional override for the DaysInMilk column
        milking_yield_col (str): Optional override for the MilkingYield column
        test_id_col (str): Optional override for the TestId column
        default_test_id (any): If TestId column is missing, create it with this value

    Returns:
        panda dataframe with the columns TestId, Total 305-day milk yield.
    """

    result = []

    # create a bit more flexibility in naming the columns and when only one lactation is put in without a testid

    # Define accepted variations for each logical column
    # Accepted aliases (case-insensitive)
    aliases = {
        "DaysInMilk": ["daysinmilk", "dim", "testday"],
        "MilkingYield": ["milkingyield", "testdaymilkyield", "milkyield", "yield"],
        "TestId": ["animalid", "testid", "id"],
    }

    # Create a mapping from lowercase to actual column names
    col_lookup = {col.lower(): col for col in df.columns}

    def get_col_name(override, possible_names):
        """Return matching actual column name from df, or None if not found."""
        if override:
            return col_lookup.get(override.lower())
        for name in possible_names:
            if name in col_lookup:
                return col_lookup[name]
        return None

    # Resolve columns
    dim_col = get_col_name(days_in_milk_col, aliases["DaysInMilk"])
    if not dim_col:
        raise ValueError("No DaysInMilk column found in DataFrame.")

    my_col = get_col_name(milking_yield_col, aliases["MilkingYield"])
    if not my_col:
        raise ValueError("No MilkingYield column found in DataFrame.")

    id_col = get_col_name(test_id_col, aliases["TestId"])
    if not id_col:
        id_col = "TestId"
        df[id_col] = default_test_id

    # Filter out records where Day > 305
    df = df[df[dim_col] <= 305]

    # Iterate over each lactation
    for lactation in df[id_col].unique():
        lactation_df = df[df[id_col] == lactation].copy()

        # Sort by DaysInMilk ascending
        lactation_df.sort_values(by=dim_col, ascending=True, inplace=True)

        if len(lactation_df) < 2:
            print(f"Skipping TestId {lactation}: not enough data points for interpolation.")
            continue

        # Start and end points
        start = lactation_df.iloc[0]
        end = lactation_df.iloc[-1]

        # Start contribution
        MY0 = start[dim_col] * start[my_col]

        # End contribution
        MYend = (306 - end[dim_col]) * end[my_col]

        # Intermediate trapezoidal contributions
        lactation_df["width"] = lactation_df[dim_col].diff().shift(-1)
        lactation_df["avg_yield"] = (lactation_df[my_col] + lactation_df[my_col].shift(-1)) / 2
        lactation_df["trapezoid_area"] = lactation_df["width"] * lactation_df["avg_yield"]

        total_intermediate = lactation_df["trapezoid_area"].sum()

        total_yield = MY0 + total_intermediate + MYend
        result.append((lactation, total_yield))

    return pd.DataFrame(result, columns=["TestId", "Total305Yield"])
