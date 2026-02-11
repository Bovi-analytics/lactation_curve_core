"""Lactation Curves API.

FastAPI application exposing lactation curve fitting, characteristic calculation,
and the ICAR Test Interval Method for 305-day yield estimation.
"""

from typing import Literal

import pandas as pd
from fastapi import FastAPI, HTTPException
from lactationcurve import calculate_characteristic, fit_lactation_curve, test_interval_method
from pydantic import BaseModel, Field

app = FastAPI(
    title="Lactation Curves API",
    description=(
        "API for dairy lactation curve analysis. Provides endpoints to fit mathematical "
        "lactation curve models (Wood, Wilmink, MilkBot, etc.) to test-day milk recordings, "
        "extract lactation characteristics (peak yield, time to peak, 305-day yield, persistency), "
        "and calculate 305-day yields using the ICAR Test Interval Method."
    ),
    version="0.1.0",
)


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------


class FitRequest(BaseModel):
    """Request body for fitting a lactation curve model to test-day data."""

    dim: list[int] = Field(
        description="Days in milk for each test day recording.",
        examples=[[10, 30, 60, 90, 120, 150, 200, 250, 305]],
    )
    milk_recordings: list[float] = Field(
        description="Milk yield (kg) for each test day, matching the order of `dim`.",
        examples=[[15.0, 25.0, 30.0, 32.0, 30.0, 28.0, 24.0, 20.0, 16.0]],
    )
    model: Literal["wood", "wilmink", "ali_schaeffer", "fischer", "milkbot"] = Field(
        default="wood",
        description="Lactation curve model to fit.",
    )
    fitting: Literal["frequentist", "bayesian"] = Field(
        default="frequentist",
        description="Fitting method. Bayesian fitting is only available for the MilkBot model.",
    )
    breed: Literal["H", "J"] = Field(
        default="H",
        description="Breed of the cow (Bayesian fitting only). H = Holstein, J = Jersey.",
    )
    parity: int = Field(
        default=3,
        ge=1,
        description="Lactation number (Bayesian fitting only). Parities >= 3 are treated as 3.",
    )
    continent: Literal["USA", "EU"] = Field(
        default="USA",
        description="Continent for Bayesian priors (Bayesian fitting only).",
    )


class FitResponse(BaseModel):
    """Response containing daily milk yield predictions for the fitted curve."""

    predictions: list[float] = Field(
        description="Predicted daily milk yield (kg) for days 1 through 305 (or max DIM if > 305).",
    )


class CharacteristicRequest(BaseModel):
    """Request body for calculating a lactation curve characteristic."""

    dim: list[int] = Field(
        description="Days in milk for each test day recording.",
        examples=[[10, 30, 60, 90, 120, 150, 200, 250, 305]],
    )
    milk_recordings: list[float] = Field(
        description="Milk yield (kg) for each test day, matching the order of `dim`.",
        examples=[[15.0, 25.0, 30.0, 32.0, 30.0, 28.0, 24.0, 20.0, 16.0]],
    )
    model: Literal["wood", "wilmink", "ali_schaeffer", "fischer", "milkbot"] = Field(
        default="wood",
        description="Lactation curve model to use for fitting.",
    )
    characteristic: Literal["time_to_peak", "peak_yield", "cumulative_milk_yield", "persistency"] = Field(
        default="cumulative_milk_yield",
        description=(
            "Which characteristic to calculate. "
            "`time_to_peak`: days to peak milk production. "
            "`peak_yield`: maximum daily milk yield (kg). "
            "`cumulative_milk_yield`: total milk over the lactation (kg). "
            "`persistency`: rate of decline after peak."
        ),
    )
    fitting: Literal["frequentist", "bayesian"] = Field(
        default="frequentist",
        description="Fitting method. Bayesian fitting is only available for the MilkBot model.",
    )
    breed: Literal["H", "J"] = Field(
        default="H",
        description="Breed of the cow (Bayesian fitting only). H = Holstein, J = Jersey.",
    )
    parity: int = Field(
        default=3,
        ge=1,
        description="Lactation number (Bayesian fitting only). Parities >= 3 are treated as 3.",
    )
    continent: Literal["USA", "EU"] = Field(
        default="USA",
        description="Continent for Bayesian priors (Bayesian fitting only).",
    )
    persistency_method: Literal["derived", "literature"] = Field(
        default="derived",
        description=(
            "How to calculate persistency. "
            "`derived`: average slope after peak (works for all models). "
            "`literature`: model-specific formula (Wood and MilkBot only)."
        ),
    )
    lactation_length: int = Field(
        default=305,
        ge=1,
        description="Lactation length in days for cumulative yield and persistency calculations.",
    )


class CharacteristicResponse(BaseModel):
    """Response containing the calculated characteristic value."""

    characteristic: str = Field(description="Name of the calculated characteristic.")
    value: float = Field(description="Numeric value of the characteristic.")


class TestDayRecord(BaseModel):
    """A single test day observation for the ICAR Test Interval Method."""

    days_in_milk: int = Field(
        ge=1,
        le=305,
        description="Day in milk for this test day recording.",
    )
    milking_yield: float = Field(
        gt=0,
        description="Milk yield (kg) for this test day.",
    )
    test_id: str | int = Field(
        default=1,
        description="Lactation/animal identifier for grouping. Records with the same test_id are treated as one lactation.",
    )


class TestIntervalRequest(BaseModel):
    """Request body for the ICAR Test Interval Method."""

    records: list[TestDayRecord] = Field(
        min_length=2,
        description="Test day records. Must have at least 2 records per test_id for interpolation.",
        examples=[
            [
                {"days_in_milk": 10, "milking_yield": 30.5, "test_id": "cow1"},
                {"days_in_milk": 30, "milking_yield": 35.2, "test_id": "cow1"},
                {"days_in_milk": 60, "milking_yield": 38.1, "test_id": "cow1"},
                {"days_in_milk": 100, "milking_yield": 36.0, "test_id": "cow1"},
            ]
        ],
    )


class TestIntervalResult(BaseModel):
    """Result for a single lactation from the Test Interval Method."""

    test_id: str | int = Field(description="Lactation/animal identifier.")
    total_305_yield: float = Field(description="Estimated 305-day milk yield (kg).")


class TestIntervalResponse(BaseModel):
    """Response containing 305-day yield estimates for each lactation."""

    results: list[TestIntervalResult]


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@app.get(
    "/",
    summary="Health check",
    description="Returns the service status. Use this to verify the API is running.",
)
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post(
    "/fit",
    response_model=FitResponse,
    summary="Fit a lactation curve",
    description=(
        "Fits a mathematical lactation curve model to test-day milk recordings and returns "
        "predicted daily milk yields for days 1 through 305 (or the maximum DIM if > 305). "
        "Supported models: Wood, Wilmink, Ali-Schaeffer, Fischer, and MilkBot. "
        "Frequentist fitting uses least-squares optimization. Bayesian fitting (MilkBot only) "
        "uses informative priors from Chen et al."
    ),
)
def fit(request: FitRequest) -> FitResponse:
    try:
        predictions = fit_lactation_curve(
            dim=request.dim,
            milkrecordings=request.milk_recordings,
            model=request.model,
            fitting=request.fitting,
            breed=request.breed,
            parity=request.parity,
            continent=request.continent,
        )
        return FitResponse(predictions=predictions.tolist())
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e)) from e


@app.post(
    "/characteristic",
    response_model=CharacteristicResponse,
    summary="Calculate a lactation characteristic",
    description=(
        "Calculates a specific characteristic from test-day data by first fitting a lactation "
        "curve model, then extracting the requested metric. Available characteristics: "
        "`time_to_peak` (days), `peak_yield` (kg/day), `cumulative_milk_yield` (kg over lactation), "
        "and `persistency` (rate of decline after peak)."
    ),
)
def characteristic(request: CharacteristicRequest) -> CharacteristicResponse:
    try:
        value = calculate_characteristic(
            dim=request.dim,
            milkrecordings=request.milk_recordings,
            model=request.model,
            characteristic=request.characteristic,
            fitting=request.fitting,
            breed=request.breed,
            parity=request.parity,
            continent=request.continent,
            persistency_method=request.persistency_method,
            lactation_length=request.lactation_length,
        )
        return CharacteristicResponse(characteristic=request.characteristic, value=value)
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e)) from e


@app.post(
    "/test-interval-method",
    response_model=TestIntervalResponse,
    summary="ICAR Test Interval Method",
    description=(
        "Calculates the 305-day milk yield using the ICAR Test Interval Method "
        "(Procedure 2, Section 2 of ICAR Guidelines). Uses linear projection for the start "
        "and end of lactation, and the trapezoidal rule for intermediate test days. "
        "Supports multiple lactations in a single request by grouping records via `test_id`."
    ),
)
def test_interval(request: TestIntervalRequest) -> TestIntervalResponse:
    df = pd.DataFrame([r.model_dump() for r in request.records])
    df = df.rename(
        columns={
            "days_in_milk": "DaysInMilk",
            "milking_yield": "MilkingYield",
            "test_id": "TestId",
        }
    )

    try:
        result_df = test_interval_method(df)
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e)) from e

    results = [
        TestIntervalResult(test_id=row["TestId"], total_305_yield=row["Total305Yield"])
        for _, row in result_df.iterrows()
    ]
    return TestIntervalResponse(results=results)
