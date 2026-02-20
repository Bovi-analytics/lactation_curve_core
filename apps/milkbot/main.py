import numpy as np
from fastapi import FastAPI
from pydantic import BaseModel, Field

from lactationcurve import milkbot_model

app = FastAPI(title="MilkBot API")


class PredictRequest(BaseModel):
    t: list[int] = Field(examples=[[1, 30, 60, 90, 120, 150, 200, 250, 305]])
    a: float = Field(examples=[40.0], description="Scale")
    b: float = Field(examples=[20.0], description="Ramp")
    c: float = Field(examples=[0.5], description="Offset")
    d: float = Field(examples=[0.003], description="Decay")


@app.get("/")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/predict")
def predict(request: PredictRequest) -> dict[str, list[float]]:
    t = np.array(request.t)
    predictions = milkbot_model(t, request.a, request.b, request.c, request.d)
    return {"predictions": predictions.tolist()}
