"""Train the Random Forest risk classifier on the SYNTHETIC dataset.

Run:  python -m app.ml.train
Outputs app/ml/artifacts/risk_model.joblib and model_metadata.json
"""
import json
from datetime import datetime, timezone
from pathlib import Path

import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, f1_score
from sklearn.model_selection import train_test_split

from app.ml.features import FEATURE_NAMES, RISK_CLASSES
from app.ml.synthetic_data import DATASET_LABEL, generate_synthetic_dataset

ARTIFACT_DIR = Path(__file__).resolve().parent / "artifacts"
MODEL_PATH = ARTIFACT_DIR / "risk_model.joblib"
META_PATH = ARTIFACT_DIR / "model_metadata.json"
DATASET_PATH = ARTIFACT_DIR / "synthetic_training_data.csv"


def train(n_samples: int = 6000, seed: int = 42, save: bool = True, verbose: bool = True) -> dict:
    df = generate_synthetic_dataset(n_samples=n_samples, seed=seed)
    X = df[FEATURE_NAMES].values
    y = df["risk_level"].astype(str).values

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=seed, stratify=y)
    model = RandomForestClassifier(
        n_estimators=200, max_depth=12, min_samples_leaf=3, class_weight="balanced", random_state=seed, n_jobs=-1
    )
    model.fit(X_train, y_train)
    pred = model.predict(X_test)

    meta = {
        "model_type": "RandomForestClassifier",
        "trained_on": DATASET_LABEL,
        "disclaimer": (
            "Trained on simulated data labelled by expert heuristics. Scores indicate relative "
            "maintenance priority, not validated real-world failure probabilities."
        ),
        "n_samples": int(n_samples),
        "classes": [c for c in model.classes_.tolist()],
        "class_order": RISK_CLASSES,
        "features": FEATURE_NAMES,
        "holdout_accuracy": round(float(accuracy_score(y_test, pred)), 4),
        "holdout_macro_f1": round(float(f1_score(y_test, pred, average="macro")), 4),
        "feature_importances": {
            n: round(float(v), 4) for n, v in sorted(
                zip(FEATURE_NAMES, model.feature_importances_), key=lambda t: -t[1])
        },
        "trained_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    if verbose:
        print(f"Dataset: {DATASET_LABEL}")
        print(f"Class balance: {df['risk_level'].value_counts().to_dict()}")
        print(classification_report(y_test, pred, labels=RISK_CLASSES))
        print(f"Hold-out accuracy on synthetic data: {meta['holdout_accuracy']}")
    if save:
        ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
        joblib.dump(model, MODEL_PATH, compress=3)
        META_PATH.write_text(json.dumps(meta, indent=2))
        df.to_csv(DATASET_PATH, index=False)
        if verbose:
            print(f"Saved model -> {MODEL_PATH}")
    return {"model": model, "meta": meta}


if __name__ == "__main__":
    train()
