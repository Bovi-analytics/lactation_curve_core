from typing import Literal

import numpy as np
from fastapi import FastAPI
from pydantic import BaseModel, Field

from lactationcurve import fit_lactation_curve, milkbot_model

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
