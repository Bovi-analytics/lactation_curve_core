"""Lactation Curves API.

FastAPI application exposing lactation curve fitting, characteristic calculation,
and the ICAR Test Interval Method for 305-day yield estimation.
"""

import pandas as pd
from fastapi import FastAPI, HTTPException
from lactationcurve import calculate_characteristic, fit_lactation_curve, test_interval_method

from .schemas import (
    CharacteristicRequest,
    CharacteristicResponse,
    FitRequest,
    FitResponse,
    TestIntervalRequest,
    TestIntervalResponse,
    TestIntervalResult,
)

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
