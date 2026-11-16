"""Risk predictor: Random Forest (synthetic-trained) with a rule-based fallback."""
import json
import logging
from dataclasses import dataclass, field
from datetime import date, timedelta

from app.ml.features import (
    CLASS_HEALTH_CENTER,
    RISK_CLASSES,
    ApplianceFeatures,
    risk_from_health,
    rule_based_analysis,
)
from app.models.enums import SERVICE_INTERVAL_DAYS

log = logging.getLogger(__name__)

PRIORITY_BY_RISK = {
    "Critical": "Immediate — within 3 days",
    "High": "High — within 2 weeks",
    "Medium": "Normal — within 6 weeks",
    "Low": "Routine — at next scheduled interval",
}


@dataclass
class PredictionResult:
    health_score: float
    risk_level: str
    priority: str
    recommended_service_date: date
    model_used: str
    confidence: float | None
    explanation: list[str]
    factors: list[dict]
    class_probabilities: dict[str, float] | None = None
    features: dict = field(default_factory=dict)


class RiskPredictor:
    def __init__(self):
        self.model = None
        self.meta: dict = {}
        self.load_error: str | None = None
        self.force_rules = False  # used by tests / admin to exercise the fallback

    def load(self) -> bool:
        from app.ml.train import META_PATH, MODEL_PATH

        try:
            import joblib

            from app.ml.train import train

            if not MODEL_PATH.exists():
                log.warning("ML model not found; training on synthetic data now...")
                train(verbose=False)
            try:
                self.model = joblib.load(MODEL_PATH)
            except Exception:
                # e.g. artifact created with a different scikit-learn version: retrain locally
                log.warning("Could not load saved model; retraining on synthetic data...")
                train(verbose=False)
                self.model = joblib.load(MODEL_PATH)
            self.meta = json.loads(META_PATH.read_text()) if META_PATH.exists() else {}
            self.load_error = None
            return True
        except Exception as exc:  # pragma: no cover - depends on environment
            log.exception("Could not load ML model, using rule-based fallback")
            self.model = None
            self.load_error = str(exc)
            return False

    @property
    def ml_available(self) -> bool:
        return self.model is not None and not self.force_rules

    def predict(self, f: ApplianceFeatures, category: str, last_service: date | None,
                today: date | None = None) -> PredictionResult:
        today = today or date.today()
        rule_health, factors = rule_based_analysis(f)

        probs = None
        confidence = None
        if self.ml_available:
            try:
                p = self.model.predict_proba([f.to_vector()])[0]
                probs = {cls: round(float(v), 4) for cls, v in zip(self.model.classes_, p)}
                for cls in RISK_CLASSES:
                    probs.setdefault(cls, 0.0)
                risk = max(probs, key=probs.get)
                health = round(sum(probs[c] * CLASS_HEALTH_CENTER[c] for c in RISK_CLASSES), 1)
                confidence = probs[risk]
                model_used = "random_forest"
                # Same safety override as the rules: open Critical issue => at least High
                if f.max_open_severity >= 4 and RISK_CLASSES.index(risk) < 2:
                    risk = "High"
                    health = min(health, 54.0)
            except Exception:  # pragma: no cover
                log.exception("ML prediction failed; falling back to rules")
                probs = None
        if probs is None:
            health = rule_health
            risk = risk_from_health(health, f)
            model_used = "rule_based"

        rec_date = self._recommended_date(risk, category, last_service, f, today)
        explanation = self._explain(risk, health, factors, model_used, confidence, rec_date)
        return PredictionResult(
            health_score=health, risk_level=risk, priority=PRIORITY_BY_RISK[risk],
            recommended_service_date=rec_date, model_used=model_used, confidence=confidence,
            explanation=explanation, factors=factors, class_probabilities=probs, features=f.to_dict(),
        )

    @staticmethod
    def _recommended_date(risk: str, category: str, last_service: date | None, f: ApplianceFeatures,
                          today: date) -> date:
        interval = SERVICE_INTERVAL_DAYS.get(category, 365)
        base = today - timedelta(days=f.days_since_service)
        due = (last_service or base) + timedelta(days=interval)
        if due <= today:
            # Already overdue: book soon, sooner for riskier appliances
            due = today + timedelta(days={"Critical": 1, "High": 3, "Medium": 7, "Low": 14}[risk])
        caps = {"Critical": 3, "High": 14, "Medium": 42}
        if risk in caps:
            due = min(due, today + timedelta(days=caps[risk]))
        return max(due, today + timedelta(days=1))

    @staticmethod
    def _explain(risk, health, factors, model_used, confidence, rec_date) -> list[str]:
        lines = []
        if factors:
            top = factors[:4]
            for x in top:
                lines.append(f"{x['factor']}: {x['detail']}.")
        else:
            lines.append("No significant risk factors detected — the appliance appears to be in good shape.")
        if risk in ("High", "Critical"):
            lines.append(f"Professional servicing is recommended by {rec_date.strftime('%d %b %Y')}.")
        elif risk == "Medium":
            lines.append(f"Plan a service visit by {rec_date.strftime('%d %b %Y')} to prevent problems from developing.")
        else:
            lines.append(f"Continue routine care; next service suggested around {rec_date.strftime('%d %b %Y')}.")
        if model_used == "random_forest":
            lines.append(
                f"Risk class from a Random Forest model trained on SYNTHETIC data (model confidence "
                f"{confidence:.0%}). Treat it as a maintenance-priority estimate, not a validated failure probability."
            )
        else:
            lines.append("Score computed by the rule-based engine (ML model unavailable).")
        return lines


predictor = RiskPredictor()
