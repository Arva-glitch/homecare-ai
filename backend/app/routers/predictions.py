from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_owned_appliance
from app.db.session import get_db
from app.ml.predictor import predictor
from app.models import Appliance, PredictionHistory, User
from app.schemas.prediction import ModelInfo, PredictionOut
from app.services.notification_service import generate_alerts
from app.services.prediction_service import predict_all, predict_appliance
from app.services.serializers import prediction_out

router = APIRouter(prefix="/predictions", tags=["Predictive Maintenance"])


@router.get("/model-info", response_model=ModelInfo)
def model_info(_: User = Depends(get_current_user)):
    m = predictor.meta or {}
    return ModelInfo(
        ml_available=predictor.ml_available,
        model_type=m.get("model_type") if predictor.ml_available else "Rule-based engine",
        trained_on=m.get("trained_on", "n/a"),
        disclaimer=m.get("disclaimer", "Rule-based heuristic scores; not validated failure probabilities."),
        n_samples=m.get("n_samples"),
        holdout_accuracy=m.get("holdout_accuracy"),
        holdout_macro_f1=m.get("holdout_macro_f1"),
        feature_importances=m.get("feature_importances"),
        trained_at=m.get("trained_at"),
    )


@router.post("/run", response_model=list[PredictionOut])
def run_all(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Re-assess every appliance owned by the current user."""
    results = predict_all(db, user.id)
    generate_alerts(db, user)
    return [prediction_out(r) for r in results]


@router.post("/appliances/{appliance_id}", response_model=PredictionOut)
def run_one(appliance_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    a = get_owned_appliance(db, user, appliance_id)
    r = predict_appliance(db, a)
    generate_alerts(db, user)
    return prediction_out(r)


@router.get("/latest", response_model=list[PredictionOut])
def latest(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Most recent prediction for each appliance."""
    appliances = db.scalars(select(Appliance).where(Appliance.user_id == user.id)).all()
    out = []
    for a in appliances:
        p = db.scalars(select(PredictionHistory).where(PredictionHistory.appliance_id == a.id)
                       .order_by(PredictionHistory.created_at.desc(), PredictionHistory.id.desc()).limit(1)).first()
        if p:
            out.append(prediction_out(p))
    order = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}
    out.sort(key=lambda p: (order.get(p.risk_level, 4), p.health_score))
    return out


@router.get("/history", response_model=list[PredictionOut])
def history(appliance_id: int | None = None, limit: int = Query(50, ge=1, le=500),
            user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    q = select(PredictionHistory).where(PredictionHistory.user_id == user.id)
    if appliance_id:
        get_owned_appliance(db, user, appliance_id)
        q = q.where(PredictionHistory.appliance_id == appliance_id)
    q = q.order_by(PredictionHistory.created_at.desc(), PredictionHistory.id.desc()).limit(limit)
    return [prediction_out(p) for p in db.scalars(q).all()]
