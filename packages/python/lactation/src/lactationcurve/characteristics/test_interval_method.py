"""
ICAR 305-day yield calculation — Test Interval Method.

This module implements the **Test Interval Method** described in ICAR guidelines
(Procedure 2, Section 2: Computing of Accumulated Lactation Yield) to compute
total **305-day milk yield** from test-day data.

Approach
--------
- **Start segment**: Linear projection from calving (DIM=0) to the first test day.
- **Intermediate segments**: **Trapezoidal rule** between consecutive test days.
- **End segment**: Linear projection from the last test day to DIM=305 (exclusive
  upper bound 306 for day counting).

Column Flexibility
------------------
The function can accept various column name aliases (case-insensitive) and
optionally create a default `TestId` if missing. Recognized aliases:

- Days in Milk: `["daysinmilk", "dim", "testday"]`
- Milk Yield: `["milkingyield", "testdaymilkyield", "milkyield", "yield"]`
- Test Id: `["animalid", "testid", "id"]`

Returns a DataFrame with columns: `["TestId", "Total305Yield"]`.

Notes
-----
- Units: DIM in days, milk yield in kg.
- Records with `DIM > 305` are excluded prior to computation.

Author: Meike van Leerdam, Date: 07-31-2025
"""

import pandas as pd



def test_interval_method(
    df, days_in_milk_col=None, milking_yield_col=None, test_id_col=None, default_test_id=1
):
    """Compute 305-day total milk yield using the ICAR Test Interval Method.

    The method applies:
    - Linear projection from calving to the first test day,
    - Trapezoidal integration between consecutive test days,
    - Linear projection from the last test day to DIM=305.

    Args:
        df (pd.DataFrame): Input DataFrame with at least DaysInMilk, MilkingYield,
            and (optionally) TestId columns (names can be provided via arguments
            or matched via known aliases, case-insensitive).
        days_in_milk_col (str | None): Optional column name override for DaysInMilk.
        milking_yield_col (str | None): Optional column name override for MilkingYield.
        test_id_col (str | None): Optional column name override for TestId.
        default_test_id (Any): If TestId is missing, a new `TestId` column is created
            with this value.

    Returns:
        pd.DataFrame: Two-column DataFrame with
            - "TestId": identifier per lactation,
            - "Total305Yield": computed total milk yield over 305 days.

    Raises:
        ValueError: If required columns (DaysInMilk or MilkingYield) cannot be found.

    Notes:
        - Records with DIM > 305 are dropped before computation.
        - At least two data points per TestId are required for trapezoidal integration;
          otherwise the lactation is skipped.
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
        """Return a matching actual column name from `df`, or `None` if not found.

        Args:
            override (str | None): Explicit column name provided by the user.
            possible_names (list[str]): List of acceptable aliases (lowercase).

        Returns:
            str | None: The actual column name present in `df`, or `None` if no match.
        """
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