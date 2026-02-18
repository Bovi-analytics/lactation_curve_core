from typing import Literal

import numpy as np
from fastapi import FastAPI
from pydantic import BaseModel, Field

from lactationcurve import (
    calculate_characteristic,
    fit_lactation_curve,
    milkbot_model,
)

app = FastAPI(title="Lactation Curves API")

DIM_DESC = (
    "Days in milk (DIM) for each test-day recording."
    " Must have the same length as milkrecordings."
)
MILK_DESC = (
    "Milk yield (kg) for each test-day recording."
    " Must have the same length as dim."
)
MODEL_DESC = (
    "Lactation curve model to fit."
    " Wood (3-param), Wilmink (4-param), Ali-Schaeffer (5-param),"
    " Fischer (3-param), or MilkBot (4-param)."
)
FITTING_DESC = (
    "Fitting method. Currently only frequentist"
    " (scipy optimization) is supported via this endpoint."
)
CHARACTERISTIC_DESC = (
    "Which lactation characteristic to compute."
    " time_to_peak: DIM at peak yield."
    " peak_yield: maximum daily yield (kg)."
    " cumulative_milk_yield: total kg over the lactation."
    " persistency: rate of decline after peak."
)
PERSISTENCY_DESC = (
    "How to calculate persistency."
    " 'derived': average slope after peak (default)."
    " 'literature': analytical formula (Wood/MilkBot only)."
)
LACTATION_LENGTH_DESC = (
    "Lactation length in days for the calculation."
    " 305 (default), or a custom integer."
)


class PredictRequest(BaseModel):
    """Request body for direct MilkBot model prediction with known parameters."""

    t: list[int] = Field(
        ...,
        description=(
            "Days in milk (DIM) at which to evaluate"
            " the MilkBot model."
        ),
        examples=[[1, 30, 60, 90, 120, 150, 200, 250, 305]],
    )
    a: float = Field(
        ...,
        description="Scale — overall milk production level (kg).",
        examples=[40.0],
    )
    b: float = Field(
        ...,
        description="Ramp — rate of rise in early lactation.",
        examples=[20.0],
    )
    c: float = Field(
        ...,
        description="Offset — time correction for calving.",
        examples=[0.5],
    )
    d: float = Field(
        ...,
        description="Decay — rate of exponential decline.",
        examples=[0.003],
    )


class FitRequest(BaseModel):
    """Request body for fitting a lactation curve model."""

    dim: list[int] = Field(
        ...,
        description=DIM_DESC,
        examples=[[10, 30, 60, 90, 120, 150, 200, 250, 305]],
    )
    milkrecordings: list[float] = Field(
        ...,
        description=MILK_DESC,
        examples=[[15.0, 25.0, 30.0, 28.0, 26.0, 24.0, 22.0, 20.0, 18.0]],
    )
    model: Literal[
        "wood", "wilmink", "ali_schaeffer", "fischer", "milkbot"
    ] = Field(
        default="wood",
        description=MODEL_DESC,
    )
    fitting: Literal["frequentist"] = Field(
        default="frequentist",
        description=FITTING_DESC,
    )
    breed: Literal["H", "J"] = Field(
        default="H",
        description="Breed: H = Holstein, J = Jersey.",
    )
    parity: int = Field(
        default=3,
        ge=1,
        description="Lactation number. Parities >= 3 are one group.",
    )
    continent: Literal["USA", "EU", "CHEN"] = Field(
        default="USA",
        description="Continent for priors: USA, EU, or CHEN.",
    )


class CharacteristicRequest(BaseModel):
    """Request body for computing a lactation characteristic."""

    dim: list[int] = Field(
        ...,
        description=DIM_DESC,
        examples=[[10, 30, 60, 90, 120, 150, 200, 250, 305]],
    )
    milkrecordings: list[float] = Field(
        ...,
        description=MILK_DESC,
        examples=[[15.0, 25.0, 30.0, 28.0, 26.0, 24.0, 22.0, 20.0, 18.0]],
    )
    model: Literal[
        "wood", "wilmink", "ali_schaeffer", "fischer", "milkbot"
    ] = Field(
        default="wood",
        description=MODEL_DESC,
    )
    characteristic: Literal[
        "time_to_peak",
        "peak_yield",
        "cumulative_milk_yield",
        "persistency",
    ] = Field(
        default="cumulative_milk_yield",
        description=CHARACTERISTIC_DESC,
    )
    fitting: Literal["frequentist"] = Field(
        default="frequentist",
        description=FITTING_DESC,
    )
    breed: Literal["H", "J"] = Field(
        default="H",
        description="Breed: H = Holstein, J = Jersey.",
    )
    parity: int = Field(
        default=3,
        ge=1,
        description="Lactation number. Parities >= 3 are one group.",
    )
    continent: Literal["USA", "EU", "CHEN"] = Field(
        default="USA",
        description="Continent for priors: USA, EU, or CHEN.",
    )
    persistency_method: Literal["derived", "literature"] = Field(
        default="derived",
        description=PERSISTENCY_DESC,
    )
    lactation_length: int = Field(
        default=305,
        ge=1,
        description=LACTATION_LENGTH_DESC,
    )


@app.get("/")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/predict")
def predict(request: PredictRequest) -> dict[str, list[float]]:
    """Evaluate the MilkBot model with known parameters.

    Use this when you already have the four MilkBot parameters
    (a, b, c, d) and want predicted milk yields at specific DIM.
    """
    t = np.array(request.t)
    predictions = milkbot_model(
        t, request.a, request.b, request.c, request.d,
    )
    return {"predictions": predictions.tolist()}


@app.post("/fit")
def fit(request: FitRequest) -> dict[str, list[float]]:
    """Fit a lactation curve model to test-day milk recordings.

    Takes observed test-day data (DIM + milk yields) and fits the
    specified model using scipy optimization. Returns predicted
    daily milk yields for DIM 1-305 (or up to max(dim) if > 305).

    The response contains 305+ predicted values, one per day.
    """
    predictions = fit_lactation_curve(
        dim=request.dim,
        milkrecordings=request.milkrecordings,
        model=request.model,
        fitting=request.fitting,
        breed=request.breed,
        parity=request.parity,
        continent=request.continent,
    )
    return {"predictions": predictions.tolist()}


@app.post("/characteristic")
def characteristic(
    request: CharacteristicRequest,
) -> dict[str, float]:
    """Compute a single lactation characteristic from milk recordings.

    Fits a lactation curve model to the data, then derives one of:
    - **time_to_peak**: DIM at which peak yield occurs.
    - **peak_yield**: maximum daily milk yield (kg).
    - **cumulative_milk_yield**: total kg over the lactation.
    - **persistency**: rate of decline after peak.

    Returns a single numeric value.
    """
    value = calculate_characteristic(
        dim=request.dim,
        milkrecordings=request.milkrecordings,
        model=request.model,
        characteristic=request.characteristic,
        fitting=request.fitting,
        parity=request.parity,
        breed=request.breed,
        continent=request.continent,
        persistency_method=request.persistency_method,
        lactation_length=request.lactation_length,
    )
    return {"value": float(value)}
