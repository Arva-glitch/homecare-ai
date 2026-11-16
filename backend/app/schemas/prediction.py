from datetime import date, datetime

from pydantic import BaseModel

from app.utils.time import UTCDateTime
from app.schemas.common import ORMModel


class Factor(BaseModel):
    factor: str
    detail: str
    impact: float  # points deducted from 100 by the transparent rule analysis


class PredictionOut(ORMModel):
    id: int
    appliance_id: int
    appliance_name: str | None = None
    appliance_category: str | None = None
    health_score: float
    risk_level: str
    priority: str
    recommended_service_date: date
    model_used: str
    confidence: float | None
    explanation: list[str]
    factors: list[Factor] = []
    class_probabilities: dict[str, float] | None = None
    created_at: UTCDateTime


class ModelInfo(BaseModel):
    ml_available: bool
    model_type: str | None
    trained_on: str
    disclaimer: str
    n_samples: int | None = None
    holdout_accuracy: float | None = None
    holdout_macro_f1: float | None = None
    feature_importances: dict[str, float] | None = None
    trained_at: str | None = None
